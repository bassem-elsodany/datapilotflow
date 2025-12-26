"""
Confluence API Client for document extraction.

This module provides a client for interacting with Atlassian Confluence Cloud API
to fetch pages, spaces, attachments, and other content.
"""

import asyncio
import base64
import re
from typing import List, Optional
from urllib.parse import urljoin

import aiohttp
from loguru import logger

from datapilotflow.domain.knowledge.knowledge_source_config import (
    ConfluenceConfig,
    ConfluenceScrapingMode,
)


class ConfluenceAuthenticationError(Exception):
    """Raised when Confluence authentication fails."""

    pass


class ConfluenceRateLimitError(Exception):
    """Raised when Confluence API rate limit is exceeded."""

    pass


class ConfluenceServerError(Exception):
    """Raised when Confluence server returns a 5xx error."""

    pass


class ConfluencePageNotFoundError(Exception):
    """Raised when a requested page or space is not found."""

    pass


class ConfluencePage:
    """Represents a Confluence page with extracted content."""

    def __init__(
        self,
        page_id: str,
        title: str,
        content: str,
        space_key: str,
        url: str,
        version: int = 1,
        labels: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        child_ids: Optional[List[str]] = None,
        last_modified: Optional[str] = None,
    ):
        self.page_id = page_id
        self.title = title
        self.content = content
        self.space_key = space_key
        self.url = url
        self.version = version
        self.labels = labels or []
        self.parent_id = parent_id
        self.child_ids = child_ids or []
        self.last_modified = last_modified

    def to_dict(self) -> dict:
        """Convert page to dictionary."""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "content": self.content,
            "space_key": self.space_key,
            "url": self.url,
            "version": self.version,
            "labels": self.labels,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "last_modified": self.last_modified,
        }


