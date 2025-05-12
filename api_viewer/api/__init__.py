import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from time import sleep

import jsonschema
import yaml

load_dotenv(find_dotenv())
print(os.environ)

from api_viewer.api.client_registry import ClientRegistry
from api_viewer.api.protocol import Protocol
from api_viewer.api.spec.registry import SpecRegistry
from api_viewer.api.spec.reader import SpecReader

logger = logging.getLogger(__name__)


def load_apis(spec_path: str = None) -> None:
    """
    Load API specifications from a file and register them with the SpecRegistry.
    :param spec_path: Path to the API specifications file
    :raises FileNotFoundError: If the specified file does not exist
    :raises ValueError: If the file format is not supported
    :raises jsonschema.ValidationError: If the JSON schema validation fails
    :raises yaml.YAMLError: If the YAML file cannot be parsed
    :raises Exception: If any other error occurs during loading

    :return: None
    """
    spec_path = spec_path or os.getenv("API_SPEC_FILE") or Path("config/api_specs.ini")
    spec_registry = SpecRegistry()
    logger.debug("Loading API specifications from file", extra={"extra_spec_path": spec_path})

    if not os.path.exists(spec_path):
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    logger.debug("Spec file found", extra={"spec_path": spec_path})

    with open(spec_path, "r", encoding="utf-8") as spec_address_file:
        spec_addresses = spec_address_file.readlines()
        logger.debug("Loaded spec addresses", extra={"extra_spec_addresses": spec_addresses})

    for line in spec_addresses:
        if line.startswith("#") or not line.strip():
            continue

        name, spec_address = line.strip().split("=")

        if not name or not spec_address:
            logger.error("Invalid spec address", extra={"extra_name": name, "extra_spec_address": spec_address})
            raise ValueError(f"Invalid spec address: {name}={spec_address}")

        logger.debug("Processing spec address", extra={"extra_name": name, "extra_spec_address": spec_address})
        spec_reader = SpecReader(spec_address)
        if not spec_reader.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_address}")

        logger.debug("Spec file found", extra={"spec_address": spec_address})

        og_spec_text = spec_reader.read()
        spec_text = spec_registry.apply_hooks(name, og_spec_text)

        if spec_address.endswith("json"):
            spec = json.loads(spec_text)
        elif spec_address.endswith("yaml"):
            spec = yaml.safe_load(spec_text)
        else:
            raise ValueError(f"Unsupported file format: {spec_address}")
        spec_registry.register(name, spec)
        try:
            spec_registry.get(name)
        except KeyError:
            logger.error("Spec not found in registry", extra={"extra_name": name})
            raise

def load_clients():
    """
    Load client configurations from a JSON file and register them with the ClientRegistry.
    :raises FileNotFoundError: If the specified file does not exist
    :raises jsonschema.ValidationError: If the JSON schema validation fails
    :raises json.JSONDecodeError: If the JSON file cannot be parsed
    :raises Exception: If any other error occurs during loading
    :return: None
    :note: The JSON file should contain a list of client configurations, each with a "clientId" key.
    :note: The JSON schema file should define the structure of the client configurations.
    :note: The JSON schema file should be in the same directory as the JSON file.
    :note: The JSON schema file should be named "client-schema.json".
    """
    client_registry = ClientRegistry()
    clients_path = os.getenv("CLIENTS_FILE") or Path("env/clients.json")
    with (open(clients_path, "r", encoding="utf-8") as clients_file,
          open("config/clients-schema.json", "r", encoding="utf-8") as schema_file):
        clients = json.load(clients_file)
        schema = json.load(schema_file)
        jsonschema.validate(clients, schema)

    for client in clients.get("clients", []):
        client_registry.register(client["name"],client)
