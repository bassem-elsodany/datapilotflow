"""
Duplicate Cleanup Script for Milvus Collections

This script identifies and removes duplicate chunks from Milvus collections.

PROBLEM:
- You have duplicate chunks due to the limit=10000 bug
- Re-running jobs would cost money (crawling + embeddings)

SOLUTION:
- Group chunks by correlation_id (source_url + chunk_index + content_hash)
- Keep the newest chunk for each correlation_id
- Delete older duplicates

USAGE:
    # Dry run (preview only, no deletions)
    python cleanup_duplicates.py --collection-name "your_collection" --dry-run

    # Actual cleanup
    python cleanup_duplicates.py --collection-name "your_collection"

    # Cleanup specific user's collection
    python cleanup_duplicates.py --collection-name "user_123_collection" --user-id "user_123"
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple

sys.path.insert(0, 'src')

from loguru import logger
from src.domain.rag.knowledge_chunk import KnowledgeChunk
from src.infrastructure.milvus.client import MilvusClientWrapper
from src.config import settings


class DuplicateCleanup:
    """Clean up duplicate chunks in Milvus collection."""

    def __init__(self, collection_name: str, vector_dimension: int = 1536, dry_run: bool = True):
        """
        Initialize duplicate cleanup.

        Args:
            collection_name: Name of the Milvus collection
            vector_dimension: Dimension of embedding vectors
            dry_run: If True, only preview changes without deleting
        """
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension
        self.dry_run = dry_run

        logger.info(f"Initializing cleanup for collection: {collection_name}")
        logger.info(f"Mode: {'DRY RUN (preview only)' if dry_run else 'CLEANUP (will delete duplicates)'}")

        # Connect to Milvus
        self.client = MilvusClientWrapper(
            model=KnowledgeChunk,
            collection_name=collection_name,
            vector_dimension=vector_dimension,
        )

    def get_all_chunks(self) -> List[Dict]:
        """
        Fetch all chunks from the collection using pagination.

        Returns:
            List of all chunk entities with their metadata
        """
        logger.info("Fetching all chunks from collection using pagination...")

        self.client.collection.load()

        all_chunks = []
        batch_count = 0

        # Determine primary key field
        schema = self.client.collection.schema
        primary_field = None
        for field in schema.fields:
            if field.is_primary:
                primary_field = field.name
                break

        if not primary_field:
            primary_field = "id"  # Fallback for old collections

        logger.info(f"Primary key field: {primary_field}")

        # Create iterator to fetch all entities
        iterator = self.client.collection.query_iterator(
            batch_size=5000,
            expr=f"{primary_field} != ''",
            output_fields=["source_url", "chunk_index", "created_at", "job_id", "page_content"],
        )

        # Iterate through all batches
        while True:
            result = iterator.next()
            if not result:
                iterator.close()
                break

            batch_count += 1
            all_chunks.extend(result)

            logger.info(f"Batch {batch_count}: Fetched {len(result)} chunks (total: {len(all_chunks)})")

        logger.info(f"✅ Fetched {len(all_chunks)} total chunks from collection")
        return all_chunks

    def calculate_correlation_id(self, chunk: Dict) -> str:
        """
        Calculate correlation_id for a chunk.

        For old collections with 'id' primary key, we need to recalculate correlation_id
        from the chunk's data.

        Args:
            chunk: Chunk entity dictionary

        Returns:
            Correlation ID string
        """
        import hashlib

        source_url = chunk.get("source_url", "")
        chunk_index = chunk.get("chunk_index", 0)
        page_content = chunk.get("page_content", "")
        content_hash = hashlib.md5(page_content.encode()).hexdigest()

        return f"{source_url}_{chunk_index}_{content_hash}"

    def find_duplicates(self, chunks: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, Dict]]:
        """
        Identify duplicate chunks by correlation_id.

        Args:
            chunks: List of all chunks

        Returns:
            Tuple of (duplicates_map, keep_map):
            - duplicates_map: {correlation_id: [list of duplicate chunks]}
            - keep_map: {correlation_id: chunk_to_keep}
        """
        logger.info("Analyzing chunks for duplicates...")

        # Group chunks by correlation_id
        chunks_by_correlation_id: Dict[str, List[Dict]] = defaultdict(list)

        for chunk in chunks:
            # Get primary key (could be 'id' or 'correlation_id' depending on schema)
            primary_key = chunk.get("correlation_id") or chunk.get("id")

            if not primary_key:
                logger.warning(f"Chunk has no primary key, skipping: {chunk}")
                continue

            # For old collections, calculate correlation_id
            correlation_id = self.calculate_correlation_id(chunk)

            # Add primary key to chunk for later deletion
            chunk["_primary_key"] = primary_key
            chunk["_correlation_id"] = correlation_id

            chunks_by_correlation_id[correlation_id].append(chunk)

        # Find duplicates (correlation_ids with multiple chunks)
        duplicates_map = {}
        keep_map = {}

        for correlation_id, chunk_list in chunks_by_correlation_id.items():
            if len(chunk_list) > 1:
                # Sort by created_at (keep newest) or by primary key (keep first if no timestamp)
                sorted_chunks = sorted(
                    chunk_list,
                    key=lambda c: c.get("created_at", ""),
                    reverse=True  # Newest first
                )

                keep_map[correlation_id] = sorted_chunks[0]  # Keep newest
                duplicates_map[correlation_id] = sorted_chunks[1:]  # Delete older ones

        logger.info(f"Analysis complete:")
        logger.info(f"  Total unique correlation_ids: {len(chunks_by_correlation_id)}")
        logger.info(f"  Correlation_ids with duplicates: {len(duplicates_map)}")
        logger.info(f"  Total duplicate chunks to delete: {sum(len(v) for v in duplicates_map.values())}")

        return duplicates_map, keep_map

    def group_by_url(self, duplicates_map: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Group duplicates by source_url for reporting.

        Args:
            duplicates_map: Map of correlation_id to duplicate chunks

        Returns:
            Map of source_url to list of all duplicates for that URL
        """
        url_duplicates = defaultdict(list)

        for correlation_id, duplicate_chunks in duplicates_map.items():
            for chunk in duplicate_chunks:
                source_url = chunk.get("source_url", "unknown")
                url_duplicates[source_url].extend(duplicate_chunks)

        return dict(url_duplicates)

    def preview_cleanup(self, duplicates_map: Dict[str, List[Dict]], keep_map: Dict[str, Dict]):
        """
        Preview what will be deleted without actually deleting.

        Args:
            duplicates_map: Map of correlation_id to duplicate chunks
            keep_map: Map of correlation_id to chunk to keep
        """
        logger.info("=" * 80)
        logger.info("DUPLICATE CLEANUP PREVIEW")
        logger.info("=" * 80)

        # Group by URL
        url_duplicates = self.group_by_url(duplicates_map)

        logger.info(f"\nFound duplicates for {len(url_duplicates)} URLs:")
        logger.info("")

        for url, dup_chunks in sorted(url_duplicates.items(), key=lambda x: len(x[1]), reverse=True):
            logger.info(f"URL: {url}")
            logger.info(f"  Duplicate chunks: {len(dup_chunks)}")
            logger.info("")

        # Show top 10 URLs with most duplicates
        logger.info("\nTop 10 URLs with most duplicates:")
        logger.info("=" * 80)

        top_urls = sorted(url_duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]

        for i, (url, dup_chunks) in enumerate(top_urls, 1):
            logger.info(f"{i}. {url[:80]}...")
            logger.info(f"   Duplicates: {len(dup_chunks)} chunks")

            # Show example
            if dup_chunks:
                example = dup_chunks[0]
                logger.info(f"   Example duplicate primary key: {example.get('_primary_key')}")
                logger.info(f"   Created at: {example.get('created_at', 'N/A')}")
                logger.info(f"   Job ID: {example.get('job_id', 'N/A')}")
            logger.info("")

        # Summary
        total_to_delete = sum(len(v) for v in duplicates_map.values())
        total_to_keep = len(keep_map)

        logger.info("=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total chunks currently in collection: {self.client.collection.num_entities}")
        logger.info(f"Unique correlation_ids: {total_to_keep}")
        logger.info(f"Duplicate chunks to DELETE: {total_to_delete}")
        logger.info(f"Chunks to KEEP: {total_to_keep}")
        logger.info(f"Collection size after cleanup: {total_to_keep}")
        logger.info("")
        logger.info(f"Space savings: {total_to_delete} chunks ({total_to_delete / (total_to_keep + total_to_delete) * 100:.1f}% reduction)")
        logger.info("=" * 80)

    def delete_duplicates(self, duplicates_map: Dict[str, List[Dict]]) -> int:
        """
        Delete duplicate chunks from Milvus.

        Args:
            duplicates_map: Map of correlation_id to duplicate chunks

        Returns:
            Number of chunks deleted
        """
        logger.info("Deleting duplicate chunks...")

        total_deleted = 0
        batch_size = 1000

        # Collect all primary keys to delete
        primary_keys_to_delete = []

        for correlation_id, duplicate_chunks in duplicates_map.items():
            for chunk in duplicate_chunks:
                primary_key = chunk.get("_primary_key")
                if primary_key:
                    primary_keys_to_delete.append(primary_key)

        logger.info(f"Collected {len(primary_keys_to_delete)} primary keys to delete")

        # Determine primary key field name
        schema = self.client.collection.schema
        primary_field_name = None
        for field in schema.fields:
            if field.is_primary:
                primary_field_name = field.name
                break

        if not primary_field_name:
            logger.error("Could not determine primary key field name")
            return 0

        logger.info(f"Primary key field: {primary_field_name}")

        # Delete in batches
        for i in range(0, len(primary_keys_to_delete), batch_size):
            batch = primary_keys_to_delete[i:i + batch_size]

            # Build delete expression with proper Milvus syntax
            # For VARCHAR primary keys, need to quote each value
            quoted_keys = [f'"{key}"' for key in batch]
            keys_str = ", ".join(quoted_keys)
            expr = f"{primary_field_name} in [{keys_str}]"

            try:
                logger.debug(f"Delete expression: {expr[:200]}...")  # Log first 200 chars
                self.client.collection.delete(expr)
                total_deleted += len(batch)
                logger.info(f"Deleted batch {i // batch_size + 1}: {len(batch)} chunks (total: {total_deleted})")
            except Exception as e:
                logger.error(f"Error deleting batch: {e}")
                logger.error(f"Expression that failed: {expr[:500]}")
                continue

        # Flush to ensure deletions are persisted
        self.client.collection.flush()
        logger.info(f"✅ Deleted {total_deleted} duplicate chunks")

        return total_deleted

    def cleanup(self):
        """Run the complete cleanup process."""
        try:
            # Step 1: Fetch all chunks
            all_chunks = self.get_all_chunks()

            if not all_chunks:
                logger.warning("No chunks found in collection")
                return

            # Step 2: Find duplicates
            duplicates_map, keep_map = self.find_duplicates(all_chunks)

            if not duplicates_map:
                logger.info("✅ No duplicates found! Collection is clean.")
                return

            # Step 3: Preview
            self.preview_cleanup(duplicates_map, keep_map)

            if self.dry_run:
                logger.info("\n" + "=" * 80)
                logger.info("DRY RUN MODE - No changes made")
                logger.info("=" * 80)
                logger.info("To perform actual cleanup, run with: --no-dry-run")
                return

            # Step 4: Confirm deletion
            logger.info("\n" + "=" * 80)
            logger.info("⚠️  WARNING: About to delete duplicate chunks")
            logger.info("=" * 80)
            response = input("Are you sure you want to proceed? (type 'yes' to confirm): ")

            if response.lower() != 'yes':
                logger.info("Cleanup cancelled by user")
                return

            # Step 5: Delete duplicates
            deleted_count = self.delete_duplicates(duplicates_map)

            # Step 6: Verify
            final_count = self.client.get_collection_count()

            logger.info("\n" + "=" * 80)
            logger.info("CLEANUP COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Deleted: {deleted_count} duplicate chunks")
            logger.info(f"Final collection size: {final_count} chunks")
            logger.info(f"Expected size: {len(keep_map)} chunks")

            if final_count == len(keep_map):
                logger.info("✅ Cleanup successful - collection size matches expected!")
            else:
                logger.warning(f"⚠️  Size mismatch - expected {len(keep_map)}, got {final_count}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
            raise

        finally:
            # Close connection
            self.client.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clean up duplicate chunks in Milvus collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (preview only)
    python cleanup_duplicates.py --collection-name "my_collection" --dry-run

    # Actual cleanup
    python cleanup_duplicates.py --collection-name "my_collection" --no-dry-run

    # Specify vector dimension
    python cleanup_duplicates.py --collection-name "my_collection" --vector-dimension 768
        """
    )

    parser.add_argument(
        "--collection-name",
        required=True,
        help="Name of the Milvus collection to clean up"
    )

    parser.add_argument(
        "--vector-dimension",
        type=int,
        default=1536,
        help="Dimension of embedding vectors (default: 1536 for OpenAI)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without deleting (default: True)"
    )

    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Actually delete duplicates (use with caution!)"
    )

    args = parser.parse_args()

    # Run cleanup
    cleanup = DuplicateCleanup(
        collection_name=args.collection_name,
        vector_dimension=args.vector_dimension,
        dry_run=args.dry_run
    )

    cleanup.cleanup()


if __name__ == "__main__":
    main()
