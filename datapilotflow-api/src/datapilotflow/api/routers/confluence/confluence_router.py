"""
Confluence API Router.

Provides endpoints for managing Confluence credentials and metadata.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from datapilotflow.api.dependencies import get_current_user
from datapilotflow.domain.user import User
from datapilotflow.services.confluence import (
    ConfluenceCredentialService,
    get_confluence_credential_service,
)


# ==================== Request/Response Models ====================


class ConfluenceCredentialCreate(BaseModel):
    """Request model for creating a Confluence credential."""

    name: str = Field(..., description="Human-readable name for the credential")
    cloud_url: str = Field(
        ...,
        description="Confluence Cloud URL (e.g., https://company.atlassian.net/wiki)",
    )
    username_or_email: str = Field(
        ..., description="Confluence username or email"
    )
    api_token: str = Field(..., description="Confluence API token")


class ConfluenceCredentialUpdate(BaseModel):
    """Request model for updating a Confluence credential."""

    name: Optional[str] = Field(
        None, description="New name for the credential"
    )
    cloud_url: Optional[str] = Field(
        None, description="New Confluence Cloud URL"
    )
    username_or_email: Optional[str] = Field(
        None, description="New username or email"
    )
    api_token: Optional[str] = Field(None, description="New API token")


class ConfluenceCredentialResponse(BaseModel):
    """Response model for a Confluence credential."""

    id: str = Field(..., description="Credential ID")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Credential name")
    cloud_url: str = Field(..., description="Confluence Cloud URL")
    username_or_email: str = Field(..., description="Username or email")
    created_at: str = Field(..., description="Creation timestamp")
    last_verified: Optional[str] = Field(
        ..., description="Last verification timestamp"
    )
    is_active: bool = Field(..., description="Whether credential is active")

    class Config:
        from_attributes = True


class ConfluenceVerifyResponse(BaseModel):
    """Response model for credential verification."""

    success: bool = Field(..., description="Whether verification succeeded")
    message: str = Field(..., description="Verification result message")


class ConfluenceErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str = Field(..., description="Error message")


# ==================== Router ====================

router = APIRouter(
    prefix="/api/v1/confluence",
    tags=["confluence"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
    },
)


# ==================== Endpoints ====================


@router.post(
    "/credentials",
    response_model=ConfluenceCredentialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Confluence credential",
    description="Create and store a new Confluence API credential",
)
async def create_confluence_credential(
    request: ConfluenceCredentialCreate,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Create a new Confluence credential.

    The credential is encrypted before being stored in the database.
    The API token is not returned in responses after creation.

    Args:
        request: Credential creation request
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        ConfluenceCredentialResponse: The created credential

    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(
            f"Creating Confluence credential for user: {current_user.id}"
        )

        credential = await service.create_credential(
            user_id=current_user.id,
            name=request.name,
            cloud_url=request.cloud_url,
            username_or_email=request.username_or_email,
            api_token=request.api_token,
        )

        # Verify the credential immediately
        try:
            await service.verify_credential(credential.id, current_user.id)
            logger.info(
                f"Created and verified Confluence credential: {credential.id}"
            )
        except Exception as e:
            logger.warning(
                f"Credential created but verification failed: {e}. "
                f"User should verify manually."
            )

        return credential

    except ValueError as e:
        logger.error(f"Invalid credential request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create credential",
        )


@router.get(
    "/credentials/{credential_id}",
    response_model=ConfluenceCredentialResponse,
    summary="Get Confluence credential",
    description="Retrieve a Confluence credential by ID",
)
async def get_confluence_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Get a Confluence credential by ID.

    Args:
        credential_id: ID of the credential to retrieve
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        ConfluenceCredentialResponse: The requested credential

    Raises:
        HTTPException: If credential not found or access denied
    """
    try:
        credential = await service.get_credential(
            credential_id, current_user.id
        )

        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found",
            )

        return credential

    except PermissionError as e:
        logger.warning(f"Permission denied for credential {credential_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credential",
        )


