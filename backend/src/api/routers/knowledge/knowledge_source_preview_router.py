"""
Knowledge Source Preview Router for previewing CSS selectors and crawling configurations.
"""

import asyncio
import traceback
from typing import List, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from src.api.routers.auth.auth_router import get_current_user
from src.domain.knowledge.knowledge_source_config import OutputFormat, ScrapingMode
from src.domain.user.user import User
from src.processors.crawler.crawler_config import (
    CrawlerKnowledgeConfig,
    get_crawler_config,
    get_deep_crawler_strategy,
)

router = APIRouter()


class PreviewContentRequest(BaseModel):
    """Request model for previewing content."""

    url: str = Field(..., description="URL to preview against")
    target_elements: List[str] = Field(
        default=[], description="Content elements to preview"
    )
    scraping_mode: ScrapingMode = Field(
        default=ScrapingMode.SINGLE_PAGE, description="Scraping mode"
    )
    crawl_depth: int = Field(default=0, description="Crawl depth (0 for single page)")
    output_format: str = Field(
        default="markdown",
        description="Output format: 'html', 'markdown', or 'llm_markdown'",
    )
    # LLM-powered markdown generation fields
    llm_instructions: Optional[str] = Field(
        default=None, description="Instructions for LLM-powered markdown generation"
    )
    llm_provider_id: Optional[str] = Field(
        default=None, description="LLM provider ID for markdown generation"
    )
    llm_model_name: Optional[str] = Field(
        default=None, description="LLM model name for markdown generation"
    )
    # Content filter threshold for standard markdown
    content_filter_threshold: Optional[float] = Field(
        default=None,
        description="Content filter threshold for standard markdown generation",
    )


class PreviewContentResponse(BaseModel):
    """Response model for content preview results."""

    success: bool = Field(description="Whether the preview was successful")
    url: str = Field(description="URL that was previewed")
    target_elements: List[str] = Field(
        description="Content elements that were previewed"
    )
    extracted_content: str = Field(description="The actual extracted content as string")
    content_length: int = Field(description="Total content length extracted")
    error_message: Optional[str] = Field(
        default=None, description="Error message if preview failed"
    )
    processing_time_ms: int = Field(description="Processing time in milliseconds")


