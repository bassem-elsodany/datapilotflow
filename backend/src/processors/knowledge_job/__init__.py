"""
Knowledge Job Processing Package.

This package contains processors for handling knowledge job processing,
including document extraction, chunking, embedding generation, and storage.

NOTE: Old callback-based processors are deprecated and not imported by default.
The new architecture uses:
- RefactoredKnowledgeJobEventProcessor
- JobOrchestrator
- JobPipeline with modular steps
- Clean async generators (NO CALLBACKS)
"""

# Old processors commented out to avoid circular imports
# They are deprecated and only kept for reference
# from .knowledge_job_processor import KnowledgeJobProcessor, get_knowledge_job_processor
# from .knowledge_job_event_processor import KnowledgeJobEventProcessor, get_knowledge_job_event_processor

# New architecture - using lazy imports to avoid circular import issues
# Import explicitly when needed:
# from src.processors.knowledge_job.refactored_knowledge_job_event_processor import RefactoredKnowledgeJobEventProcessor

__all__ = [
    # New architecture (import explicitly from submodules)
    "RefactoredKnowledgeJobEventProcessor",
]
