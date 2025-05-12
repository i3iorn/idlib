import json
import logging
from typing import Union

import httpx
from api_essentials import APIFactory, OAuth2Auth, TokenAuth, TRUST_UNDEFINED_PARAMETERS, ClientCredentials
from api_essentials.response import Response

from api_viewer.storage import RequestResponseStorage

logger = logging.getLogger(__name__)


auth_map = {
    "OAuth2Auth": OAuth2Auth,
    "BasicAuth": httpx.BasicAuth,
    "TokenAuth": TokenAuth,
}


class APIRequestHandler:
    def __init__(self, secrets_manager, signals):
        self.secrets_manager = secrets_manager
        self.signals = signals
        self.storage = RequestResponseStorage()

    async def call(self, spec, endpoint_path, client_spec, body, verify=False):
        auth_class = auth_map.get(client_spec.get("authType", "OAuth2Auth"))
        factory_options = {
            "openapi_spec": spec,
            "auth": auth_class(client_spec.get("associatedServer")),
            "verify": verify
        }
        if client_spec.get("environment") == "sandbox":
            factory_options["host_prefix"] = "sandbox-"

        my_api = APIFactory.from_openapi(**factory_options)

        logger.debug(f"API created: {my_api}")
        logger.debug(f"Endpoint path: {endpoint_path}")
        logger.debug(f"Client spec: {client_spec}")
        logger.debug(f"Client ID: {client_spec.get('clientId')}")
        logger.debug(f"Client secret key: {client_spec.get('clientSecretKey')}")
        logger.debug(f"Scopes: {client_spec.get('scopes', [])}")
        logger.debug(f"Body: {body}")

        client_auth_info = client_spec.get("auth")

        if "clientId" in client_auth_info and "clientSecretKey" in client_auth_info:
            secret = self.secrets_manager.get_secret(client_spec["clientSecretKey"])
            credentials = ClientCredentials(
                client_id=client_auth_info.get("clientId"),
                client_secret=secret,
                scopes=client_auth_info.get("scopes", [])
            )
        elif "token" in client_auth_info:
            secret = self.secrets_manager.get_secret(client_auth_info["token"])
            credentials = TokenAuth(
                token=secret
            )§
        else:
            raise ValueError("Invalid authentication information provided.")

        response = await my_api.request(
            TRUST_UNDEFINED_PARAMETERS,
            auth_info=credentials,
            endpoint=my_api.get_endpoint(endpoint_path),
            **body
        )
        req_id = self._store_response(response)
        self._send_signals(req_id)

    def _store_response(self, response: Response) -> int:
        token_request: httpx.Request = response.request.extensions["token_request"]
        token_req_id = self.storage.insert_request(
            str(token_request.method),
            str(token_request.url),
            json.dumps(dict(token_request.headers)),
            token_request.content.decode("utf-8"),
            http_version=response.http_version
        )
        token_response: Response = response.request.extensions["token_response"]
        self.storage.insert_response(
            token_req_id,
            token_response.status_code,
            json.dumps(dict(token_response.headers)),
            token_response.perf_request_time,
            token_response.text,
            http_version=token_response.http_version,
            reason_phrase=token_response.reason_phrase
        )

        req_id = self.storage.insert_request(
            str(response.request.method),
            str(response.request.url),
            json.dumps(dict(response.request.headers)),
            response.request.content.decode("utf-8"),
            token_request_id=token_req_id,
            http_version=response.http_version
        )
        self.storage.insert_response(
            req_id,
            response.status_code,
            json.dumps(dict(response.headers)),
            response.perf_request_time,
            response.text,
            http_version=response.http_version,
            reason_phrase=response.reason_phrase
        )
        if response.status_code == 200:
            self._store_individual_values(req_id, response.json())

        return req_id

    def _store_individual_values(self, req_id, response_json: Union[dict, list], parent_key: str = ""):
        if isinstance(response_json, dict):
            for key, value in response_json.items():
                new_key = f"{parent_key}.{key}" if parent_key else key
                if isinstance(value, (dict, list)):
                    self._store_individual_values(value, new_key)
                else:
                    self.storage.insert_value(req_id, new_key, str(value))
        elif isinstance(response_json, list):
            for index, item in enumerate(response_json):
                new_key = f"{parent_key}[{index}]"
                if isinstance(item, (dict, list)):
                    self._store_individual_values(req_id, item, new_key)
                else:
                    self.storage.insert_value(req_id, new_key, str(item))

    def _send_signals(self, req_id: int):
        self.signals.loadRequestId.emit(req_id)
