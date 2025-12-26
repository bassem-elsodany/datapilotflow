# Confluence API Integration Documentation

## Overview

This document describes the complete integration of Atlassian Confluence Cloud API into DataPilotFlow's document processing pipeline. This integration allows users to extract knowledge directly from Confluence instances via the API, instead of relying on web crawling.

## Architecture

### Components

1. **Domain Layer** (`datapilotflow-domain`)
   - `ContentSourceType.CONFLUENCE` - New content source type
   - `ConfluenceScrapingMode` - 4 extraction modes
   - `ConfluenceConfig` - Complete configuration model
   - `ConfluenceContentExtracted` - Domain event

2. **Processor Layer** (`datapilotflow-processors`)
   - `ConfluenceApiClient` - API interaction with authentication, pagination, format conversion
   - `ConfluenceDocumentExtractor` - Async generator-based document extraction
   - `DocumentExtractionService` - Routing to Confluence extractor

3. **Service Layer** (`datapilotflow-services`)
   - `ConfluenceCredentialService` - Credential lifecycle management
   - `ConfluenceMetadataService` - Space and page metadata caching

4. **API Layer** (`datapilotflow-api`)
   - REST endpoints for credential management at `/api/v1/confluence/`
   - 10 endpoints covering CRUD operations and verification

5. **Infrastructure Layer** (`datapilotflow-infrastructure`)
   - `ConfluenceCredentialDAO` - Credential persistence
   - `ConfluenceSpaceDAO` - Space metadata caching
   - `ConfluencePageDAO` - Page metadata caching

6. **UI Layer** (`dashboard`)
   - TypeScript schemas for Confluence types
   - API hooks for credential management
   - Configuration endpoints

### Data Flow

```
User Creates Confluence Job
    ↓
POST /api/v1/confluence/credentials
    ↓ (Store & verify credential)
POST /api/v1/knowledge-jobs/{id}/execute
    ↓ (Create JobActionRequested event)
RabbitMQ job_events_queue
    ↓
JobEventListener
    ↓
RefactoredKnowledgeJobEventProcessor
    ↓
JobOrchestrator (with PipelineFactory routing)
    ↓
DocumentExtractionStep
    ↓
DocumentExtractionService._extract_from_confluence()
    ↓
ConfluenceDocumentExtractor
    ↓
ConfluenceApiClient (fetch from API)
    ↓
Batch Document Yielding
    ↓
Pipeline: Chunking → Embedding → Storage → Timeline
    ↓
Job Completion with Statistics
```

## Configuration

### Confluence Extraction Modes

1. **SPECIFIC_PAGES** - Extract specific page IDs
   - Required: `page_ids` list
   - Example: Extract by IDs ["123456", "789012"]

2. **SPACE_PAGES** - Extract all pages in specific spaces
   - Required: `space_keys` list
   - Optional: `max_pages_per_space` for limiting
   - Example: Extract all pages from "TECH" and "DOCS" spaces

3. **PAGES_WITH_LABEL** - Extract pages matching specific labels
   - Required: `labels` list
   - Example: Extract all pages tagged with "important" and "api-docs"

4. **RECENTLY_MODIFIED** - Extract recently modified pages
   - Fetches pages modified in last 30 days
   - No additional configuration required
   - Useful for incremental updates

### Configuration Fields

```python
ConfluenceConfig:
  # Confluence instance details (required)
  cloud_url: str                    # e.g., https://company.atlassian.net/wiki
  username_or_email: str            # For Basic Auth
  api_token: str                    # Confluence API token

  # Extraction mode (required)
  confluence_mode: ConfluenceScrapingMode

  # Mode-specific fields
  space_keys: Optional[List[str]]   # For space_pages mode
  page_ids: Optional[List[str]]     # For specific_pages mode
  labels: Optional[List[str]]       # For pages_with_label mode

  # Filtering options
  include_attachments: bool         # Default: false
  include_comments: bool            # Default: false
  max_pages_per_space: Optional[int]

  # Processing options
  expand_child_pages: bool          # Default: true
  follow_page_links: bool           # Default: false
```

## API Reference

### Base URL
```
/api/v1/confluence
```

### Endpoints

#### Create Credential
```
POST /credentials
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Confluence",
  "cloud_url": "https://company.atlassian.net/wiki",
  "username_or_email": "user@company.com",
  "api_token": "{api_token}"
}

Response: 201 Created
{
  "id": "credential_id",
  "user_id": "user_id",
  "name": "My Confluence",
  "cloud_url": "https://company.atlassian.net/wiki",
  "username_or_email": "user@company.com",
  "created_at": "2024-01-01T12:00:00Z",
  "last_verified": null,
  "is_active": true
}
```

