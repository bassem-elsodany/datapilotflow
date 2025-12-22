"""
JSON-based provider configuration loader for OpenAI-compatible providers.
(Following LiteLLM's exact implementation)
"""

import json
from pathlib import Path
from typing import Dict, Optional

from loguru import logger


class SimpleProviderConfig:
    """Simple data class for JSON provider config"""

    def __init__(self, slug: str, data: dict):
        self.slug = slug
        self.base_url = data["base_url"]
        self.api_key_env = data["api_key_env"]
        self.api_base_env = data.get("api_base_env")
        self.base_class = data.get("base_class", "openai_gpt")
        self.param_mappings = data.get("param_mappings", {})
        self.constraints = data.get("constraints", {})
        self.special_handling = data.get("special_handling", {})


class JSONProviderRegistry:
    """Load providers from JSON once on import"""

    _providers: Dict[str, SimpleProviderConfig] = {}
    _loaded = False

    @classmethod
    def load(cls):
        """Load providers from JSON configuration file"""
        if cls._loaded:
            return

        json_path = Path(__file__).parent / "providers.json"
        logger.info(f"Loading JSON providers from: {json_path}")
        logger.info(f"JSON file exists: {json_path.exists()}")

        if not json_path.exists():
            # No JSON file yet, that's okay
            cls._loaded = True
            logger.warning(f"No providers.json found at {json_path}")
            return

        try:
            with open(json_path) as f:
                data = json.load(f)

            logger.info(f"Loaded providers from JSON: {list(data.keys())}")

            for slug, config in data.items():
                cls._providers[slug] = SimpleProviderConfig(slug, config)
                logger.info(f"Registered provider '{slug}' in JSONProviderRegistry")

            cls._loaded = True
            logger.info(f"JSONProviderRegistry load complete. Total providers: {len(cls._providers)}")
        except Exception as e:
            logger.warning(f"Warning: Failed to load JSON provider configs: {e}")
            cls._loaded = True

    @classmethod
    def get(cls, slug: str) -> Optional[SimpleProviderConfig]:
        """Get a provider configuration by slug"""
        return cls._providers.get(slug)

    @classmethod
    def exists(cls, slug: str) -> bool:
        """Check if a provider is defined via JSON"""
        return slug in cls._providers

    @classmethod
    def list_providers(cls) -> list:
        """List all registered provider slugs"""
        return list(cls._providers.keys())


# Load on import
JSONProviderRegistry.load()


def register_json_providers_with_litellm():
    """Register JSON providers with LiteLLM's models_by_provider.

    This makes custom providers visible to LiteLLM and the rest of the system.
    """
    try:
        from litellm import models_by_provider

        logger.info(f"Starting JSON provider registration. Providers to register: {JSONProviderRegistry.list_providers()}")

        for provider_slug in JSONProviderRegistry.list_providers():
            # Add provider to models_by_provider using the provider slug (not base_class)
            # This is how LiteLLM's routing logic finds the provider
            logger.info(f"Registering provider '{provider_slug}'")
            if provider_slug not in models_by_provider:
                models_by_provider[provider_slug] = set()
                logger.info(f"Successfully registered provider '{provider_slug}' with LiteLLM")
            else:
                logger.info(f"Provider '{provider_slug}' already registered")

        logger.info(f"JSON provider registration complete. Total providers: {len(models_by_provider)}")
    except ImportError:
        logger.warning("LiteLLM not available, skipping provider registration")
    except Exception as e:
        logger.error(f"Error registering providers with LiteLLM: {e}")
