"""
Duplicate detection for documents using Milvus.
"""

import traceback
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from loguru import logger

from datapilotflow.domain.config import settings
from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.infrastructure.milvus.client import MilvusClientWrapper


class DuplicateDetector:
    """Detect duplicate documents using Milvus."""

    def __init__(self, milvus_client: Optional[MilvusClientWrapper] = None):
        """Initialize the duplicate detector.

        Args:
            milvus_client: Milvus client wrapper. If None, duplicate detection will be disabled.
                          Pass the job's Milvus client to use the correct collection and vector dimension.
        """
        try:
            if milvus_client is None:
                logger.warning(
                    "No Milvus client provided to duplicate detector - duplicate detection will be disabled"
                )
                self.milvus_client = None
            else:
                self.milvus_client = milvus_client
                logger.info(
                    f"Duplicate detector initialized with Milvus collection: {milvus_client.collection_name}"
                )
        except Exception as e:
            logger.warning(f"Error initializing duplicate detector: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Set milvus_client to None to indicate initialization failed
            self.milvus_client = None

    def get_existing_urls(self) -> Set[str]:
        """Get existing URLs from Milvus collection.

        Fetches all URLs from the collection (no filtering needed since
        duplicate detection works at collection level).

        Returns:
            Set of existing URLs in the collection
        """
        # Check if milvus_client is available
        if self.milvus_client is None:
            logger.warning("Milvus client not available, skipping duplicate detection")
            return set()

        try:
            logger.info(
                f"Loading existing URLs from collection {self.milvus_client.collection_name}"
            )

            # Load from Milvus
            milvus_urls = self._get_existing_urls_from_milvus()

            logger.info(
                f"Found {len(milvus_urls)} existing URLs in collection {self.milvus_client.collection_name}"
            )
            return milvus_urls

        except Exception as e:
            logger.warning(f"Error loading existing URLs: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return set()

    def _get_existing_urls_from_milvus(self) -> Set[str]:
        """Get ALL existing URLs from Milvus collection using pagination.

        Uses query_iterator to fetch all URLs without memory issues,
        regardless of collection size (works with millions of chunks).

        Returns:
            Set of existing URLs
        """
        # Check if milvus_client is available
        if self.milvus_client is None:
            logger.warning("Milvus client not available, skipping duplicate detection")
            return set()

        try:
            # Load collection into memory for querying
            self.milvus_client.collection.load()

            # Use query_iterator for paginated fetching (handles large collections)
            # This fetches ALL entities without hard-coded limits
            urls = set()
            batch_count = 0
            total_entities = 0

            logger.info(
                f"Loading existing URLs from collection {self.milvus_client.collection_name} using pagination..."
            )

            # Create iterator with batch size for efficient memory usage
            # Determine which primary key to use for the query expression
            # New collections: correlation_id (primary key)
            # Old collections: id (primary key)
            try:
                # Try to get schema to determine primary key
                schema = self.milvus_client.collection.schema
                primary_field = None
                for field in schema.fields:
                    if field.is_primary:
                        primary_field = field.name
                        break

                if primary_field:
                    expr = f"{primary_field} != ''" if primary_field in ["id", "correlation_id"] else None
                    logger.debug(f"Using primary key '{primary_field}' for query expression")
                else:
                    # Fallback: try correlation_id first, then id
                    expr = "correlation_id != ''"
                    logger.debug("No primary key detected, using correlation_id as default")
            except Exception as e:
                # If schema inspection fails, use correlation_id as default
                expr = "correlation_id != ''"
                logger.debug(f"Could not inspect schema ({e}), using correlation_id as default")

            iterator = self.milvus_client.collection.query_iterator(
                batch_size=5000,  # Process 5000 entities per batch
                expr=expr,  # Get all entities using primary key check
                output_fields=["source_url"],
                # limit=-1 means fetch ALL matching entities (default behavior)
            )

            # Iterate through all batches using the iterator pattern
            while True:
                result = iterator.next()
                if not result:
                    # No more results - close iterator and break
                    iterator.close()
                    break

                batch_count += 1
                total_entities += len(result)

                # Extract URLs from batch
                # result is a list of dictionaries with entity data
                for entity in result:
                    source_url = entity.get("source_url")
                    if source_url:
                        urls.add(source_url)

                logger.debug(
                    f"Batch {batch_count}: Processed {len(result)} entities, "
                    f"found {len(urls)} unique URLs so far (total entities: {total_entities})"
                )

            logger.info(
                f"✅ Retrieved {len(urls)} unique URLs from {total_entities} total entities "
                f"in collection {self.milvus_client.collection_name} (processed in {batch_count} batches)"
            )
            return urls

        except Exception as e:
            logger.warning(
                f"Error getting existing URLs from collection {self.milvus_client.collection_name}: {e}"
            )
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Return empty set on error - this allows processing to continue
            return set()

    def is_duplicate_url(self, url: str, existing_urls: Set[str]) -> bool:
        """Check if a URL is a duplicate.

        Args:
            url: URL to check
            existing_urls: Set of existing URLs

        Returns:
            True if URL is a duplicate, False otherwise
        """
        return url in existing_urls

    def filter_duplicate_urls(
        self, urls: List[str], knowledge_source: str
    ) -> List[str]:
        """Filter out duplicate URLs.

        Args:
            urls: List of URLs to filter
            knowledge_source: Knowledge source name

        Returns:
            List of non-duplicate URLs
        """
        try:
            existing_urls = self.get_existing_urls(knowledge_source)

            non_duplicates = []
            duplicates = []

            for url in urls:
                if self.is_duplicate_url(url, existing_urls):
                    duplicates.append(url)
                else:
                    non_duplicates.append(url)

            logger.info(
                f"Filtered {len(urls)} URLs for {knowledge_source}: {len(non_duplicates)} new, {len(duplicates)} duplicates"
            )

            if duplicates:
                logger.info(
                    f"Duplicate URLs found: {duplicates[:5]}{'...' if len(duplicates) > 5 else ''}"
                )

            return non_duplicates

        except Exception as e:
            logger.error(f"Error filtering duplicate URLs: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return urls  # Return original list on error

    def filter_new_documents(self, documents: List[Any], job_id: str) -> List[Any]:
        """Filter out documents with duplicate URLs.

        Args:
            documents: List of Document objects to filter
            job_id: Job ID (for logging purposes only - filtering is done by collection)

        Returns:
            List of non-duplicate documents
        """
        try:
            logger.debug(
                f"🔍 DUPLICATE DETECTION: Checking {len(documents)} documents for job {job_id}"
            )

            # Get existing URLs from Milvus for this job
            existing_urls = self.get_existing_urls(job_id)
            logger.debug(
                f"🔍 DUPLICATE DETECTION: Found {len(existing_urls)} existing URLs in collection for job {job_id}"
            )

            non_duplicates = []
            duplicates = []
            duplicate_details = []

            for doc in documents:
                url = doc.metadata.get("source_url", "")
                if self.is_duplicate_url(url, existing_urls):
                    duplicates.append(doc)
                    duplicate_details.append(
                        {"url": url, "title": doc.metadata.get("title", "N/A")}
                    )
                    logger.debug(f"❌ DUPLICATE FOUND: {url}")
                else:
                    non_duplicates.append(doc)
                    logger.debug(f"✅ NEW DOCUMENT: {url}")

            # Summary logging
            logger.info(
                f"🔍 DUPLICATE DETECTION SUMMARY: "
                f"Total={len(documents)}, New={len(non_duplicates)}, Duplicates={len(duplicates)}"
            )

            if duplicates:
                logger.info(f"📋 DUPLICATE DETAILS ({len(duplicates)} total):")
                for i, dup in enumerate(duplicate_details[:10], 1):  # Show first 10
                    logger.info(f"  {i}. {dup['url']} - {dup['title']}")
                if len(duplicates) > 10:
                    logger.info(f"  ... and {len(duplicates) - 10} more duplicates")
            else:
                logger.info(f"✅ NO DUPLICATES: All {len(documents)} documents are new")

            return non_duplicates

        except Exception as e:
            logger.error(f"❌ ERROR filtering duplicate documents: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.warning(f"⚠️  Returning all {len(documents)} documents due to error")
            return documents  # Return original list on error

    def get_url_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return url

    def close(self):
        """Close the Weaviate client connection.

        This method should be called when the duplicate detector is no longer needed
        to properly release resources.
        """
        if hasattr(self, "weaviate_client") and self.weaviate_client:
            try:
                self.weaviate_client.close()
                logger.debug("Closed Weaviate client connection in duplicate detector")
            except Exception as e:
                logger.warning(
                    f"Error closing Weaviate client in duplicate detector: {e}"
                )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically close the connection."""
        self.close()

    def get_domain_statistics(self, urls: List[str]) -> Dict[str, int]:
        """Get statistics by domain.

        Args:
            urls: List of URLs

        Returns:
            Dictionary mapping domains to URL counts
        """
        domain_counts = {}
        for url in urls:
            domain = self.get_url_domain(url)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        return domain_counts
