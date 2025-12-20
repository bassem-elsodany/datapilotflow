"""
Crawler configuration module for web crawling setup.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from crawl4ai import (
    BestFirstCrawlingStrategy,
    CacheMode,
    ContentTypeFilter,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    DomainFilter,
    FilterChain,
    LLMConfig,
    LLMContentFilter,
    PruningContentFilter,
    URLPatternFilter,
)
from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import OutputFormat, ScrapingMode


@dataclass
class CrawlerKnowledgeConfig:
    """Configuration for the web crawler."""

    cache_mode: CacheMode = CacheMode.BYPASS
    max_depth: int = 6
    allowed_domains: List[str] = None
    blocked_domains: List[str] = None
    url_patterns: List[Dict[str, Any]] = None
    target_elements: List[str] = None
    content_filter_threshold: float = 0.5
    scraping_mode: ScrapingMode = ScrapingMode.WEBSITE
    output_format: OutputFormat = OutputFormat.MARKDOWN

    # LLM Content Filter Configuration
    llm_content_filter_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.allowed_domains is None:
            self.allowed_domains = ["docs.examples.com"]
        if self.blocked_domains is None:
            self.blocked_domains = [
                "old.docs.examples.com",
                "archive.docs.examples.com",
                "help.examples.com",
                "support.examples.com",
                "www.examples.com",
                "videos.examples.com",
            ]
        if self.url_patterns is None:
            self.url_patterns = []
        # Don't set default empty dict - keep as None if not provided
        if self.scraping_mode not in ["single_page", "website", "multiple_pages"]:
            raise ValueError(
                "scraping_mode must be either 'single_page' or 'website' or 'multiple_pages'"
            )


def _create_llm_content_filter(llm_config_dict: Dict[str, Any]) -> LLMContentFilter:
    """Create an LLM content filter from configuration dictionary.

    Args:
        llm_config_dict: Dictionary containing LLM configuration

    Returns:
        LLMContentFilter: Configured LLM content filter
    """
    if not llm_config_dict:
        return None

    # Construct provider string from provider name and model name
    provider_name = llm_config_dict.get("provider_name", "openai")
    model_name = llm_config_dict.get("llm_model_name", "gpt-4o-mini")
    provider = f"{provider_name}/{model_name}"

    # Create LLM config
    llm_config = LLMConfig(
        provider=provider,
        api_token=llm_config_dict.get("api_token"),
        base_url=llm_config_dict.get("base_url"),
    )

    # Create LLM content filter
    return LLMContentFilter(
        llm_config=llm_config,
        instruction=llm_config_dict.get("instruction", ""),
        verbose=True,
    )


def get_crawler_config(
    config: CrawlerKnowledgeConfig, deep_crawl_strategy: BestFirstCrawlingStrategy
) -> CrawlerRunConfig:
    """Get the crawler configuration.

    Args:
        config: The crawler configuration
        deep_crawl_strategy: The crawling strategy to use

    Returns:
        CrawlerRunConfig: The configured crawler settings
    """
    # Use LLM content filter configuration if provided
    # Create content filter (LLM or Pruning)
    content_filter = None
    if config.output_format == OutputFormat.LLM_MARKDOWN:
        # Use LLM content filter if configured and not empty
        if config.llm_content_filter_config:
            content_filter = _create_llm_content_filter(
                config.llm_content_filter_config
            )
            logger.debug(
                f"Using LLM content filter: {config.llm_content_filter_config['provider_name']}/{config.llm_content_filter_config['llm_model_name']}"
            )
        else:
            logger.warning(
                "LLM_MARKDOWN output format requested but no LLM content filter config provided"
            )
            # Fall back to pruning content filter
            content_filter = PruningContentFilter(
                threshold=config.content_filter_threshold, threshold_type="dynamic"
            )
    else:
        # Use default pruning content filter for HTML and standard MARKDOWN
        content_filter = PruningContentFilter(
            threshold=config.content_filter_threshold, threshold_type="dynamic"
        )
        logger.debug(
            f"Using pruning content filter: {config.content_filter_threshold} with threshold type: dynamic"
        )

    crawler_config = {
        "cache_mode": config.cache_mode,
        "process_iframes": False,
        "remove_overlay_elements": True,
        "exclude_external_images": True,
        "excluded_tags": ["nav", "footer", "form", "header"],
        "screenshot": False,
        "exclude_external_links": True,
        "exclude_social_media_links": True,
        "target_elements": (config.target_elements or []) + ["header"],
        "stream": True,
        "check_robots_txt": True,
        "scan_full_page": True,
        "markdown_generator": DefaultMarkdownGenerator(
            content_filter=content_filter,
            options={
                "ignore_links": True,
                "ignore_images": True,
                "escape_html": True,
                "skip_internal_links": True,
                "include_sup_sub": True,
                "ignore_emphasis": False,
                "bypass_tables": False,
                "protect_links": True,
                "bypass_images": True,
                "bypass_emphasis": True,
                "bypass_code_blocks": False,
            },
        ),
        # ALWAYS include deep_crawl_strategy for ALL modes
        # The max_depth parameter controls crawling behavior:
        # - max_depth=0: Only the exact URL (no link following)
        # - max_depth=1: Starting page + 1 level of links
        # - max_depth=2+: Starting page + multiple levels
        "deep_crawl_strategy": deep_crawl_strategy,
    }

    logger.debug(f"Crawler config: {crawler_config}")
    return CrawlerRunConfig(**crawler_config)


def get_deep_crawler_strategy(
    config: CrawlerKnowledgeConfig,
) -> BestFirstCrawlingStrategy:
    """Get the crawler strategy with scorer and filter chain.

    Args:
        config: The crawler configuration

    Returns:
        BestFirstCrawlingStrategy: The configured crawling strategy
    """

    # Create filter chain components
    filters = [
        # Domain boundaries
        DomainFilter(
            allowed_domains=config.allowed_domains,
            blocked_domains=config.blocked_domains,
        ),
        # Content type filtering
        ContentTypeFilter(allowed_types=["text/html"]),
    ]

    # Add URL pattern filters with their individual reverse settings
    for pattern in config.url_patterns:
        filters.append(
            URLPatternFilter(
                patterns=[pattern["pattern"]],
                reverse=pattern.get(
                    "reverse", True
                ),  # Use pattern's reverse setting, default to True
            )
        )

    # Create the filter chain
    filter_chain = FilterChain(filters)

    # Ensure max_depth is not None (default to 0 if it is)
    max_depth = config.max_depth if config.max_depth is not None else 0

    logger.debug(f"Creating BestFirstCrawlingStrategy with max_depth={max_depth}")

    # Configure the strategy
    return BestFirstCrawlingStrategy(
        max_depth=max_depth, include_external=False, filter_chain=filter_chain
    )