#### List Credentials
```
GET /credentials
Authorization: Bearer {token}

Response: 200 OK
[
  { ... credential ... }
]
```

#### Get Credential
```
GET /credentials/{credential_id}
Authorization: Bearer {token}

Response: 200 OK
{ ... credential ... }
```

#### Update Credential
```
PUT /credentials/{credential_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name",
  "cloud_url": "...",
  "username_or_email": "...",
  "api_token": "..."
}

Response: 200 OK
{ ... updated credential ... }
```

#### Verify Credential
```
POST /credentials/{credential_id}/verify
Authorization: Bearer {token}

Response: 200 OK
{
  "success": true,
  "message": "Credential verified successfully"
}
```

#### Deactivate Credential
```
POST /credentials/{credential_id}/deactivate
Authorization: Bearer {token}

Response: 200 OK
{ ... credential with is_active: false ... }
```

#### Activate Credential
```
POST /credentials/{credential_id}/activate
Authorization: Bearer {token}

Response: 200 OK
{ ... credential with is_active: true ... }
```

#### Delete Credential
```
DELETE /credentials/{credential_id}
Authorization: Bearer {token}

Response: 204 No Content
```

## Implementation Details

### API Client

**File**: `datapilotflow-processors/src/datapilotflow/processors/confluence/confluence_api_client.py`

**Features**:
- Basic Auth with email + API token
- 4 methods for different page fetching strategies
- Pagination support (up to 250 items per request)
- Confluence Storage Format (XHTML) → Markdown conversion
- Comprehensive error handling and logging
- Rate limiting detection and reporting

**Key Methods**:
- `verify_credentials()` - Test API connection
- `get_space_pages(space_key)` - Fetch pages from space
- `get_page_by_id(page_id)` - Fetch specific page
- `get_pages_by_label(labels)` - Search by labels
- `get_recently_modified_pages(limit)` - Fetch recent pages

### Document Extractor

**File**: `datapilotflow-processors/src/datapilotflow/processors/confluence/confluence_document_extractor.py`

**Features**:
- Async generator pattern for memory efficiency
- Batch-wise document yielding (matching web extraction)
- Support for all 4 extraction modes
- Conversion to LangChain Document with metadata

**Metadata Included**:
- `source_url` - Direct link to Confluence page
- `title` - Page title
- `page_id` - Confluence page ID
- `space_key` - Space containing page
- `labels` - Page labels
- `version` - Page version number
- `last_modified` - Modification timestamp
- `confluence_mode` - Which extraction mode was used
- `extraction_method` - "confluence_api"

### Credential Service

**File**: `datapilotflow-services/src/datapilotflow/services/confluence/confluence_credential_service.py`

**Responsibilities**:
- Create, read, update, delete credentials
- User ownership verification
- Credential verification via API test
- Activate/deactivate without deletion
- Encryption of API tokens before storage

### Metadata Service

**File**: `datapilotflow-services/src/datapilotflow/services/confluence/confluence_metadata_service.py`

**Responsibilities**:
- Sync and cache Confluence spaces
- Fetch pages by space with pagination
- Search pages by labels
- Cache invalidation with 1-hour TTL

## Database Schema

### Tables

**confluence_credentials**
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to users)
- `name`: String
- `cloud_url`: String
- `username_or_email`: String (encrypted)
- `api_token`: String (encrypted)
- `created_at`: Timestamp
- `last_verified`: Timestamp (nullable)
- `is_active`: Boolean

**confluence_spaces_cache**
- `id`: UUID (primary key)
- `credential_id`: UUID (foreign key)
- `user_id`: UUID
- `space_key`: String
- `space_name`: String
- `total_pages`: Integer
- `last_synced`: Timestamp

**confluence_pages_cache**
- `id`: UUID (primary key)
- `credential_id`: UUID (foreign key)
- `user_id`: UUID
- `space_key`: String
- `page_id`: String
- `page_title`: String
- `page_version`: Integer
- `last_modified`: Timestamp
- `labels`: Array[String]
- `last_synced`: Timestamp

## TypeScript Schemas

**File**: `dashboard/src/api/resources/knowledge-sources.ts`

Schemas exported:
- `ConfluenceScrapingModeSchema`
- `ConfluenceConfigSchema`
- `ContentSourceTypeSchema` (updated to include 'confluence')

**File**: `dashboard/src/api/resources/confluence-credentials.ts`

Exports:
- `ConfluenceCredentialSchema`
- `ConfluenceCredentialCreateSchema`
- `ConfluenceCredentialUpdateSchema`
- React Query hooks for all operations

## Usage Example

### 1. Create Credential