class ConfluenceApiClient:
    """
    Client for interacting with Confluence Cloud API.

    Supports:
    - Authentication via Basic Auth (email + API token)
    - Fetching pages from specific spaces
    - Fetching specific pages by ID
    - Searching pages by labels
    - Fetching recently modified pages
    - Converting Confluence Storage Format to Markdown
    - Handling pagination and rate limiting
    """

    # API endpoints
    SEARCH_ENDPOINT = "/wiki/api/v2/pages"
    PAGES_ENDPOINT = "/wiki/api/v2/pages"
    SPACES_ENDPOINT = "/wiki/api/v2/spaces"

    # Pagination
    DEFAULT_LIMIT = 25
    MAX_LIMIT = 250

    def __init__(self, config: ConfluenceConfig):
        """
        Initialize Confluence API client.

        Args:
            config: ConfluenceConfig with cloud_url, username/email, and API token
        """
        self.config = config
        self.base_url = config.cloud_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

        # Prepare Basic Auth header
        credentials = f"{config.username_or_email}:{config.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded}"

        logger.debug(f"Initialized Confluence API client for {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def verify_credentials(self) -> bool:
        """
        Verify that credentials are valid by making a test API call.

        Returns:
            bool: True if credentials are valid

        Raises:
            ConfluenceAuthenticationError: If credentials are invalid
        """
        try:
            async with self.session.get(
                urljoin(self.base_url, self.SPACES_ENDPOINT),
                headers=self._get_headers(),
                params={"limit": 1},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    raise ConfluenceAuthenticationError(
                        "Invalid Confluence credentials"
                    )
                if resp.status == 403:
                    raise ConfluenceAuthenticationError(
                        "User does not have permission to access Confluence"
                    )
                if resp.status >= 500:
                    raise ConfluenceServerError(
                        f"Confluence server error: {resp.status}"
                    )
                if resp.status >= 400:
                    raise ConfluencePageNotFoundError(
                        f"Invalid Confluence URL or API not available: {resp.status}"
                    )

                logger.info("Confluence credentials verified successfully")
                return True
        except asyncio.TimeoutError:
            raise ConfluenceAuthenticationError(
                "Connection timeout - invalid Confluence URL or server unreachable"
            )

    async def get_space_pages(
        self, space_key: str, max_pages: Optional[int] = None
    ) -> List[ConfluencePage]:
        """
        Fetch all pages in a specific space.

        Args:
            space_key: The space key (e.g., "TECH")
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            List[ConfluencePage]: Pages in the space

        Raises:
            ConfluencePageNotFoundError: If space doesn't exist
            ConfluenceRateLimitError: If rate limited
            ConfluenceServerError: If server error occurs
        """
        logger.info(f"Fetching pages from space: {space_key}")
        pages = []
        start = 0

        while True:
            try:
                params = {
                    "space-key": space_key,
                    "limit": self.MAX_LIMIT,
                    "start": start,
                    "expand": "body.storage,history,children",
                }

                async with self.session.get(
                    urljoin(self.base_url, self.SEARCH_ENDPOINT),
                    headers=self._get_headers(),
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 401:
                        raise ConfluenceAuthenticationError(
                            "Authentication failed"
                        )
                    if resp.status == 403:
                        raise ConfluenceAuthenticationError(
                            "Permission denied to access this space"
                        )
                    if resp.status == 404:
                        raise ConfluencePageNotFoundError(
                            f"Space not found: {space_key}"
                        )
                    if resp.status == 429:
                        raise ConfluenceRateLimitError(
                            "Rate limit exceeded - please try again later"
                        )
                    if resp.status >= 500:
                        raise ConfluenceServerError(
                            f"Server error: {resp.status}"
                        )

                    data = await resp.json()

                    if not data.get("results"):
                        logger.debug(
                            f"No more pages found for space {space_key}"
                        )
                        break

                    for page_data in data["results"]:
                        page = self._parse_page(page_data)
                        pages.append(page)
                        logger.debug(f"Fetched page: {page.title} ({page.page_id})")

                    # Check if we should stop
                    if max_pages and len(pages) >= max_pages:
                        pages = pages[:max_pages]
                        logger.info(
                            f"Reached max_pages limit: {max_pages}"
                        )
                        break

                    # Check pagination
                    if not data.get("_links", {}).get("next"):
                        logger.debug(
                            f"Completed pagination for space {space_key}"
                        )
                        break

                    start = data.get("start", 0) + len(data.get("results", []))

            except asyncio.TimeoutError:
                logger.error(
                    f"Timeout fetching pages from space {space_key}"
                )
                raise ConfluenceServerError(
                    "Request timeout - server not responding"
                )

        logger.info(f"Fetched {len(pages)} pages from space {space_key}")
        return pages

    async def get_page_by_id(
        self, page_id: str, expand_children: bool = True
    ) -> ConfluencePage:
        """
        Fetch a specific page by ID.

        Args:
            page_id: The page ID
            expand_children: Whether to fetch child pages

        Returns:
            ConfluencePage: The requested page

        Raises:
            ConfluencePageNotFoundError: If page doesn't exist
        """
        logger.info(f"Fetching page: {page_id}")

        try:
            expand = "body.storage,history,children" if expand_children else "body.storage,history"
            params = {"expand": expand}

            async with self.session.get(
                urljoin(self.base_url, f"{self.PAGES_ENDPOINT}/{page_id}"),
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 404:
                    raise ConfluencePageNotFoundError(
                        f"Page not found: {page_id}"
                    )
                if resp.status == 401:
                    raise ConfluenceAuthenticationError(
                        "Authentication failed"
                    )
                if resp.status == 429:
                    raise ConfluenceRateLimitError(
                        "Rate limit exceeded"
                    )
                if resp.status >= 500:
                    raise ConfluenceServerError(
                        f"Server error: {resp.status}"
                    )

                data = await resp.json()
                page = self._parse_page(data)
                logger.info(f"Fetched page: {page.title}")
                return page

        except asyncio.TimeoutError:
            raise ConfluenceServerError("Request timeout")

    async def get_pages_by_label(
        self, labels: List[str], max_pages: Optional[int] = None
    ) -> List[ConfluencePage]:
        """
        Fetch pages matching specific labels.

        Args:
            labels: List of labels to search for
            max_pages: Maximum number of pages to fetch

        Returns:
            List[ConfluencePage]: Pages matching the labels
        """
        logger.info(f"Searching for pages with labels: {labels}")
        pages = []
        start = 0

        # Build CQL query for labels
        label_query = " OR ".join([f'label = "{label}"' for label in labels])
        cql = f"({label_query}) AND type = page"

        while True:
            try:
                params = {
                    "cql": cql,
                    "limit": self.MAX_LIMIT,
                    "start": start,
                    "expand": "body.storage,history,children",
                }

                async with self.session.get(
                    urljoin(self.base_url, self.SEARCH_ENDPOINT),
                    headers=self._get_headers(),
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 400:
                        logger.warning(
                            f"Invalid CQL query for labels: {labels}"
                        )
                        break
                    if resp.status == 401:
                        raise ConfluenceAuthenticationError(
                            "Authentication failed"
                        )
                    if resp.status == 429:
                        raise ConfluenceRateLimitError(
                            "Rate limit exceeded"
                        )
                    if resp.status >= 500:
                        raise ConfluenceServerError(
                            f"Server error: {resp.status}"
                        )

                    data = await resp.json()

                    if not data.get("results"):
                        logger.debug("No more pages found with given labels")
                        break

                    for page_data in data["results"]:
                        page = self._parse_page(page_data)
                        pages.append(page)

                    if max_pages and len(pages) >= max_pages:
                        pages = pages[:max_pages]
                        break

                    if not data.get("_links", {}).get("next"):
                        break

                    start = data.get("start", 0) + len(data.get("results", []))

            except asyncio.TimeoutError:
                logger.error("Timeout searching for pages by label")
                raise ConfluenceServerError("Request timeout")

        logger.info(
            f"Found {len(pages)} pages matching labels: {labels}"
        )
        return pages

    async def get_recently_modified_pages(
        self, limit: int = 50
    ) -> List[ConfluencePage]:
        """
        Fetch recently modified pages.

        Args:
            limit: Maximum number of pages to fetch

        Returns:
            List[ConfluencePage]: Recently modified pages
        """
        logger.info(f"Fetching {limit} recently modified pages")

        try:
            # CQL query for pages modified within last 30 days
            cql = 'type = page AND modified >= -30d ORDER BY modified DESC'

            params = {
                "cql": cql,
                "limit": min(limit, self.MAX_LIMIT),
                "expand": "body.storage,history,children",
            }

            async with self.session.get(
                urljoin(self.base_url, self.SEARCH_ENDPOINT),
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise ConfluenceAuthenticationError(
                        "Authentication failed"
                    )
                if resp.status == 429:
                    raise ConfluenceRateLimitError(
                        "Rate limit exceeded"
                    )
                if resp.status >= 500:
                    raise ConfluenceServerError(
                        f"Server error: {resp.status}"
                    )

                data = await resp.json()
                pages = [
                    self._parse_page(page_data)
                    for page_data in data.get("results", [])
                ]

                logger.info(f"Fetched {len(pages)} recently modified pages")
                return pages

        except asyncio.TimeoutError:
            raise ConfluenceServerError("Request timeout")

    def _parse_page(self, page_data: dict) -> ConfluencePage:
        """
        Parse Confluence API page response to ConfluencePage.

        Args:
            page_data: Raw page data from API

        Returns:
            ConfluencePage: Parsed page object
        """
        page_id = page_data.get("id", "")
        title = page_data.get("title", "Untitled")

        # Extract storage format content and convert to markdown
        storage_content = (
            page_data.get("body", {})
            .get("storage", {})
            .get("value", "")
        )
        markdown_content = self._convert_storage_to_markdown(
            storage_content
        )

        # Extract space key from metadata
        space = page_data.get("space", {})
        space_key = space.get("key", "UNKNOWN")

        # Get page URL
        links = page_data.get("_links", {})
        url = urljoin(self.base_url, links.get("webui", ""))

        # Extract metadata
        version = page_data.get("version", {}).get("number", 1)
        labels = [
            label.get("name", "")
            for label in page_data.get("metadata", {})
            .get("labels", {})
            .get("results", [])
        ]
        last_modified = (
            page_data.get("version", {})
            .get("createdAt", "")
        )

        # Extract parent/children relationships
        parent_id = None
        if "ancestors" in page_data and page_data["ancestors"]:
            parent_id = page_data["ancestors"][-1].get("id")

        child_ids = []
        if "children" in page_data:
            children = page_data["children"].get("page", {}).get("results", [])
            child_ids = [child.get("id", "") for child in children]

        return ConfluencePage(
            page_id=page_id,
            title=title,
            content=markdown_content,
            space_key=space_key,
            url=url,
            version=version,
            labels=labels,
            parent_id=parent_id,
            child_ids=child_ids,
            last_modified=last_modified,
        )

    @staticmethod
    def _convert_storage_to_markdown(storage_content: str) -> str:
        """
        Convert Confluence Storage Format (XHTML) to Markdown.

        This is a basic implementation that handles common patterns.
        For more complex conversions, consider using a dedicated library.

        Args:
            storage_content: Raw Confluence storage format HTML

        Returns:
            str: Markdown representation
        """
        if not storage_content:
            return ""

        # Remove Confluence-specific tags
        content = re.sub(r'<ac:.*?</ac:[^>]*>', '', storage_content, flags=re.DOTALL)
        content = re.sub(r'<ri:.*?/>', '', content)

        # Convert headings
        content = re.sub(r'<h([1-6])>(.*?)</h\1>', r'#\1 \2', content, flags=re.DOTALL)
        content = re.sub(r'#+', lambda m: m.group(0) if len(m.group(0)) < 7 else '#' * 6, content)

        # Convert bold
        content = re.sub(r'<(strong|b)>(.*?)</\1>', r'**\2**', content, flags=re.DOTALL)

        # Convert italic
        content = re.sub(r'<(em|i)>(.*?)</\1>', r'*\2*', content, flags=re.DOTALL)

        # Convert links
        content = re.sub(
            r'<a\s+href="([^"]*)">([^<]*)</a>',
            r'[\2](\1)',
            content,
        )

        # Convert code
        content = re.sub(
            r'<code>(.*?)</code>',
            r'`\1`',
            content,
            flags=re.DOTALL,
        )

        # Convert pre/code blocks
        content = re.sub(
            r'<pre[^>]*>(.*?)</pre>',
            r'```\n\1\n```',
            content,
            flags=re.DOTALL,
        )

        # Convert lists
        content = re.sub(r'<li>(.*?)</li>', r'- \1', content, flags=re.DOTALL)

        # Convert line breaks
        content = re.sub(r'<br\s*/?>', '\n', content)

        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)

        # Clean up whitespace
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)

        return content.strip()

    def _get_headers(self) -> dict:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": self.auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "DataPilotFlow/1.0",
        }
