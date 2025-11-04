# Model Provider Update Script

This directory contains scripts to update model providers in the database with the latest available models.

## Overview

The `update_model_providers.py` script reads the predefined model configurations from `ModelProviderInitializationService` and updates the corresponding providers in the database.

**What gets updated:**
- ✅ Embedding model lists
- ✅ Generative model lists
- ✅ Reranker model lists
- ✅ Model configuration for each type
- ✅ Updated timestamp and user tracking

## Prerequisites

1. **Database Running**: Ensure your MongoDB is running and accessible
2. **Environment Setup**: Set up environment variables if needed:
   ```bash
   export MONGO_HOST=localhost
   export MONGO_PORT=27017
   export MONGO_DB=datapilotflow
   ```

3. **Virtual Environment**: Activate your Python virtual environment
   ```bash
   source .venv/bin/activate
   ```

## Usage

### Option 1: Run Shell Script (Recommended)
```bash
cd backend
bash scripts/run_update_models.sh
```

### Option 2: Run Python Script Directly
```bash
cd backend
python scripts/update_model_providers.py
```

## What Happens

The script performs the following steps:

1. **Reads** predefined providers from `ModelProviderInitializationService`
2. **Finds** existing providers in the database by name
3. **Updates** each provider with:
   - Latest model lists for each model type
   - Updated configuration for each model type
   - Timestamp and user tracking
4. **Reports** summary of updates

## Expected Output

```
====================================================================================================
🚀 STARTING MODEL PROVIDER UPDATE SCRIPT
====================================================================================================
📋 Found 8 predefined providers to update

====================================================================================================
📦 UPDATING PROVIDER: OpenAI
====================================================================================================
✅ Found existing provider: {provider_id}
   📊 Embedding: 3 models
   🧠 Generative: 15 models
✅✅✅ SUCCESSFULLY UPDATED: OpenAI
   ID: {provider_id}
   Updated at: 2025-11-04 10:30:45.123456
   📊 Embedding models: 3
   🧠 Generative models: 15

[... more providers ...]

====================================================================================================
📊 UPDATE SUMMARY
====================================================================================================
✅ Successfully updated: 8 providers
⏭️  Skipped: 0 providers
❌ Errors: 0 providers
====================================================================================================
🎉 ALL PROVIDERS UPDATED SUCCESSFULLY!
```

## Providers Updated

When you run this script, it updates:

1. **OpenAI** - 15 generative models including GPT-5, GPT-4o, GPT-4
2. **Anthropic** - 15 generative models including Claude 4, Claude Opus 4.1, Sonnet 4.5
3. **Google** - 11 generative models including Gemini 2.5, Gemini 2.0
4. **Ollama** - 23 generative models including Llama 3.3, 3.2 Vision, Phi4
5. **Hugging Face** - 21 generative models including Llama 3.3, Mistral, Qwen 2.5
6. **Groq** - 18 generative models including Llama 4, Llama 3.3
7. **Cohere** - 11 generative models including Command A series
8. **Voyage AI** - Embedding and Reranker models (no generative)

## Troubleshooting

### Issue: "Provider not found in database"
**Solution**: This is normal if the provider hasn't been created yet. You need to:
1. Run the initialization script first: `python scripts/initialize_system.py`
2. Then run the update script: `bash scripts/run_update_models.sh`

### Issue: "Connection refused" error
**Solution**: Ensure MongoDB is running:
```bash
# Check if MongoDB is running (macOS with Homebrew)
brew services list | grep mongodb

# Start MongoDB if needed
brew services start mongodb-community

# Or using Docker
docker-compose up -d mongodb
```

### Issue: Environment variables not set
**Solution**: Set them manually or add to `.env`:
```bash
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_DB=datapilotflow
export MONGO_USER=admin
export MONGO_PASS=password
```

## Model Update Frequency

We recommend running this script:
- ✅ **After deployment** - to ensure latest models are available
- ✅ **Quarterly** - to pick up new model releases
- ✅ **When providers release new models** - update immediately

## Latest Models (2025)

This script includes the latest models available as of November 2025:

- **OpenAI**: GPT-5 family (gpt-5, gpt-5-mini, gpt-5-nano)
- **Anthropic**: Claude 4 family + Haiku 4.5
- **Google**: Gemini 2.5 Pro, Flash, Flash-Lite
- **Meta**: Llama 4, Llama 3.3, Llama 3.2 with Vision
- **Cohere**: Command A (111B, 256K context)
- **Qwen**: Qwen 2.5 series (72B, 32B, 7B)
- **DeepSeek**: R1 Distill, Coder series

## Advanced: Manual Update

If you need to add a model not in the predefined list:

```python
from src.services.model_provider.model_provider_service import ModelProviderService
from src.domain.model_provider.model_provider import ModelTypeConfig

service = ModelProviderService()

# Get the provider
provider = service.get_provider_by_name("admin", "OpenAI")

# Update generative models
provider.generative.models.append("gpt-5-new")

# Save changes
service.update_model_provider(provider.id, {"generative": provider.generative}, "admin")
```

## Notes

- The script uses `admin` as the default user ID for updates
- In production, you may want to modify the script to use the actual admin user ID
- All updates are logged to the console for tracking
- The `updated_at` timestamp is automatically set to the current time
