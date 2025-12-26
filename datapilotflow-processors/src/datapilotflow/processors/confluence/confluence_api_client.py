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
    Client for interacting with Confluence Cloud API or Server/Data Center API.

    Supports:
    - Authentication via Basic Auth (email + API token)
    - Auto-detection of Confluence Cloud vs Server/Data Center
    - Fetching pages from specific spaces
    - Fetching specific pages by ID
    - Searching pages by labels
    - Fetching recently modified pages
    - Converting Confluence Storage Format to Markdown
    - Handling pagination and rate limiting
    """

    # Cloud API v2 endpoints
    CLOUD_SEARCH_ENDPOINT = "/wiki/api/v2/pages"
    CLOUD_PAGES_ENDPOINT = "/wiki/api/v2/pages"
    CLOUD_SPACES_ENDPOINT = "/wiki/api/v2/spaces"

    # Server/Data Center API v1 endpoints
    SERVER_SPACES_ENDPOINT = "/rest/api/space"
    SERVER_PAGES_ENDPOINT = "/rest/api/content"

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
        self.auth_method = None  # Will be determined as "bearer" or "basic"

        # Prepare both Bearer and Basic Auth headers
        # Bearer token (works for Server/Data Center with token auth)
        self.bearer_auth_header = f"Bearer {config.api_token}"

        # Basic Auth (works for Cloud and some Server/Data Center setups)
        credentials = f"{config.username_or_email}:{config.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.basic_auth_header = f"Basic {encoded}"

        # Default to Bearer first (since that's what works)
        self.auth_header = self.bearer_auth_header

        # Set Confluence type if provided, otherwise will be auto-detected on first API call
        if config.is_cloud_instance is not None:
            self.is_cloud = config.is_cloud_instance
            self.is_server = not config.is_cloud_instance
            instance_type = "Cloud" if self.is_cloud else "Local/Self-Hosted"
            logger.debug(f"Initialized Confluence API client for {self.base_url} (explicitly configured as {instance_type})")
        else:
            self.is_cloud = None  # Will be determined on first API call
            self.is_server = None  # Will be determined on first API call
            logger.debug(f"Initialized Confluence API client for {self.base_url} (will auto-detect instance type)")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _detect_confluence_type(self) -> bool:
        """
        Detect whether this is Confluence Cloud or Server/Data Center.

        Returns:
            True if Cloud, False if Server/Data Center

        Raises:
            ConfluenceAuthenticationError: If credentials are invalid
            ConfluenceServerError: If server error occurs
        """
        if self.is_cloud is not None:
            return self.is_cloud

        cloud_auth_error = None
        server_auth_error = None

        # Check if this is a local instance (localhost, 127.0.0.1, etc.)
        is_local = (
            "localhost" in self.base_url.lower()
            or "127.0.0.1" in self.base_url
            or "0.0.0.0" in self.base_url
        )

        if not is_local:
            # Only try Cloud API v2 for non-local URLs (actual Cloud instances)
            try:
                async with self.session.get(
                    urljoin(self.base_url, self.CLOUD_SPACES_ENDPOINT),
                    headers=self._get_headers(),
                    params={"limit": 1},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    logger.debug(f"Cloud API v2 response: {resp.status}")
                    content_type = resp.headers.get("content-type", "").lower()
                    logger.debug(f"Cloud API v2 content-type: {content_type}")

                    if resp.status == 200 and "application/json" in content_type:
                        logger.debug("Detected Confluence Cloud (v2 API)")
                        self.is_cloud = True
                        self.is_server = False
                        return True
                    elif resp.status == 200 and "text/html" in content_type:
                        logger.debug("Cloud API v2 returned HTML (not JSON) - likely not Cloud API")
                    elif resp.status == 401:
                        cloud_auth_error = "Invalid Confluence credentials (Cloud API)"
                    elif resp.status == 403:
                        cloud_auth_error = "User does not have permission to access Confluence (Cloud API)"
            except asyncio.TimeoutError:
                logger.debug("Cloud API v2 timeout")
            except Exception as e:
                logger.debug(f"Cloud API v2 not available: {e}")
        else:
            logger.debug(f"Local Confluence instance detected ({self.base_url}) - skipping Cloud API check")

        # Try Server/Data Center API v1
        try:
            async with self.session.get(
                urljoin(self.base_url, self.SERVER_SPACES_ENDPOINT),
                headers=self._get_headers(),
                params={"limit": 1},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                logger.debug(f"Server API v1 response: {resp.status}")
                response_text = await resp.text()
                logger.debug(f"Server API response: {response_text[:200]}")

                if resp.status == 200:
                    logger.debug("Detected Confluence Server/Data Center (v1 API)")
                    self.is_cloud = False
                    self.is_server = True
                    return False
                elif resp.status == 401:
                    # Check if it's a Basic Auth disabled message
                    if "Basic Authentication has been disabled" in response_text:
                        server_auth_error = "Basic Authentication is disabled on this Confluence instance. Enable Basic Auth or use Confluence Cloud with API tokens."
                    else:
                        server_auth_error = "Invalid Confluence credentials (Server API)"
                elif resp.status == 403:
                    server_auth_error = "User does not have permission to access Confluence (Server API)"
        except asyncio.TimeoutError:
            logger.debug("Server API v1 timeout")
        except Exception as e:
            logger.debug(f"Server API v1 not available: {e}")

        # If we have specific auth errors, raise them
        if cloud_auth_error or server_auth_error:
            error_msg = server_auth_error or cloud_auth_error

            # Provide helpful context for the user
            detailed_msg = (
                f"{error_msg}\n\n"
                "HINT: Pages in Confluence may have been created via the UI (logging in manually), "
                "not via API. To use API-based data extraction:\n"
                "1. Check Confluence Admin → Security Configuration → Enable Basic Authentication\n"
                "2. Verify your account has API token permissions\n"
                "3. If using Confluence Server/Data Center locally, OAuth is required (use admin panel)"
            )
            logger.warning(f"Confluence authentication error: {error_msg}")
            raise ConfluenceAuthenticationError(detailed_msg)

        # If neither API works, raise error with more details
        logger.error("Could not detect Confluence type - neither API is accessible")
        raise ConfluenceServerError(
            "Could not detect Confluence type - neither Cloud nor Server/Data Center API is accessible. "
            "Check that the Confluence URL is correct and the server is running."
        )

    async def verify_credentials(self) -> bool:
        """
        Verify that credentials are valid by detecting Confluence type and making a test API call.

        Returns:
            bool: True if credentials are valid

        Raises:
            ConfluenceAuthenticationError: If credentials are invalid
        """
        try:
            # This will detect and set self.is_cloud and self.is_server
            await self._detect_confluence_type()
            logger.info("Confluence credentials verified successfully")
            return True
        except asyncio.TimeoutError:
            raise ConfluenceAuthenticationError(
                "Connection timeout - invalid Confluence URL or server unreachable"
            )

    async def get_spaces(self) -> List[dict]:
        """
        Fetch all available spaces from Cloud or Server/Data Center Confluence.

        Returns:
            List[dict]: List of spaces with key and name

        Raises:
            ConfluenceAuthenticationError: If credentials are invalid
            ConfluenceServerError: If server error occurs
        """
        try:
            # Ensure we've detected the Confluence type
            if self.is_cloud is None:
                await self._detect_confluence_type()

            spaces = []

            # Use appropriate endpoint based on Confluence type
            if self.is_cloud:
                return await self._get_spaces_cloud(spaces)
            else:
                return await self._get_spaces_server(spaces)

        except (ConfluenceAuthenticationError, ConfluenceServerError, ConfluencePageNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error fetching spaces: {e}")
            raise ConfluenceServerError(f"Error fetching spaces: {str(e)}")

    async def _get_spaces_cloud(self, spaces: List[dict]) -> List[dict]:
        """Fetch spaces from Confluence Cloud using v2 API."""
        start = 0

        while True:
            try:
                params = {
                    "limit": self.MAX_LIMIT,
                    "start": start,
                }

                async with self.session.get(
                    urljoin(self.base_url, self.CLOUD_SPACES_ENDPOINT),
                    headers=self._get_headers(),
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 401:
                        raise ConfluenceAuthenticationError("Invalid Confluence credentials")
                    if resp.status == 403:
                        raise ConfluenceAuthenticationError("User does not have permission to access Confluence")
                    if resp.status >= 500:
                        raise ConfluenceServerError(f"Confluence server error: {resp.status}")
                    if resp.status >= 400:
                        raise ConfluencePageNotFoundError(f"Unable to fetch spaces: {resp.status}")

                    data = await resp.json()

                    if not data.get("results"):
                        logger.debug("No more spaces found")
                        break

                    for space_data in data["results"]:
                        space_info = {
                            "key": space_data.get("key"),
                            "name": space_data.get("name"),
                            "id": space_data.get("id"),
                        }
                        spaces.append(space_info)
                        logger.debug(f"Found space: {space_info['key']} - {space_info['name']}")

                    # Check pagination
                    if not data.get("_links", {}).get("next"):
                        logger.debug("Completed pagination for spaces")
                        break

                    start = data.get("start", 0) + len(data.get("results", []))

            except asyncio.TimeoutError:
                logger.error("Timeout fetching spaces")
                raise ConfluenceServerError("Request timeout - server not responding")

        logger.info(f"Fetched {len(spaces)} spaces from Cloud")
        return spaces

    async def _get_spaces_server(self, spaces: List[dict]) -> List[dict]:
        """Fetch spaces from Confluence Server/Data Center using v1 API."""
        start = 0

        while True:
            try:
                params = {
                    "limit": self.MAX_LIMIT,
                    "start": start,
                }

                async with self.session.get(
                    urljoin(self.base_url, self.SERVER_SPACES_ENDPOINT),
                    headers=self._get_headers(),
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 401:
                        raise ConfluenceAuthenticationError("Invalid Confluence credentials")
                    if resp.status == 403:
                        raise ConfluenceAuthenticationError("User does not have permission to access Confluence")
                    if resp.status >= 500:
                        raise ConfluenceServerError(f"Confluence server error: {resp.status}")
                    if resp.status >= 400:
                        raise ConfluencePageNotFoundError(f"Unable to fetch spaces: {resp.status}")

                    data = await resp.json()

                    # Server API returns results in a "results" key
                    results = data.get("results", [])
                    if not results:
                        logger.debug("No more spaces found")
                        break

                    for space_data in results:
                        space_info = {
                            "key": space_data.get("key"),
                            "name": space_data.get("name"),
                            "id": space_data.get("id"),
                        }
                        spaces.append(space_info)
                        logger.debug(f"Found space: {space_info['key']} - {space_info['name']}")

                    # Check pagination - Server API may not have _links
                    if isinstance(results, list) and len(results) < self.MAX_LIMIT:
                        logger.debug("Completed pagination for spaces")
                        break

                    start = data.get("start", 0) + len(results) if isinstance(results, list) else start + self.MAX_LIMIT

            except asyncio.TimeoutError:
                logger.error("Timeout fetching spaces")
                raise ConfluenceServerError("Request timeout - server not responding")

        logger.info(f"Fetched {len(spaces)} spaces from Server/Data Center")
        return spaces

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

        # Ensure we've detected the Confluence type
        if self.is_cloud is None:
            await self._detect_confluence_type()

        pages = []
        start = 0

        while True:
            try:
                # Use the correct endpoint based on Confluence type
                if self.is_cloud:
                    endpoint = self.CLOUD_SEARCH_ENDPOINT
                    params = {
                        "space-key": space_key,
                        "limit": self.MAX_LIMIT,
                        "start": start,
                        "expand": "body.storage,history,children",
                    }
                else:
                    endpoint = self.SERVER_PAGES_ENDPOINT
                    params = {
                        "spaceKey": space_key,
                        "limit": self.MAX_LIMIT,
                        "start": start,
                        "expand": "body.storage,history,children",
                    }

                async with self.session.get(
                    urljoin(self.base_url, endpoint),
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

        # Ensure we've detected the Confluence type
        if self.is_cloud is None:
            await self._detect_confluence_type()

        try:
            expand = "body.storage,history,children" if expand_children else "body.storage,history"
            params = {"expand": expand}

            # Use the correct endpoint based on Confluence type
            if self.is_cloud:
                endpoint = f"{self.CLOUD_PAGES_ENDPOINT}/{page_id}"
            else:
                endpoint = f"{self.SERVER_PAGES_ENDPOINT}/{page_id}"

            async with self.session.get(
                urljoin(self.base_url, endpoint),
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

        # Ensure we've detected the Confluence type
        if self.is_cloud is None:
            await self._detect_confluence_type()

        pages = []
        start = 0

        # Build CQL query for labels
        label_query = " OR ".join([f'label = "{label}"' for label in labels])
        cql = f"({label_query}) AND type = page"

        while True:
            try:
                # Use the correct endpoint based on Confluence type
                if self.is_cloud:
                    endpoint = self.CLOUD_SEARCH_ENDPOINT
                else:
                    endpoint = self.SERVER_PAGES_ENDPOINT

                params = {
                    "cql": cql,
                    "limit": self.MAX_LIMIT,
                    "start": start,
                    "expand": "body.storage,history,children",
                }

                async with self.session.get(
                    urljoin(self.base_url, endpoint),
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

        # Ensure we've detected the Confluence type
        if self.is_cloud is None:
            await self._detect_confluence_type()

        try:
            # CQL query for pages modified within last 30 days
            cql = 'type = page AND modified >= -30d ORDER BY modified DESC'

            # Use the correct endpoint based on Confluence type
            if self.is_cloud:
                endpoint = self.CLOUD_SEARCH_ENDPOINT
            else:
                endpoint = self.SERVER_PAGES_ENDPOINT

            params = {
                "cql": cql,
                "limit": min(limit, self.MAX_LIMIT),
                "expand": "body.storage,history,children",
            }

            async with self.session.get(
                urljoin(self.base_url, endpoint),
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
