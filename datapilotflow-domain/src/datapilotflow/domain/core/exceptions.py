"""
Custom exceptions for the SkillPilot domain.

This module defines domain-specific exceptions used throughout the SkillPilot
application for handling knowledge source related errors and validation failures.
"""

class KnowledgeNameNotFound(Exception):
    """Exception raised when a knowledge source's name is not found."""

    def __init__(self, knowledge_id: str):
        self.message = f"Knowledge source name for {knowledge_id} not found."
        super().__init__(self.message)


class KnowledgePerspectiveNotFound(Exception):
    """Exception raised when a knowledge source's perspective is not found."""

    def __init__(self, knowledge_id: str):
        self.message = f"Knowledge source perspective for {knowledge_id} not found."
        super().__init__(self.message)


class KnowledgeStyleNotFound(Exception):
    """Exception raised when a knowledge source's style is not found."""

    def __init__(self, knowledge_id: str):
        self.message = f"Knowledge source style for {knowledge_id} not found."
        super().__init__(self.message)


class KnowledgeContextNotFound(Exception):
    """Exception raised when a knowledge source's context is not found."""

    def __init__(self, knowledge_id: str):
        self.message = f"Knowledge source context for {knowledge_id} not found."
        super().__init__(self.message)


class KnowledgeURLNotFound(Exception):
    """Exception raised when a knowledge source's URL is not found."""

    def __init__(self, knowledge_id: str):
        self.message = f"Knowledge source URL for {knowledge_id} not found."
        super().__init__(self.message)


class KnowledgeSchemaNotFound(Exception):
    """Exception raised when a knowledge source's schema is not found."""

    def __init__(self, knowledge_id: str):
        self.message = f"Knowledge source schema for {knowledge_id} not found."
        super().__init__(self.message)


class KnowledgeConfigNotFound(Exception):
    """Exception raised when a knowledge source's configuration is not found."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class KnowledgeConfigValidationError(Exception):
    """Exception raised when knowledge configuration validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = f"Invalid {field}: {message}"
        super().__init__(self.message)


class KnowledgeConfigRequiredError(Exception):
    """Exception raised when a required knowledge configuration field is missing."""

    def __init__(self, field: str):
        self.field = field
        self.message = f"Required field '{field}' is missing in knowledge configuration"
        super().__init__(self.message)


# Workflow-specific exceptions
class WorkflowToolError(Exception):
    """Base exception for workflow tool errors."""

    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        self.message = f"Workflow tool '{tool_name}' error: {message}"
        super().__init__(self.message)


class VectorSearchError(WorkflowToolError):
    """Exception raised when vector search fails."""

    def __init__(self, query: str, error: str):
        self.query = query
        self.error = error
        self.message = f"Vector search failed for query '{query}': {error}"
        super().__init__("vector_search", self.message)


class SemanticSearchError(WorkflowToolError):
    """Exception raised when semantic search fails."""

    def __init__(self, query: str, error: str):
        self.query = query
        self.error = error
        self.message = f"Semantic search failed for query '{query}': {error}"
        super().__init__("semantic_search", self.message)


class HybridSearchError(WorkflowToolError):
    """Exception raised when hybrid search fails."""

    def __init__(self, query: str, error: str):
        self.query = query
        self.error = error
        self.message = f"Hybrid search failed for query '{query}': {error}"
        super().__init__("hybrid_search", self.message)


class EntitySearchError(WorkflowToolError):
    """Exception raised when entity search fails."""

    def __init__(self, entities: list, error: str):
        self.entities = entities
        self.error = error
        self.message = f"Entity search failed for entities {entities}: {error}"
        super().__init__("entity_search", self.message)


class RelationshipSearchError(WorkflowToolError):
    """Exception raised when relationship search fails."""

    def __init__(self, relationships: list, error: str):
        self.relationships = relationships
        self.error = error
        self.message = f"Relationship search failed for relationships {relationships}: {error}"
        super().__init__("relationship_search", self.message)


class KnowledgeGraphSearchError(WorkflowToolError):
    """Exception raised when knowledge graph search fails."""

    def __init__(self, query: str, error: str):
        self.query = query
        self.error = error
        self.message = f"Knowledge graph search failed for query '{query}': {error}"
        super().__init__("knowledge_graph_search", self.message)


class DocumentRetrievalError(WorkflowToolError):
    """Exception raised when document retrieval by ID fails."""

    def __init__(self, document_id: str, error: str):
        self.document_id = document_id
        self.error = error
        self.message = f"Document retrieval failed for ID '{document_id}': {error}"
        super().__init__("get_document_by_id", self.message)


class WeaviateConnectionError(WorkflowToolError):
    """Exception raised when Weaviate connection fails."""

    def __init__(self, error: str):
        self.error = error
        self.message = f"Weaviate connection failed: {error}"
        super().__init__("weaviate_connection", self.message)


class InvalidSearchParametersError(WorkflowToolError):
    """Exception raised when search parameters are invalid."""

    def __init__(self, tool_name: str, parameter: str, value: any, reason: str):
        self.parameter = parameter
        self.value = value
        self.reason = reason
        self.message = f"Invalid parameter '{parameter}' with value '{value}' for {tool_name}: {reason}"
        super().__init__(tool_name, self.message)