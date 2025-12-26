"""Confluence Data Access Objects."""

from .confluence_credential_dao import (
    ConfluenceCredential,
    ConfluenceCredentialDAO,
    get_confluence_credential_dao,
)
from .confluence_page_dao import (
    ConfluencePage,
    ConfluencePageDAO,
    get_confluence_page_dao,
)
from .confluence_space_dao import (
    ConfluenceSpace,
    ConfluenceSpaceDAO,
    get_confluence_space_dao,
)

__all__ = [
    # Credentials
    "ConfluenceCredential",
    "ConfluenceCredentialDAO",
    "get_confluence_credential_dao",
    # Spaces
    "ConfluenceSpace",
    "ConfluenceSpaceDAO",
    "get_confluence_space_dao",
    # Pages
    "ConfluencePage",
    "ConfluencePageDAO",
    "get_confluence_page_dao",
]
