import asyncio
import json
import os

import yaml

from api_essentials import APIFactory, TRUST_UNDEFINED_PARAMETERS
from api_essentials.auth import OAuth2Auth, ClientCredentials

from api_viewer.api.protocol import Protocol
from api_viewer.api.spec.registry import SpecRegistry
from api_viewer.api.spec.reader import SpecReader


def load_apis(spec_path: str = "api_specs.ini") -> None:
    spec_registry = SpecRegistry()

    def decisioning_fix(spec: str) -> str:
        return spec.replace("""content:
                application/json:
                  schema:
                    oneOf:
                      - $ref: '#/components/schemas/NonCreditDecision-api-v3-b2c-background_BackgroundDataB2CSE'
                  examples:
    """, "").replace("User comment", "string")

    spec_registry.add_hook(
        "decisioning",
        decisioning_fix
    )

    if not os.path.exists(spec_path):
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    registry = SpecRegistry()
    with open(spec_path, "r", encoding="utf-8") as spec_address_file:
        spec_addresses = spec_address_file.readlines()

    for name, spec_address in (line.strip().split("=") for line in spec_addresses):
        print(f"Loading spec: {name} from {spec_address}")
        spec_reader = SpecReader(spec_address)
        spec_text = spec_reader.read()

        spec_text = registry.apply_hooks(name, spec_text)

        if spec_address.endswith("json"):
            spec = json.loads(spec_text)
        elif spec_address.endswith("yaml"):
            spec = yaml.safe_load(spec_text)
        else:
            raise ValueError(f"Unsupported file format: {spec_address}")
        registry.register(name, spec)

async def call(spec):
    my_api = APIFactory.from_openapi(spec, auth=OAuth2Auth(r"https://login.bisnode.com/sandbox/v1/token.oauth2"), verify=False, host_prefix="sandbox-")
    response = await my_api.request(
        TRUST_UNDEFINED_PARAMETERS,
        auth_info=ClientCredentials(
            client_id="71a7c376-0f79-4fc5-9db9-6447d2097e21",
            client_secret="Ut0dzd8PWzZpxorrFJ8l0d8D4ZcbLNHsJVncvjc26v9V7A4LlLkCAgF11jsJdOxM",
            scopes=["credit_data_persons"]
        ),
        endpoint=my_api.get_endpoint("/persons/fi/credit-data"),
        **{
            "nationalIdentificationNumber": "020365-999P",
            "reportType": "LARGE",
            "reasonCode": "1 (Application for credit)"
        }
    )
    response.print_http()