@router.post("/", response_model=PreviewContentResponse)
async def preview_content(
    request: PreviewContentRequest, current_user: User = Depends(get_current_user)
):
    """
    Preview content against a given URL using the same crawling infrastructure.

    This endpoint uses the same crawling logic as the main knowledge source processing
    to preview how content will work against the target URL.
    """
    import time

    start_time = time.time()

    try:
        logger.debug(f"Previewing content for URL: {request.url}")
        logger.debug(f"Target elements: {request.target_elements}")
        logger.debug(f"LLM instructions: {request.llm_instructions}")
        logger.debug(
            f"Scraping mode: {request.scraping_mode}, Output format: {request.output_format}"
        )

        # Resolve LLM content filter configuration if provided
        llm_content_filter_config = None
        if request.llm_provider_id and request.llm_instructions:
            try:
                from src.services.knowledge.llm_content_filter_service import (
                    get_llm_content_filter_service,
                )
                from src.services.model_provider.model_provider_service import (
                    get_model_provider_service,
                )

                # Get LLM content filter service
                llm_filter_service = get_llm_content_filter_service()
                model_provider_service = get_model_provider_service()

                # Get the provider using the authenticated user ID
                logger.debug(
                    f"Looking up provider with ID: {request.llm_provider_id} for user: {current_user.id}"
                )
                provider = model_provider_service.get_model_provider(
                    request.llm_provider_id, current_user.id
                )
                logger.debug(f"Provider lookup result: {provider is not None}")
                if provider:
                    logger.debug(
                        f"LLM provider: {provider.provider_type}/{request.llm_model_name}"
                    )
                    llm_content_filter_config = {
                        "provider_name": provider.provider_type,
                        "llm_model_name": request.llm_model_name,
                        "api_token": provider.api_key,
                        "base_url": provider.endpoint,
                        "instruction": request.llm_instructions,
                        "verbose": True,
                    }
            except Exception as e:
                logger.error(
                    f"Failed to resolve LLM content filter: {e} - {traceback.format_exc()}"
                )

        # Create crawler config - always use single_page for previewing
        crawler_config = CrawlerKnowledgeConfig(
            cache_mode=CacheMode.BYPASS,
            max_depth=0,
            allowed_domains=[],
            blocked_domains=[],
            url_patterns=[],
            target_elements=request.target_elements,
            content_filter_threshold=request.content_filter_threshold or 0.5,
            scraping_mode=request.scraping_mode or ScrapingMode.SINGLE_PAGE,
            output_format=OutputFormat(request.output_format or OutputFormat.MARKDOWN),
            llm_content_filter_config=llm_content_filter_config,
        )

        # Get crawler configuration - use proper strategy for single page previewing
        deep_crawl_strategy = get_deep_crawler_strategy(crawler_config)
        crawler_run_config = get_crawler_config(crawler_config, deep_crawl_strategy)

        # Browser configuration
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            java_script_enabled=False,
            extra_args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        extracted_content = ""
        total_content_length = 0

        # Preview the crawling
        async with AsyncWebCrawler(config=browser_config) as crawler:
            try:
                # Run the crawler
                async for result in await crawler.arun(
                    request.url, config=crawler_run_config
                ):
                    logger.debug(f"Crawler result: {result.url}")

                    # Return content based on requested format
                    if request.output_format == "html":
                        if hasattr(result, "cleaned_html") and result.cleaned_html:
                            extracted_content = result.cleaned_html
                            total_content_length = len(result.cleaned_html)
                            logger.info(
                                f"Extracted HTML content length: {total_content_length}"
                            )
                        else:
                            logger.warning("HTML content not available")
                            extracted_content = ""
                            total_content_length = 0

                    elif request.output_format == "markdown":
                        if (
                            hasattr(result, "markdown")
                            and hasattr(result.markdown, "fit_markdown")
                            and result.markdown.fit_markdown
                        ):
                            extracted_content = result.markdown.fit_markdown
                            total_content_length = len(result.markdown.fit_markdown)
                            logger.info(
                                f"Extracted markdown content length: {total_content_length}"
                            )

                            # DEBUG: Log preview content details
                            logger.debug(f"PREVIEW DEBUG - URL: {result.url}")
                            logger.debug(
                                f"PREVIEW DEBUG - Content length: {total_content_length}"
                            )
                            logger.debug(f"PREVIEW DEBUG - FULL CONTENT:")
                            logger.debug(f"PREVIEW DEBUG - {extracted_content}")
                        else:
                            logger.warning("Markdown content not available")
                            extracted_content = ""
                            total_content_length = 0

                    elif request.output_format == "llm_markdown":
                        if (
                            hasattr(result, "markdown")
                            and hasattr(result.markdown, "fit_markdown")
                            and result.markdown.fit_markdown
                        ):
                            extracted_content = result.markdown.fit_markdown
                            total_content_length = len(result.markdown.fit_markdown)
                            logger.info(
                                f"Extracted LLM markdown content length: {total_content_length}"
                            )
                        else:
                            logger.warning("LLM markdown content not available")
                            extracted_content = ""
                            total_content_length = 0

                    else:
                        # Unknown output format
                        logger.warning(
                            f"Unknown output format '{request.output_format}'"
                        )
                        extracted_content = ""
                        total_content_length = 0

                    # For single page mode, we only expect one result
                    if request.scraping_mode == "single_page":
                        break

            except Exception as e:
                logger.error(f"Error during crawling: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Crawling failed: {str(e)}"
                )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return PreviewContentResponse(
            success=True,
            url=request.url,
            target_elements=request.target_elements,
            extracted_content=extracted_content,
            content_length=total_content_length,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Error previewing content: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        processing_time_ms = int((time.time() - start_time) * 1000)

        return PreviewContentResponse(
            success=False,
            url=request.url,
            target_elements=request.target_elements,
            extracted_content="",
            content_length=0,
            error_message=str(e),
            processing_time_ms=processing_time_ms,
        )
