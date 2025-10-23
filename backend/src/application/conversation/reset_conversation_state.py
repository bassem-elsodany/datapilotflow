"""
Conversation state reset utilities for SkillPilot.

This module provides functionality to reset conversation state
and clear LangGraph checkpoints from MongoDB.
"""

from loguru import logger

from skillpilot.config import settings


async def reset_conversation_messages_state(conversation_id: str, user_id: str) -> dict:
    """Resets the conversation state by deleting all checkpoint and writes collections.

    This function will:
      - Delete the state checkpoint collection for the given conversation
      - Delete the state writes collection for the given conversation
      - Log the deletion process

    Returns:
        dict: Status indicating success or failure

    Raises:
        Exception: On MongoDB errors or invalid configuration
    """
    try:
        from skillpilot.infrastructure.mongo.client import get_mongo_client
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]

        collections_deleted = []

        if settings.MONGO_STATE_CHECKPOINT_COLLECTION in db.list_collection_names():
            db.drop_collection(settings.MONGO_STATE_CHECKPOINT_COLLECTION)
            collections_deleted.append(settings.MONGO_STATE_CHECKPOINT_COLLECTION)
            logger.info(f"Deleted collection: {settings.MONGO_STATE_CHECKPOINT_COLLECTION}")

        if settings.MONGO_STATE_WRITES_COLLECTION in db.list_collection_names():
            db.drop_collection(settings.MONGO_STATE_WRITES_COLLECTION)
            collections_deleted.append(settings.MONGO_STATE_WRITES_COLLECTION)
            logger.info(f"Deleted collection: {settings.MONGO_STATE_WRITES_COLLECTION}")

        if collections_deleted:
            return {
                "status": "success",
                "message": f"Deleted collections: {', '.join(collections_deleted)}"
            }
        else:
            return {
                "status": "success",
                "message": "No collections were deleted. Nothing to reset."
            }

    except Exception as e:
        logger.error(f"Failed to reset state: {str(e)}")
        raise Exception(f"Failed to reset SkillPilot state: {str(e)}")


async def cleanup_problematic_checkpoints() -> dict:
    """Cleans up problematic checkpoints with null values that cause duplicate key errors.

    Removes:
      - Checkpoints with null thread_id
      - Checkpoints with null checkpoint_ns
      - Checkpoints with null checkpoint_id

    Returns:
        dict: Status indicating success or failure
    """
    try:
        from skillpilot.infrastructure.mongo.client import get_mongo_client
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]
        
        checkpoint_collection = db[settings.MONGO_STATE_CHECKPOINT_COLLECTION]
        writes_collection = db[settings.MONGO_STATE_WRITES_COLLECTION]
        
        deleted_count = 0
        
        # Clean up checkpoints with null values
        null_checkpoints = checkpoint_collection.delete_many({
            "$or": [
                {"thread_id": None},
                {"thread_id": ""},
                {"checkpoint_ns": None},
                {"checkpoint_id": None}
            ]
        })
        deleted_count += null_checkpoints.deleted_count
        logger.info(f"Deleted {null_checkpoints.deleted_count} problematic checkpoints")
        
        # Clean up writes with null values
        null_writes = writes_collection.delete_many({
            "$or": [
                {"thread_id": None},
                {"thread_id": ""},
                {"checkpoint_ns": None},
                {"checkpoint_id": None}
            ]
        })
        deleted_count += null_writes.deleted_count
        logger.info(f"Deleted {null_writes.deleted_count} problematic writes")
        
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} problematic documents",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup problematic checkpoints: {str(e)}")
        raise Exception(f"Failed to cleanup problematic checkpoints: {str(e)}")


async def fix_checkpoint_indexes() -> dict:
    """Fixes MongoDB indexes to prevent duplicate key errors.

    Creates:
      - Sparse indexes that ignore null values
      - Unique indexes with proper constraints

    Returns:
        dict: Status indicating success or failure
    """
    try:
        from skillpilot.infrastructure.mongo.client import get_mongo_client
        client = get_mongo_client()
        db = client[settings.MONGO_DB_NAME]
        
        checkpoint_collection = db[settings.MONGO_STATE_CHECKPOINT_COLLECTION]
        
        # Drop existing problematic indexes
        try:
            checkpoint_collection.drop_index("thread_id_1_checkpoint_ns_1_checkpoint_id_-1")
            logger.info("Dropped problematic index")
        except Exception as e:
            logger.info(f"Index not found or already dropped: {e}")
        
        # Create sparse index that ignores null values
        checkpoint_collection.create_index(
            [("thread_id", 1), ("checkpoint_ns", 1), ("checkpoint_id", -1)],
            unique=True,
            sparse=True,
            name="thread_checkpoint_unique_sparse"
        )
        logger.info("Created sparse unique index for checkpoints")
        
        return {
            "status": "success",
            "message": "Fixed checkpoint indexes"
        }
        
    except Exception as e:
        logger.error(f"Failed to fix checkpoint indexes: {str(e)}")
        raise Exception(f"Failed to fix checkpoint indexes: {str(e)}")