@router.get(
    "/credentials",
    response_model=List[ConfluenceCredentialResponse],
    summary="List Confluence credentials",
    description="List all Confluence credentials for the current user",
)
async def list_confluence_credentials(
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    List all Confluence credentials for the current user.

    Args:
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        List[ConfluenceCredentialResponse]: List of credentials
    """
    try:
        logger.debug(f"Listing credentials for user: {current_user.id}")

        credentials = await service.list_credentials(current_user.id)
        return credentials

    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list credentials",
        )


@router.put(
    "/credentials/{credential_id}",
    response_model=ConfluenceCredentialResponse,
    summary="Update Confluence credential",
    description="Update an existing Confluence credential",
)
async def update_confluence_credential(
    credential_id: str,
    request: ConfluenceCredentialUpdate,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Update a Confluence credential.

    Args:
        credential_id: ID of the credential to update
        request: Update request with optional fields
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        ConfluenceCredentialResponse: The updated credential

    Raises:
        HTTPException: If credential not found or update fails
    """
    try:
        logger.info(f"Updating credential: {credential_id}")

        credential = await service.update_credential(
            credential_id=credential_id,
            user_id=current_user.id,
            name=request.name,
            cloud_url=request.cloud_url,
            username_or_email=request.username_or_email,
            api_token=request.api_token,
        )

        return credential

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credential",
        )


@router.delete(
    "/credentials/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Confluence credential",
    description="Delete a Confluence credential",
)
async def delete_confluence_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Delete a Confluence credential.

    Args:
        credential_id: ID of the credential to delete
        current_user: Currently authenticated user
        service: Confluence credential service

    Raises:
        HTTPException: If credential not found or deletion fails
    """
    try:
        logger.info(f"Deleting credential: {credential_id}")

        success = await service.delete_credential(
            credential_id, current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete credential",
            )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credential",
        )


@router.post(
    "/credentials/{credential_id}/verify",
    response_model=ConfluenceVerifyResponse,
    summary="Verify Confluence credential",
    description="Test a Confluence credential by connecting to the API",
)
async def verify_confluence_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Verify a Confluence credential by testing the connection.

    Args:
        credential_id: ID of the credential to verify
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        ConfluenceVerifyResponse: Verification result

    Raises:
        HTTPException: If verification fails
    """
    try:
        logger.info(f"Verifying credential: {credential_id}")

        await service.verify_credential(credential_id, current_user.id)

        return ConfluenceVerifyResponse(
            success=True, message="Credential verified successfully"
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        # Could be either not found or verification failed
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        else:
            return ConfluenceVerifyResponse(success=False, message=str(e))
    except Exception as e:
        logger.error(f"Failed to verify credential: {e}")
        return ConfluenceVerifyResponse(
            success=False, message=f"Verification failed: {str(e)}"
        )


@router.post(
    "/credentials/{credential_id}/deactivate",
    response_model=ConfluenceCredentialResponse,
    summary="Deactivate Confluence credential",
    description="Deactivate a credential without deleting it",
)
async def deactivate_confluence_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Deactivate a Confluence credential.

    Args:
        credential_id: ID of the credential to deactivate
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        ConfluenceCredentialResponse: The updated credential

    Raises:
        HTTPException: If credential not found or deactivation fails
    """
    try:
        logger.info(f"Deactivating credential: {credential_id}")

        await service.deactivate_credential(credential_id, current_user.id)
        credential = await service.get_credential(
            credential_id, current_user.id
        )

        return credential

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to deactivate credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate credential",
        )


@router.post(
    "/credentials/{credential_id}/activate",
    response_model=ConfluenceCredentialResponse,
    summary="Activate Confluence credential",
    description="Activate a deactivated credential",
)
async def activate_confluence_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    service: ConfluenceCredentialService = Depends(
        get_confluence_credential_service
    ),
):
    """
    Activate a Confluence credential.

    Args:
        credential_id: ID of the credential to activate
        current_user: Currently authenticated user
        service: Confluence credential service

    Returns:
        ConfluenceCredentialResponse: The updated credential

    Raises:
        HTTPException: If credential not found or activation fails
    """
    try:
        logger.info(f"Activating credential: {credential_id}")

        await service.activate_credential(credential_id, current_user.id)
        credential = await service.get_credential(
            credential_id, current_user.id
        )

        return credential

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to activate credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate credential",
        )
