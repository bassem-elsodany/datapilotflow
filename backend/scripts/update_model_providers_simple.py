#!/usr/bin/env python
"""
Simplified Model Provider Update Script - Direct MongoDB Updates

This script directly updates MongoDB without importing the full app stack.
Useful when some dependencies are not available.

Usage:
    python scripts/update_model_providers_simple.py
"""

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger
from pymongo import MongoClient

# Get latest models directly (no imports needed)
LATEST_MODELS = {
    "OpenAI": {
        "embedding": {
            "models": [
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            "config": {
                "endpoint_suffix": "/embeddings",
                "max_input_tokens": 8191,
                "batch_size": 100,
            },
        },
        "generative": {
            "models": [
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-5-chat-latest",
                "gpt-4o",
                "gpt-4o-2024-11-20",
                "gpt-4o-2024-08-06",
                "gpt-4o-mini",
                "gpt-4o-mini-2024-07-18",
                "gpt-4-turbo",
                "gpt-4-turbo-2024-04-09",
                "gpt-4",
                "gpt-4-32k",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
            ],
            "config": {
                "endpoint_suffix": "/chat/completions",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            },
        },
    },
    "Anthropic": {
        "embedding": {
            "models": [
                "claude-3-5-sonnet-embedding",
                "claude-3-opus-embedding",
                "claude-3-sonnet-embedding",
            ],
            "config": {
                "endpoint_suffix": "/embeddings",
                "max_input_tokens": 8192,
                "batch_size": 50,
            },
        },
        "generative": {
            "models": [
                "claude-opus-4-1-20250805",
                "claude-4-sonnet-20250514",
                "claude-4-opus-20250514",
                "claude-4-haiku-20250514",
                "claude-sonnet-4-20250514",
                "claude-haiku-4-5-20241119",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2",
                "claude-instant-1.2",
            ],
            "config": {
                "endpoint_suffix": "/messages",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
            },
        },
    },
    "Google": {
        "embedding": {
            "models": ["text-embedding-004", "text-multilingual-embedding-002"],
            "config": {
                "endpoint_suffix": "/models",
                "max_input_tokens": 2048,
                "batch_size": 100,
            },
        },
        "generative": {
            "models": [
                "gemini-2-5-pro",
                "gemini-2-5-flash",
                "gemini-2-5-flash-lite",
                "gemini-2.0-flash",
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-pro-002",
                "gemini-1.5-flash",
                "gemini-1.5-flash-002",
                "gemini-1.0-pro",
                "gemini-1.0-pro-vision",
            ],
            "config": {
                "endpoint_suffix": "/models",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
            },
        },
    },
    "Groq": {
        "generative": {
            "models": [
                "llama-4-8b",
                "llama-4-70b",
                "llama-4-405b",
                "llama-3-3-70b-versatile",
                "llama-3-3-70b-specdec",
                "llama-3-1-70b-versatile",
                "llama-3-1-8b-instant",
                "llama-3-2-90b-vision-preview",
                "llama-3-2-11b-vision-preview",
                "llama-3-2-1b-preview",
                "mixtral-8x7b-32768",
                "gemma-7b-it",
                "gemma-2-9b-it",
                "deepseek-r1-distill-qwen-32b",
                "qwen-qwq-32b",
                "qwen-2-5-coder-32b",
                "qwen-2-5-32b",
                "mistral-saba-24b",
            ],
            "config": {
                "endpoint_suffix": "/chat/completions",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
            },
        },
    },
    "Cohere": {
        "embedding": {
            "models": [
                "embed-english-v3.0",
                "embed-english-light-v3.0",
                "embed-multilingual-v3.0",
                "embed-multilingual-light-v3.0",
            ],
            "config": {
                "endpoint_suffix": "/embed",
                "max_input_tokens": 512,
                "batch_size": 96,
            },
        },
        "generative": {
            "models": [
                "command-a-03-2025",
                "command-a-reasoning-03-2025",
                "command-a-translate-03-2025",
                "command-r-plus-08-2024",
                "command-r-plus",
                "command-r-08-2024",
                "command-r",
                "command-nightly",
                "command",
                "command-light",
                "command-light-nightly",
            ],
            "config": {
                "endpoint_suffix": "/generate",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
            },
        },
        "reranker": {
            "models": [
                "rerank-english-v3.0",
                "rerank-multilingual-v3.0",
                "rerank-english-v2.0",
                "rerank-multilingual-v2.0",
            ],
            "config": {
                "endpoint_suffix": "/rerank",
                "max_documents": 1000,
                "top_n": 10,
            },
        },
    },
    "Ollama": {
        "embedding": {
            "models": [
                "nomic-embed-text",
                "mxbai-embed-large",
                "all-minilm",
                "bge-large-en",
                "bge-base-en",
            ],
            "config": {
                "endpoint_suffix": "/embeddings",
                "max_input_tokens": 8192,
                "batch_size": 10,
            },
        },
        "generative": {
            "models": [
                "llama3.3:70b",
                "llama3.2:90b",
                "llama3.2:11b",
                "llama3.2:3b",
                "llama3.2-vision:90b",
                "llama3.2-vision:11b",
                "llama3.1:405b",
                "llama3.1:70b",
                "llama3.1:8b",
                "llama3:70b",
                "llama3:8b",
                "mistral:7b",
                "mistral-large:latest",
                "mixtral:8x7b",
                "codellama:34b",
                "codellama:13b",
                "codellama:7b",
                "phi3:3.8b",
                "phi3:14b",
                "phi4:14b",
                "neural-chat:7b",
                "deepseek-coder:33b",
                "deepseek-coder:6.7b",
            ],
            "config": {
                "endpoint_suffix": "/generate",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
            },
        },
    },
    "Hugging Face": {
        "embedding": {
            "models": [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "sentence-transformers/distilbert-base-nli-mean-tokens",
            ],
            "config": {
                "endpoint_suffix": "/",
                "max_input_tokens": 512,
                "batch_size": 50,
            },
        },
        "generative": {
            "models": [
                "meta-llama/Llama-3.3-70B-Instruct",
                "meta-llama/Llama-3.1-70B-Instruct",
                "meta-llama/Llama-3.1-8B-Instruct",
                "meta-llama/Llama-2-70b-chat-hf",
                "meta-llama/Llama-2-13b-chat-hf",
                "meta-llama/Llama-2-7b-chat-hf",
                "mistralai/Mistral-Large-Instruct-2411",
                "mistralai/Mistral-7B-Instruct-v0.3",
                "mistralai/Mistral-7B-Instruct-v0.2",
                "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
                "NousResearch/Nous-Hermes-2-7b-DPO",
                "google/flan-t5-xxl",
                "google/flan-t5-large",
                "google/flan-t5-base",
                "deepseek-ai/deepseek-coder-33b-instruct",
                "deepseek-ai/deepseek-coder-7b-instruct",
                "Qwen/Qwen2.5-72B-Instruct",
                "Qwen/Qwen2.5-32B-Instruct",
                "Qwen/Qwen2.5-7B-Instruct",
                "stabilityai/stablelm-2-zephyr-1.6b",
            ],
            "config": {
                "endpoint_suffix": "/",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 1.0,
            },
        },
    },
    "Voyage AI": {
        "embedding": {
            "models": [
                "voyage-large-2",
                "voyage-code-2",
                "voyage-2",
                "voyage-lite-02-instruct",
            ],
            "config": {
                "endpoint_suffix": "/embeddings",
                "max_input_tokens": 8000,
                "batch_size": 128,
            },
        },
        "reranker": {
            "models": ["rerank-lite-1", "rerank-1"],
            "config": {
                "endpoint_suffix": "/rerank",
                "max_documents": 1000,
                "top_n": 10,
            },
        },
    },
}


def get_mongo_client():
    """Get MongoDB client connection."""
    import os

    host = os.getenv("MONGO_HOST", "localhost")
    port = int(os.getenv("MONGO_PORT", 27017))
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASS")
    db_name = os.getenv("MONGO_DB", "datapilotflow")

    if user and password:
        uri = f"mongodb://{user}:{password}@{host}:{port}/{db_name}?authSource=admin"
    else:
        uri = f"mongodb://{host}:{port}/{db_name}"

    logger.info(f"Connecting to MongoDB at {host}:{port}")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    # Test connection
    try:
        client.admin.command("ping")
        logger.info("✅ MongoDB connection successful")
        return client
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


def update_model_providers():
    """Update all model providers in MongoDB."""
    logger.info("=" * 100)
    logger.info("🚀 STARTING SIMPLIFIED MODEL PROVIDER UPDATE")
    logger.info("=" * 100)

    try:
        client = get_mongo_client()
        db = client[
            "datapilotflow"
        ]  # Get the database name from env or default
        providers_collection = db["model_providers"]

        updated_count = 0
        skipped_count = 0
        error_count = 0

        logger.info(f"📋 Found {len(LATEST_MODELS)} providers to update")

        for provider_name, model_config in LATEST_MODELS.items():
            logger.info("")
            logger.info("=" * 100)
            logger.info(f"📦 UPDATING PROVIDER: {provider_name}")
            logger.info("=" * 100)

            try:
                # Find existing provider by name
                existing = providers_collection.find_one({"name": provider_name})

                if not existing:
                    logger.warning(
                        f"⏭️  Provider '{provider_name}' not found in database, skipping"
                    )
                    skipped_count += 1
                    continue

                logger.info(f"✅ Found existing provider: {existing.get('_id')}")

                # Build update dict
                update_data = {
                    "updated_at": datetime.utcnow(),
                    "updated_by": "admin",
                }

                # Update each model type
                for model_type, config in model_config.items():
                    update_data[model_type] = config
                    model_count = len(config.get("models", []))
                    logger.info(
                        f"   {'📊' if model_type == 'embedding' else '🧠' if model_type == 'generative' else '🔍'} {model_type.capitalize()}: {model_count} models"
                    )

                # Update in MongoDB
                result = providers_collection.update_one(
                    {"_id": existing["_id"]}, {"$set": update_data}
                )

                if result.modified_count > 0:
                    logger.info(f"✅✅✅ SUCCESSFULLY UPDATED: {provider_name}")
                    logger.info(f"   ID: {existing['_id']}")
                    logger.info(f"   Updated at: {update_data['updated_at']}")
                    updated_count += 1
                else:
                    logger.warning(f"⚠️  No changes made for: {provider_name}")
                    skipped_count += 1

            except Exception as e:
                logger.error(f"❌ Error updating provider '{provider_name}': {e}")
                error_count += 1
                continue

        # Summary
        logger.info("")
        logger.info("=" * 100)
        logger.info("📊 UPDATE SUMMARY")
        logger.info("=" * 100)
        logger.info(f"✅ Successfully updated: {updated_count} providers")
        logger.info(f"⏭️  Skipped: {skipped_count} providers")
        logger.info(f"❌ Errors: {error_count} providers")
        logger.info("=" * 100)

        if error_count == 0 and updated_count > 0:
            logger.info("🎉 ALL PROVIDERS UPDATED SUCCESSFULLY!")
            return True
        elif updated_count > 0:
            logger.warning(f"⚠️  {error_count} providers had errors, but some were updated")
            return True
        else:
            logger.error("❌ NO PROVIDERS WERE UPDATED")
            return False

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = update_model_providers()
    sys.exit(0 if success else 1)
