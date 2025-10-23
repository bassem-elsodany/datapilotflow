"""
Knowledge Source Configuration API Router.

This router provides REST endpoints for managing knowledge source configurations
and knowledge processing jobs.
"""

import uuid
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.routers.auth.auth_router import get_current_user
from src.domain.knowledge.knowledge_job import (
    JobStatus,
    KnowledgeJob,
    KnowledgeJobCreate,
)
from src.domain.knowledge.knowledge_source_config import (
    KnowledgeSourceConfig,
    KnowledgeSourceConfigCreate,
    KnowledgeSourceConfigExpanded,
    KnowledgeSourceConfigUpdate,
    UrlSourceConfig,
)
from src.domain.knowledge.llm_content_filter_config import LLMContentFilterConfig
from src.domain.user import User
from src.services.knowledge.knowledge_job_service import (
    KnowledgeJobService,
    get_knowledge_job_service,
)
from src.services.knowledge.knowledge_source_service import (
    KnowledgeSourceService,
    get_knowledge_source_service,
)
from src.services.knowledge.llm_content_filter_service import (
    get_llm_content_filter_service,
)

router = APIRouter()


@router.post(
    "/", response_model=KnowledgeSourceConfig, status_code=status.HTTP_201_CREATED
)
async def create_knowledge_source_config(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """
    Create a new knowledge source configuration.

    Supports both:
    - JSON payload (web scraping): Content-Type: application/json
    - FormData with files (local files): Content-Type: multipart/form-data
    """
    import json
    from datetime import datetime

    try:
        content_type = request.headers.get("content-type", "")

        # Handle multipart/form-data (file uploads)
        if "multipart/form-data" in content_type:
            form = await request.form()

            # Parse config from JSON string
            config_data_json = form.get("config_data_json")
            if not config_data_json:
                raise HTTPException(
                    status_code=400,
                    detail="config_data_json field required in FormData",
                )

            try:
                config_dict = json.loads(config_data_json)
                config_create = KnowledgeSourceConfigCreate(**config_dict)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

            # Extract uploaded files
            files = form.getlist("files")

        # Handle application/json (no files)
        elif "application/json" in content_type:
            body = await request.json()
            config_create = KnowledgeSourceConfigCreate(**body)
            files = []

        else:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json or multipart/form-data",
            )

        # For local_files with FormData, set file_types based on uploaded files
        if (
            config_create.content_source_type == "local_files"
            and files
            and len(files) > 0
        ):
            # Set file_types based on the uploaded files
            file_types = list(
                set(file.filename.split(".")[-1].lower() for file in files)
            )
            config_create.file_types = file_types

        # Create the config first to get the ID
        config = service.create_knowledge_source_config(config_create, current_user.id)

        # Handle file uploads if files are provided
        if files and len(files) > 0:
            # Create inbound directory for this config
            inbound_dir = Path("upload") / "inbound" / config.id
            inbound_dir.mkdir(parents=True, exist_ok=True)

            # Upload and save files
            uploaded_files = []
            for file in files:
                # Keep original filename (sanitized for filesystem)
                original_filename = file.filename
                # Sanitize filename: replace unsafe chars but keep original name
                safe_filename = original_filename.replace("/", "_").replace("\\", "_").replace("..", "_")
                file_path = inbound_dir / safe_filename

                # Save file asynchronously
                async with aiofiles.open(file_path, "wb") as f:
                    content = await file.read()
                    await f.write(content)

                # Get file info
                file_size = file_path.stat().st_size
                file_ext = Path(safe_filename).suffix
                file_type = file_ext.lstrip(".").lower()

                uploaded_files.append(
                    {
                        "file_id": str(uuid.uuid4()),
                        "original_filename": file.filename,
                        "file_path": str(file_path),
                        "file_type": file_type,
                        "file_size": file_size,
                        "upload_timestamp": datetime.utcnow().isoformat(),
                    }
                )

                logger.info(
                    f"Uploaded file '{file.filename}' to '{file_path}' "
                    f"for config_id={config.id}, size={file_size} bytes"
                )

            # Update the config with file paths
            updated_config = service.update_knowledge_source_config(
                config.id,
                current_user.id,
                KnowledgeSourceConfigUpdate(local_files=uploaded_files),
            )

            logger.info(
                f"Created config '{config.name}' with {len(uploaded_files)} uploaded files"
            )

            return updated_config if updated_config else config

        return config

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/", response_model=List[KnowledgeSourceConfig])
def list_knowledge_source_configs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    content_source_type: Optional[str] = Query(
        None, description="Filter by content source type"
    ),
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """List knowledge source configurations for the current user."""
    try:
        configs = service.list_knowledge_source_configs(
            current_user.id, skip, limit, content_source_type
        )
        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{config_id}", response_model=KnowledgeSourceConfigExpanded)
