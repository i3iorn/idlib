import logging
from api_essentials import APIFactory, OAuth2Auth, TRUST_UNDEFINED_PARAMETERS, ClientCredentials

logger = logging.getLogger(__name__)


class APIRequestHandler:
    def __init__(self, secrets_manager, signals):
        self.secrets_manager = secrets_manager
        self.signals = signals

    async def call(self, spec, endpoint_path, client_spec, body):
        factory_options = {
            "openapi_spec": spec,
            "auth": OAuth2Auth(client_spec.get("associatedServer")),
            "verify": False
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

        response = await my_api.request(
            TRUST_UNDEFINED_PARAMETERS,
            auth_info=ClientCredentials(
                client_id=client_spec.get("clientId"),
                client_secret=self.secrets_manager.get_secret(client_spec.get("clientSecretKey")).get("value"),
                scopes=client_spec.get("scopes", [])
            ),
            endpoint=my_api.get_endpoint(endpoint_path),
            **body
        )

        http_request, http_response = response.as_http_format().values()
        self.signals.request.emit(http_request)
        self.signals.response.emit(http_response)
