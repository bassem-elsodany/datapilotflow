"""
Long-term Memory Deletion Tool for SkillPilot System

This module provides a CLI tool for deleting MongoDB collections used for long-term memory.
It enables safe cleanup of memory data when needed.

Features:
    - Safe collection deletion with existence checking
    - Configurable MongoDB connection parameters
    - Comprehensive logging of deletion operations
    - Connection cleanup after operations

Usage:
    python -m tools.core.delete_long_term_memory --collection-name "long_term_memory"

Author: SkillPilot Team
Version: 2.0.0
"""

import click
from loguru import logger
from pymongo import MongoClient
from pymongo.database import Database

from config import settings


@click.command()
@click.option(
    "--collection-name",
    "-c",
    default=settings.MONGO_LONG_TERM_MEMORY_COLLECTION,
    help="Name of the collection to delete",
)
@click.option(
    "--mongo-uri",
    "-u",
    default=settings.MONGO_CONN_STR,
    help="MongoDB connection URI",
)
@click.option(
    "--db-name",
    "-d",
    default=settings.MONGO_DB_NAME,
    help="Name of the database",
)
def main(collection_name: str, mongo_uri: str, db_name: str) -> None:
    """Command line interface to delete a MongoDB collection.

    Args:
        collection_name: Name of the collection to delete.
        mongo_uri: The MongoDB connection URI string.
        db_name: The name of the database containing the collection.
    """
    # Create MongoDB client
    client = MongoClient(mongo_uri)

    # Get database
    db: Database = client[db_name]

    # Delete collection if it exists
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        logger.info(f"Successfully deleted '{collection_name}' collection.")
    else:
        logger.info(f"'{collection_name}' collection does not exist.")

    # Close the connection
    client.close()


if __name__ == "__main__":
    main()