def get_knowledge_source_config(
    config_id: str,
    expand: Optional[str] = Query(
        None,
        description="Comma-separated list of related data to expand (content_filter,model_provider,url_source)",
    ),
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """Get a specific knowledge source configuration with optional expanded related data."""
    try:
        # Parse expand parameter
        expand_list = []
        if expand:
            expand_list = [item.strip() for item in expand.split(",") if item.strip()]

        config = service.get_knowledge_source_config_expanded(
            config_id, current_user.id, expand
        )
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/{config_id}", response_model=KnowledgeSourceConfig)
async def update_knowledge_source_config(
    config_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """Update a knowledge source configuration."""
    import json
    import os
    from datetime import datetime
    from pathlib import Path

    import aiofiles

    try:
        logger.info(f"🔍 [ROUTER] Received PUT request for config {config_id}")

        # Get existing config to access its folder
        existing_config = service.get_knowledge_source_config(
            config_id, current_user.id
        )
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )

        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            # Handle file upload
            form = await request.form()
            config_data_json = form.get("config_data_json")
            if not config_data_json:
                raise HTTPException(
                    status_code=400,
                    detail="config_data_json field required in FormData",
                )

            try:
                config_dict = json.loads(config_data_json)
                update_data = KnowledgeSourceConfigUpdate(**config_dict)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

            # Get the list of files to keep from the update_data
            existing_files = update_data.local_files or []

            # Get new uploaded files
            new_files = form.getlist("files")

            # Use the existing config's inbound folder
            inbound_dir = Path("upload/inbound") / config_id
            inbound_dir.mkdir(parents=True, exist_ok=True)

            # Collect existing file paths that should be kept
            existing_file_paths = {
                Path(f["file_path"]) for f in existing_files if "file_path" in f
            }

            # Remove old files that are no longer in the configuration
            if inbound_dir.exists():
                for file_path in inbound_dir.iterdir():
                    if file_path.is_file() and file_path not in existing_file_paths:
                        logger.info(f"🗑️ Removing old file: {file_path}")
                        file_path.unlink()

            # Upload new files
            uploaded_files = []
            for file in new_files:
                # Keep original filename (sanitized for filesystem)
                original_filename = file.filename
                # Sanitize filename: replace unsafe chars but keep original name
                safe_filename = original_filename.replace("/", "_").replace("\\", "_").replace("..", "_")
                file_path = inbound_dir / safe_filename

                # Save file asynchronously
                async with aiofiles.open(file_path, "wb") as f:
                    content = await file.read()
                    await f.write(content)

                # Get file info
                file_size = file_path.stat().st_size
                file_ext = Path(safe_filename).suffix
                file_type = file_ext.lstrip(".").lower()

                uploaded_files.append(
                    {
                        "file_id": str(uuid.uuid4()),
                        "original_filename": file.filename,
                        "file_path": str(file_path),
                        "file_type": file_type,
                        "file_size": file_size,
                        "upload_timestamp": datetime.utcnow().isoformat(),
                    }
                )

                logger.info(
                    f"📤 Uploaded new file '{file.filename}' to '{file_path}' "
                    f"for config_id={config_id}, size={file_size} bytes"
                )

            # Combine existing files with newly uploaded files
            all_files = existing_files + uploaded_files
            update_data.local_files = all_files

            logger.info(
                f"📁 Total files after update: {len(all_files)} "
                f"(kept: {len(existing_files)}, new: {len(uploaded_files)})"
            )

        elif "application/json" in content_type:
            # Handle JSON update (no file changes)
            body = await request.json()
            update_data = KnowledgeSourceConfigUpdate(**body)
        else:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json or multipart/form-data",
            )

        logger.debug(f"🔍 [ROUTER] Update data: {update_data.model_dump()}")

        if update_data.url_source and update_data.scraping_mode == "multiple_pages":
            logger.info(
                f"🔍 [ROUTER] URL source present for multiple_pages mode: {len(update_data.url_source.urls)} URLs"
            )

        config = service.update_knowledge_source_config(
            config_id, current_user.id, update_data
        )
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating config {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_source_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """Delete a knowledge source configuration."""
    try:
        deleted = service.delete_knowledge_source_config(config_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    except ValueError as e:
        # Dependency conflict (existing jobs)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/{config_id}/jobs",
    response_model=KnowledgeJob,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_job(
    config_id: str,
    job_data: KnowledgeJobCreate,
    current_user: User = Depends(get_current_user),
    service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """Create a new knowledge processing job from a configuration."""
    try:
        job = service.create_knowledge_job(config_id, current_user.id, job_data)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )
        return job
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{config_id}/jobs", response_model=List[KnowledgeJob])
def list_knowledge_jobs_for_config(
    config_id: str,
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    current_user: User = Depends(get_current_user),
    config_service: KnowledgeSourceService = Depends(get_knowledge_source_service),
    job_service: KnowledgeJobService = Depends(get_knowledge_job_service),
):
    """List knowledge processing jobs for a specific configuration."""
    try:
        # Verify the configuration exists and belongs to the user
        config = config_service.get_knowledge_source_config(config_id, current_user.id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )

        jobs = job_service.list_knowledge_jobs(
            current_user.id, config_id, status, skip, limit
        )
        return jobs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{config_id}/url-sources/{url_source_id}", response_model=UrlSourceConfig)
def get_url_source_config(
    config_id: str,
    url_source_id: str,
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """Get a specific URL source configuration for a knowledge source config."""
    try:
        # Verify the config belongs to the user
        config = service.get_knowledge_source_config(config_id, current_user.id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source configuration not found",
            )

        # Verify the URL source belongs to this config
        if config.url_source_id != url_source_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL source does not belong to this configuration",
            )

        url_source = service.get_url_source_config(url_source_id, current_user.id)
        if not url_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL source configuration not found",
            )
        return url_source
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{config_id}/content-filter", response_model=Optional[LLMContentFilterConfig]
)
def get_source_content_filter(
    config_id: str,
    current_user: User = Depends(get_current_user),
    source_service: KnowledgeSourceService = Depends(get_knowledge_source_service),
    filter_service=Depends(get_llm_content_filter_service),
):
    """Get the LLM content filter configuration associated with a knowledge source config.

    This is the primary endpoint used by the crawler/processor to retrieve
    the filter configuration when processing a source.

    Returns:
        - LLM content filter configuration if source has one configured
        - null if source has no filter configured

    Raises:
        - 404: Source config not found
        - 404: Source has filter_id but filter config not found (orphaned reference)
    """
    try:
        logger.debug(f"Getting content filter for source config {config_id}")

        # Get the source configuration
        source_config = source_service.get_knowledge_source_config(
            config_id, current_user.id
        )

        if not source_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge source configuration not found: {config_id}",
            )

        # Check if source has a content filter configured
        if not source_config.llm_content_filter_id:
            logger.debug(f"Source config {config_id} has no content filter configured")
            return None

        # Get the content filter configuration
        filter_config = filter_service.get_config(
            source_config.llm_content_filter_id, current_user.id
        )

        if not filter_config:
            logger.warning(
                f"Source config {config_id} references filter {source_config.llm_content_filter_id} but it was not found"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content filter configuration not found: {source_config.llm_content_filter_id}",
            )

        logger.debug(
            f"Retrieved content filter '{filter_config.name}' for source config {config_id}"
        )
        return filter_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving content filter for source config {config_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve content filter for source config: {str(e)}",
        )
