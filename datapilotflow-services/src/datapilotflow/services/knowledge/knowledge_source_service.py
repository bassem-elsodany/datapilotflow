"""
Knowledge Source Configuration Service.

This service handles business logic for knowledge source configurations,
delegating data access to DAOs.
"""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import (
    KnowledgeSourceConfig,
    KnowledgeSourceConfigCreate,
    KnowledgeSourceConfigExpanded,
    KnowledgeSourceConfigUpdate,
    UrlSourceConfig,
)
from datapilotflow.persistence.dao import KnowledgeSourceDAO, UrlSourceDAO


class KnowledgeSourceService:
    """Service for managing knowledge source configurations."""

    def __init__(self):
        self.knowledge_source_dao = KnowledgeSourceDAO()
        self.url_source_dao = UrlSourceDAO()

    def create_knowledge_source_config(
        self, config_data: KnowledgeSourceConfigCreate, user_id: str
    ) -> KnowledgeSourceConfig:
        """Create a new knowledge source configuration."""

        # Validate content source type specific requirements
        if config_data.content_source_type == "web_scraping":
            if not config_data.scraping_mode:
                raise ValueError(
                    "Scraping mode is required for web scraping configurations"
                )

            # URL validation depends on scraping mode
            if config_data.scraping_mode in ["single_page", "website"]:
                # For single page and website modes, URL is required
                if not config_data.url:
                    raise ValueError(
                        f"URL is required for {config_data.scraping_mode} scraping mode"
                    )
            # For multiple_pages mode, URL is optional (URLs come from url_source)
        elif config_data.content_source_type == "local_files":
            # For local files, we only validate if local_files is provided (not None)
            # This allows FormData uploads to pass validation initially
            if (
                config_data.local_files is not None
                and len(config_data.local_files) == 0
            ):
                raise ValueError(
                    "Local files are required for local files configurations"
                )
            if not config_data.file_types:
                raise ValueError(
                    "File types are required for local files configurations"
                )

        # Handle URL source creation if present (only for web scraping)
        if (
            config_data.content_source_type == "web_scraping"
            and config_data.url_source
            and config_data.scraping_mode == "multiple_pages"
        ):
            url_source_id = self.url_source_dao.create_url_source(
                config_data.url_source, user_id
            )
            if not url_source_id:
                raise ValueError("Failed to create URL source configuration")

            # Set the url_source_id in config_data before creating the config
            config_data.url_source_id = url_source_id

        # Create the main configuration
        config_id = self.knowledge_source_dao.create_config(config_data, user_id)
        if not config_id:
            raise ValueError("Failed to create knowledge source configuration")

        # Get and return the created configuration
        config = self.knowledge_source_dao.get_config(config_id, user_id)
        if not config:
            raise ValueError("Failed to retrieve created configuration")

        return config

    def get_knowledge_source_config(
        self, config_id: str, user_id: str
    ) -> Optional[KnowledgeSourceConfig]:
        """Get a knowledge source configuration by ID."""
        return self.knowledge_source_dao.get_config(config_id, user_id)

    def get_knowledge_source_config_expanded(
        self, config_id: str, user_id: str, expand: Optional[str] = None
    ) -> Optional[KnowledgeSourceConfigExpanded]:
        """Get a knowledge source configuration with expanded related data."""
        # Get the base configuration
        config = self.knowledge_source_dao.get_config(config_id, user_id)
        if not config:
            return None

        # Convert to expanded model
        expanded_data = config.model_dump()

        # Parse expand parameter
        expand_fields = set()
        if expand:
            expand_fields = set(expand.split(","))

        # Fetch related data based on expand parameter
        if "content_filter" in expand_fields and config.llm_content_filter_id:
            try:
                # Import here to avoid circular dependencies
                from datapilotflow.services.llm_content_filter.llm_content_filter_service import (
                    get_llm_content_filter_service,
                )

                content_filter_service = get_llm_content_filter_service()
                content_filter = content_filter_service.get_llm_content_filter_config(
                    config.llm_content_filter_id, user_id
                )
                if content_filter:
                    expanded_data["content_filter"] = content_filter.model_dump()
            except Exception as e:
                logger.warning(
                    f"Failed to fetch content filter {config.llm_content_filter_id}: {e}"
                )

        if "model_provider" in expand_fields and config.llm_content_filter_id:
            try:
                # Import here to avoid circular dependencies
                from datapilotflow.services.llm_content_filter.llm_content_filter_service import (
                    get_llm_content_filter_service,
                )
                from datapilotflow.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                content_filter_service = get_llm_content_filter_service()
                content_filter = content_filter_service.get_llm_content_filter_config(
                    config.llm_content_filter_id, user_id
                )
                if content_filter and content_filter.llm_provider_id:
                    model_provider_service = get_model_provider_service()
                    model_provider = model_provider_service.get_model_provider(
                        content_filter.llm_provider_id, user_id
                    )
                    if model_provider:
                        expanded_data["model_provider"] = model_provider.model_dump()
            except Exception as e:
                logger.warning(f"Failed to fetch model provider: {e}")

        if "url_source" in expand_fields and config.url_source_id:
            try:
                url_source = self.url_source_dao.get_url_source(
                    config.url_source_id, user_id
                )
                if url_source:
                    expanded_data["url_source"] = url_source.model_dump()
            except Exception as e:
                logger.warning(
                    f"Failed to fetch URL source {config.url_source_id}: {e}"
                )

        return KnowledgeSourceConfigExpanded(**expanded_data)

    def list_knowledge_source_configs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        content_source_type: Optional[str] = None,
    ) -> List[KnowledgeSourceConfig]:
        """List knowledge source configurations for a user."""
        configs = self.knowledge_source_dao.list_configs(
            user_id, skip, limit, content_source_type
        )

        # Clean up any invalid local_files data
        for config in configs:
            if hasattr(config, "local_files") and config.local_files:
                # Remove any local_files entries with undefined required fields
                config.local_files = [
                    file_data
                    for file_data in config.local_files
                    if (
                        isinstance(file_data, dict)
                        and file_data.get("file_id")
                        and file_data.get("original_filename")
                        and file_data.get("file_path")
                        and file_data.get("file_type")
                        and file_data.get("file_size") is not None
                        and file_data.get("upload_timestamp")
                    )
                ]
                # If no valid files remain, set to None
                if not config.local_files:
                    config.local_files = None

        return configs

    def update_knowledge_source_config(
        self, config_id: str, user_id: str, update_data: KnowledgeSourceConfigUpdate
    ) -> Optional[KnowledgeSourceConfig]:
        """Update a knowledge source configuration."""

        # Handle URL source update if url_source is present and scraping mode is multiple_pages
        if (
            update_data.url_source is not None
            and update_data.scraping_mode == "multiple_pages"
        ):
            logger.info(f"📝 URL source present, updating URL source")

            # Get existing config to get url_source_id
            existing_config = self.knowledge_source_dao.get_config(config_id, user_id)
            if not existing_config:
                logger.error(f"Config {config_id} not found")
                return None

            if existing_config.url_source_id:
                # Update existing URL source
                logger.info(
                    f"🔄 Updating URL source {existing_config.url_source_id} with {len(update_data.url_source.urls)} URLs"
                )

                success = self.url_source_dao.update_url_source(
                    existing_config.url_source_id, update_data.url_source
                )
                if success:
                    logger.info(
                        f"✅ Successfully updated URL source {existing_config.url_source_id}"
                    )
                else:
                    logger.warning(
                        f"⚠️  Update returned False for URL source {existing_config.url_source_id}"
                    )
            else:
                # Create new URL source if config doesn't have one
                logger.info(f"📝 Config has no URL source, creating new one")

                url_source_id = self.url_source_dao.create_url_source(
                    update_data.url_source, user_id
                )
                if not url_source_id:
                    logger.error("Failed to create URL source")
                    return None

                # Update config with new url_source_id
                logger.info(f"🔗 Linking URL source {url_source_id} to config")
                from bson import ObjectId

                self.knowledge_source_dao.collection.update_one(
                    {"_id": ObjectId(config_id)},
                    {"$set": {"url_source_id": url_source_id}},
                )

        return self.knowledge_source_dao.update_config(config_id, user_id, update_data)

    def delete_knowledge_source_config(self, config_id: str, user_id: str) -> bool:
        """Delete a knowledge source configuration.

        Prevent deletion if there are dependent knowledge jobs referencing this config.
        """
        try:
            # Local import to avoid wider coupling
            from datapilotflow.persistence.dao.knowledge_job_dao import KnowledgeJobDAO

            job_dao = KnowledgeJobDAO()
            existing_jobs = job_dao.list_jobs(
                user_id=user_id, config_id=config_id, status=None, skip=0, limit=1
            )
            if existing_jobs:
                # Signal dependency conflict
                raise ValueError(
                    "Cannot delete configuration with existing jobs. Delete related jobs first."
                )

            return self.knowledge_source_dao.delete_config(config_id, user_id)
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Error validating delete for knowledge source configuration {config_id}: {e}"
            )
            raise

    def get_url_source_config(
        self, url_source_id: str, user_id: str
    ) -> Optional["UrlSourceConfig"]:
        """Get a URL source configuration by ID.

        Note: Access control is handled at the router level via the nested route
        /sources/{config_id}/url-sources/{url_source_id}
        """
        return self.url_source_dao.get_url_source(url_source_id)


# Global service instance
_knowledge_source_service: Optional[KnowledgeSourceService] = None


def get_knowledge_source_service() -> KnowledgeSourceService:
    """Get the global knowledge source service instance."""
    global _knowledge_source_service

    if _knowledge_source_service is None:
        _knowledge_source_service = KnowledgeSourceService()

    return _knowledge_source_service
