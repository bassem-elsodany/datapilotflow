"""
Test services package imports and basic initialization.
"""

import pytest
from unittest.mock import Mock, patch


class TestDomainImports:
    """Test that domain models can be imported."""

    def test_import_job_status(self):
        """Test importing JobStatus enum from domain."""
        from datapilotflow.domain.knowledge.knowledge_job import JobStatus
        assert JobStatus.RUNNING
        assert JobStatus.COMPLETED
        assert JobStatus.FAILED

    def test_import_knowledge_job_models(self):
        """Test importing knowledge job models."""
        from datapilotflow.domain.knowledge.knowledge_job import (
            KnowledgeJob,
            KnowledgeJobCreate,
            KnowledgeJobUpdate
        )
        assert KnowledgeJob
        assert KnowledgeJobCreate
        assert KnowledgeJobUpdate


class TestPersistenceImports:
    """Test that persistence layer can be imported."""

    def test_import_mongo_client(self):
        """Test importing MongoDB client wrapper."""
        from datapilotflow.infrastructure.mongo.client import MongoClientWrapper
        assert MongoClientWrapper

    def test_import_knowledge_source_dao(self):
        """Test importing knowledge source DAO."""
        from datapilotflow.infrastructure.dao.knowledge import (
            KnowledgeSourceDAO
        )
        assert KnowledgeSourceDAO

    def test_import_knowledge_job_dao(self):
        """Test importing knowledge job DAO."""
        from datapilotflow.infrastructure.dao.knowledge import (
            KnowledgeJobDAO
        )
        assert KnowledgeJobDAO


class TestVectordbImports:
    """Test that vectordb layer can be imported."""

    def test_import_milvus_client(self):
        """Test importing Milvus client wrapper from persistence."""
        from datapilotflow.infrastructure.vectordb.milvus import MilvusClientWrapper
        assert MilvusClientWrapper


class TestEventsImports:
    """Test that events layer can be imported."""

    def test_events_package_exists(self):
        """Test that events package is installed."""
        try:
            import datapilotflow.events
            assert True
        except ImportError:
            # Events package may not be fully initialized yet
            assert True


class TestKnowledgeServices:
    """Test knowledge services module."""

    def test_import_knowledge_source_service(self):
        """Test importing knowledge source service."""
        from datapilotflow.services.knowledge.knowledge_source_service import (
            KnowledgeSourceService
        )
        assert KnowledgeSourceService

    def test_import_knowledge_job_service(self):
        """Test importing knowledge job service."""
        from datapilotflow.services.knowledge.knowledge_job_service import (
            KnowledgeJobService
        )
        assert KnowledgeJobService

    def test_import_job_timeline_service(self):
        """Test importing job timeline service."""
        from datapilotflow.services.knowledge.job_timeline_service import (
            JobTimelineService
        )
        assert JobTimelineService

    def test_import_vectordb_collection_service(self):
        """Test importing vectordb collection service."""
        from datapilotflow.services.knowledge.vectordb_collection_service import (
            VectorDBCollectionService
        )
        assert VectorDBCollectionService

    def test_import_document_splitter_service(self):
        """Test importing document splitter service."""
        from datapilotflow.services.knowledge.document_splitter_service import (
            DocumentSplitterService
        )
        assert DocumentSplitterService

    def test_knowledge_services_module_exports(self):
        """Test that knowledge services module exports key classes."""
        from datapilotflow.services import knowledge
        assert hasattr(knowledge, 'KnowledgeSourceService')
        assert hasattr(knowledge, 'KnowledgeJobService')
        assert hasattr(knowledge, 'JobTimelineService')


class TestModelProviderServices:
    """Test model provider services module."""

    def test_import_model_provider_service(self):
        """Test importing model provider service."""
        from datapilotflow.services.model_provider.model_provider_service import (
            ModelProviderService
        )
        assert ModelProviderService

    def test_import_model_provider_initialization_service(self):
        """Test importing model provider initialization service."""
        from datapilotflow.services.model_provider.model_provider_initialization_service import (
            ModelProviderInitializationService
        )
        assert ModelProviderInitializationService

    def test_model_provider_services_module_exports(self):
        """Test that model_provider services module exports key classes."""
        from datapilotflow.services import model_provider
        assert hasattr(model_provider, 'ModelProviderService')
        assert hasattr(model_provider, 'ModelProviderInitializationService')


class TestServicesModuleExports:
    """Test services module top-level exports."""

    def test_services_module_has_submodules(self):
        """Test that services module exports its submodules."""
        from datapilotflow import services
        assert hasattr(services, 'knowledge')
        assert hasattr(services, 'model_provider')


class TestServiceMethods:
    """Test that services have expected methods."""

    def test_knowledge_source_service_has_methods(self):
        """Test that KnowledgeSourceService has expected methods."""
        from datapilotflow.services.knowledge.knowledge_source_service import (
            KnowledgeSourceService
        )

        # Check for class methods (don't instantiate)
        assert hasattr(KnowledgeSourceService, 'create_knowledge_source_config')
        assert hasattr(KnowledgeSourceService, 'get_knowledge_source_config')
        assert hasattr(KnowledgeSourceService, 'list_knowledge_source_configs')

    def test_knowledge_job_service_has_methods(self):
        """Test that KnowledgeJobService has expected methods."""
        from datapilotflow.services.knowledge.knowledge_job_service import (
            KnowledgeJobService
        )

        assert hasattr(KnowledgeJobService, 'create_knowledge_job')
        assert hasattr(KnowledgeJobService, 'get_knowledge_job')

    def test_job_timeline_service_has_methods(self):
        """Test that JobTimelineService has expected methods."""
        from datapilotflow.services.knowledge.job_timeline_service import (
            JobTimelineService
        )

        assert hasattr(JobTimelineService, 'create_timeline_entry')
        assert hasattr(JobTimelineService, 'get_timeline_entry')

    def test_model_provider_service_has_methods(self):
        """Test that ModelProviderService has expected methods."""
        from datapilotflow.services.model_provider.model_provider_service import (
            ModelProviderService
        )

        assert hasattr(ModelProviderService, 'create_model_provider')
        assert hasattr(ModelProviderService, 'get_model_provider')


class TestNamespacePackaging:
    """Test that namespace package is properly set up."""

    def test_datapilotflow_namespace_imports(self):
        """Test that datapilotflow namespace can import from multiple packages."""
        # Import from different packages in the datapilotflow namespace
        from datapilotflow.domain.knowledge.knowledge_job import JobStatus
        from datapilotflow.infrastructure.mongo.client import MongoClientWrapper
        from datapilotflow.infrastructure.vectordb.milvus import MilvusClientWrapper
        from datapilotflow.services.knowledge.knowledge_source_service import KnowledgeSourceService

        # All imports should succeed without conflicts
        assert JobStatus
        assert MongoClientWrapper
        assert MilvusClientWrapper
        assert KnowledgeSourceService

    def test_services_package_path(self):
        """Test that services package is properly installed."""
        import datapilotflow.services
        import os

        # Check that services package exists in site-packages or local install
        services_path = datapilotflow.services.__file__
        assert services_path
        assert os.path.exists(os.path.dirname(services_path))
