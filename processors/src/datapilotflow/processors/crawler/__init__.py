"""
Crawler subpackage for web crawling and document extraction.
"""

from .crawler_config import CrawlerKnowledgeConfig, get_crawler_config, get_deep_crawler_strategy
from .crawler_processor import get_knowledge_source_documents

__all__ = [
    # Crawler configuration
    "CrawlerKnowledgeConfig",
    "get_crawler_config",
    "get_deep_crawler_strategy",
    
    # Crawler processing
    "get_knowledge_source_documents"
] 