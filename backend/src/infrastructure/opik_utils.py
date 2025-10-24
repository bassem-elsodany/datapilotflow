import os

import opik
from loguru import logger
from opik.configurator.configure import OpikConfigurator

from src.config import settings


def configure() -> None:
    if settings.AGENT_TRACING_ENABLED:
        try:
            client = OpikConfigurator(use_local=True, url=settings.OPIK_URL_OVERRIDE)
            default_workspace = client._get_default_workspace()
            logger.info(f"Default workspace: {default_workspace}")
        except Exception:
            logger.error(
                "Default workspace not found. Setting workspace to None and enabling interactive mode."
            )
            default_workspace = None

        os.environ["OPIK_PROJECT_NAME"] = settings.COMET_PROJECT

        try:
            opik.configure(
                api_key=settings.COMET_API_KEY,
                workspace=default_workspace,
                use_local=True,
                url=settings.OPIK_URL_OVERRIDE,
                force=True,
            )
            logger.info(
                f"Opik configured successfully using workspace '{default_workspace}'"
            )
        except Exception:
            logger.error(
                "Couldn't configure Opik. There is probably a problem with AGENT_TRACING_ENABLED or OPIK_URL_OVERRIDE environment variables or with the Opik server."
            )
    else:
        logger.debug("Agent tracing is disabled, skipping Opik configuration")


def get_dataset(name: str) -> opik.Dataset | None:
    client = opik.Opik()
    try:
        dataset = client.get_dataset(name=name)
    except Exception:
        dataset = None

    return dataset


def create_dataset(name: str, description: str, items: list[dict]) -> opik.Dataset:
    client = opik.Opik()

    client.delete_dataset(name=name)

    dataset = client.create_dataset(name=name, description=description)
    dataset.insert(items)

    return dataset
