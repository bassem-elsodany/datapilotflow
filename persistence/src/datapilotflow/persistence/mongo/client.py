from datetime import datetime
from typing import Generic, Type, TypeVar

from bson import ObjectId
from loguru import logger
from pydantic import BaseModel
from pymongo import MongoClient, errors

from src.config import settings


T = TypeVar("T", bound=BaseModel)

# Global MongoDB client instance
_mongo_client = None

def get_mongo_client():
    """Get or create a singleton MongoDB client instance."""
    global _mongo_client
    if _mongo_client is None:
        try:
            # Build connection options from settings
            connection_options = {
                "appname": "datapilotflow",
                "maxPoolSize": settings.MONGO_MAX_POOL_SIZE,
                "minPoolSize": settings.MONGO_MIN_POOL_SIZE,
                "maxIdleTimeMS": settings.MONGO_MAX_IDLE_TIME_MS,
                "connectTimeoutMS": settings.MONGO_CONNECT_TIMEOUT_MS,
                "serverSelectionTimeoutMS": settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
            }
            
            # Add authentication if credentials are provided
            if hasattr(settings, 'MONGO_USER') and hasattr(settings, 'MONGO_PASS'):
                if settings.MONGO_USER and settings.MONGO_PASS:
                    connection_options.update({
                        "username": settings.MONGO_USER,
                        "password": settings.MONGO_PASS,
                    })
            
            _mongo_client = MongoClient(settings.MONGO_CONN_STR, **connection_options)
            _mongo_client.admin.command("ping")
            logger.info("Created singleton MongoDB client")
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {e}")
            raise
    return _mongo_client

def close_mongo_client():
    """Close the global MongoDB client instance."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        logger.info("Closed singleton MongoDB client")

class MongoClientWrapper(Generic[T]):
    """
    A wrapper class for MongoDB operations that provides a clean interface
    for CRUD operations on Pydantic models.

    This class handles the connection to MongoDB, document serialization/deserialization,
    and provides methods for common database operations.

    Attributes:
        model (Type[T]): The Pydantic model class to use for document serialization.
        collection_name (str): Name of the MongoDB collection to use.
        database_name (str): Name of the MongoDB database to use.
        mongodb_uri (str): URI for connecting to MongoDB instance.
        client (MongoClient): The MongoDB client instance.
        database (Database): The MongoDB database instance.
        collection (Collection): The MongoDB collection instance.

    Example:
        ```python
        class User(BaseModel):
            name: str
            email: str

        user_service = MongoClientWrapper(User, "users")
        users = user_service.fetch_documents(10, {"name": "John"})
        ```
    """

    def __init__(
        self,
        model: Type[T],
        collection_name: str,
        database_name: str = settings.MONGO_DB_NAME,
        mongodb_uri: str = settings.MONGO_CONN_STR,
    ) -> None:
        """Initialize a connection to the MongoDB collection.

        Args:
            model (Type[T]): The Pydantic model class to use for document serialization.
            collection_name (str): Name of the MongoDB collection to use.
            database_name (str, optional): Name of the MongoDB database to use.
                Defaults to value from settings.
            mongodb_uri (str, optional): URI for connecting to MongoDB instance.
                Defaults to value from settings.

        Raises:
            Exception: If connection to MongoDB fails.
        """

        self.model = model
        self.collection_name = collection_name
        self.database_name = database_name
        self.mongodb_uri = mongodb_uri

        # Use the singleton client
        self.client = get_mongo_client()
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    def __enter__(self) -> "MongoClientWrapper":
        """Enable context manager support.

        Returns:
            MongoDBService: The current instance.
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - no need to close since we use singleton client.

        Args:
            exc_type: Type of exception that occurred, if any.
            exc_val: Exception instance that occurred, if any.
            exc_tb: Traceback of exception that occurred, if any.
        """
        # Don't close the client here since it's a singleton
        pass

    def clear_collection(self) -> None:
        """Remove all documents from the collection.

        This method deletes all documents in the collection to avoid duplicates
        during reingestion.

        Raises:
            errors.PyMongoError: If the deletion operation fails.
        """

        try:
            result = self.collection.delete_many({})
            logger.debug(
                f"Cleared collection. Deleted {result.deleted_count} documents."
            )
        except errors.PyMongoError as e:
            logger.error(f"Error clearing the collection: {e}")
            raise

    def ingest_documents(self, documents: list[T]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            documents: List of Pydantic model instances to insert.

        Raises:
            ValueError: If documents is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """

        try:
            if not documents or not all(
                isinstance(doc, BaseModel) for doc in documents
            ):
                raise ValueError("Documents must be a list of Pycantic models.")

            dict_documents = [doc.model_dump() for doc in documents]

            # Remove '_id' fields to avoid duplicate key errors
            for doc in dict_documents:
                doc.pop("_id", None)

            self.collection.insert_many(dict_documents)
            logger.debug(f"Inserted {len(documents)} documents into MongoDB.")
        except errors.PyMongoError as e:
            logger.error(f"Error inserting documents: {e}")
            raise

    def fetch_documents(self, limit: int, query: dict) -> list[T]:
        """Retrieve documents from the MongoDB collection based on a query.

        Args:
            limit (int): Maximum number of documents to retrieve.
            query (dict): MongoDB query filter to apply.

        Returns:
            list[T]: List of Pydantic model instances matching the query criteria.

        Raises:
            Exception: If the query operation fails.
        """
        try:
            documents = list(self.collection.find(query).limit(limit))
            logger.debug(f"Fetched {len(documents)} documents with query: {query}")
            return self.__parse_documents(documents)
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            raise

    def __parse_documents(self, documents: list[dict]) -> list[T]:
        """Convert MongoDB documents to Pydantic model instances.

        Converts MongoDB ObjectId fields to strings and transforms the document structure
        to match the Pydantic model schema.

        Args:
            documents (list[dict]): List of MongoDB documents to parse.

        Returns:
            list[T]: List of validated Pydantic model instances.
        """
        parsed_documents = []
        for doc in documents:
            parsed_doc = self._parse_single_document(doc)
            parsed_documents.append(parsed_doc)

        return parsed_documents

    def _parse_single_document(self, doc: dict) -> T:
        """Convert a single MongoDB document to a Pydantic model instance.

        Args:
            doc (dict): MongoDB document to parse.

        Returns:
            T: Validated Pydantic model instance.
        """
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, datetime):
                # Convert datetime objects to ISO format strings
                doc[key] = value.isoformat()

        _id = doc.pop("_id", None)
        doc["id"] = _id

        return self.model.model_validate(doc)

    def get_collection_count(self) -> int:
        """Count the total number of documents in the collection.

        Returns:
            Total number of documents in the collection.

        Raises:
            errors.PyMongoError: If the count operation fails.
        """

        try:
            return self.collection.count_documents({})
        except errors.PyMongoError as e:
            logger.error(f"Error counting documents in MongoDB: {e}")
            raise