```bash
curl -X POST http://localhost:8000/api/v1/confluence/credentials \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Company Confluence",
    "cloud_url": "https://company.atlassian.net/wiki",
    "username_or_email": "user@company.com",
    "api_token": "{confluence_api_token}"
  }'
```

### 2. Verify Credential

```bash
curl -X POST http://localhost:8000/api/v1/confluence/credentials/{credential_id}/verify \
  -H "Authorization: Bearer {token}"
```

### 3. Create Knowledge Source

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/sources \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Company Docs from Confluence",
    "content_source_type": "confluence",
    "confluence_credential_id": "{credential_id}",
    "confluence_config": {
      "cloud_url": "https://company.atlassian.net/wiki",
      "username_or_email": "user@company.com",
      "api_token": "{confluence_api_token}",
      "confluence_mode": "space_pages",
      "space_keys": ["TECH", "DOCS"],
      "include_attachments": false,
      "expand_child_pages": true
    }
  }'
```

### 4. Create Job

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/sources/{config_id}/jobs \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Extract Confluence Docs",
    "vectordb_collection_id": "{collection_id}",
    "splitter_id": "{splitter_id}",
    "batch_size": 100
  }'
```

### 5. Execute Job

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/jobs/{job_id}/execute \
  -H "Authorization: Bearer {token}"
```

## Error Handling

The system handles the following error scenarios:

1. **Authentication Errors** (401)
   - Invalid credentials
   - Expired token
   - Permission denied

2. **Validation Errors** (400)
   - Missing required fields
   - Invalid configuration
   - Malformed requests

3. **Not Found Errors** (404)
   - Space not found in Confluence
   - Page not found
   - Credential not found

4. **Rate Limiting** (429)
   - Confluence API rate limit exceeded
   - Automatic retry with exponential backoff

5. **Server Errors** (500)
   - Confluence server errors
   - Internal processing errors
   - Database errors

## Security Considerations

1. **Token Encryption**
   - API tokens are encrypted before storage in database
   - Encryption key should be managed via environment variables
   - Never return tokens in API responses

2. **User Isolation**
   - All credentials are tied to user accounts
   - Users can only access their own credentials
   - Permission checks on all operations

3. **Rate Limiting**
   - Respects Confluence API rate limits (420 requests per minute)
   - Implements exponential backoff on 429 responses

4. **Access Control**
   - All endpoints require authentication
   - Proper HTTP status codes returned
   - Audit logging of sensitive operations

## Performance Considerations

1. **Pagination**
   - API client fetches up to 250 items per request
   - Supports configurable page limits per space

2. **Batch Processing**
   - Documents yielded in configurable batches
   - Memory efficient for large spaces

3. **Caching**
   - Spaces and pages cached with 1-hour TTL
   - Cache invalidation on credential updates

4. **Async Processing**
   - Event-driven architecture with RabbitMQ
   - Background job processing doesn't block UI
   - Real-time progress notifications

## Future Enhancements

1. **OAuth 2.0 Support** - Replace Basic Auth with OAuth
2. **Incremental Sync** - Track last sync and only fetch new/modified pages
3. **Comment Threading** - Include discussion threads as separate documents
4. **Attachment Processing** - Extract text from attachments
5. **Deep Page Linking** - Follow cross-page links for comprehensive extraction
6. **Custom Field Support** - Extract custom metadata fields
7. **Space Webhooks** - Real-time updates when pages change

## Testing

### Unit Tests
- `test_confluence_api_client.py` - API client functionality
- `test_confluence_document_extractor.py` - Document extraction
- `test_confluence_credential_service.py` - Credential management

### Integration Tests
- Full pipeline from credential creation to document extraction
- API endpoint testing
- Database operation verification

### End-to-End Tests
- Complete job execution with Confluence source
- Vector database integration
- Timeline progress tracking

## Troubleshooting

### Common Issues

**Invalid Credentials**
- Verify API token is valid for the Confluence instance
- Check email/username is correct
- Ensure API token has necessary scopes

**Rate Limit Exceeded**
- Wait 1 minute before retrying
- System automatically implements exponential backoff
- Consider reducing batch size

**Page Not Found**
- Verify page ID/space key is correct
- Check user has access to the page
- Page may have been deleted or moved

**Storage Format Conversion Error**
- Complex page layouts may not convert perfectly
- Check logs for specific conversion errors
- Consider using "follow_page_links: false"

## Support

For issues, questions, or feature requests, please:
1. Check the logs in `/var/log/datapilotflow/`
2. Review the error messages in the UI
3. Contact the development team with detailed error logs

## License

This integration is part of DataPilotFlow and follows the same license terms.
