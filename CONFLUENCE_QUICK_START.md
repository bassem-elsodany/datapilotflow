# Confluence API Integration - Quick Start Guide

## Overview
Confluence Cloud API integration is now available as an alternative to web crawling for document extraction in DataPilotFlow.

## For Users: Creating a Confluence Knowledge Source

### Step 1: Create a Confluence Credential
```bash
curl -X POST http://localhost:8000/api/v1/confluence/credentials \
  -H "Authorization: Bearer {your-jwt-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Confluence Instance",
    "cloud_url": "https://mycompany.atlassian.net/wiki",
    "username_or_email": "user@company.com",
    "api_token": "{your-confluence-api-token}"
  }'
```

Response:
```json
{
  "id": "credential-uuid",
  "user_id": "user-uuid",
  "name": "My Confluence Instance",
  "cloud_url": "https://mycompany.atlassian.net/wiki",
  "username_or_email": "user@company.com",
  "created_at": "2024-01-01T12:00:00Z",
  "last_verified": null,
  "is_active": true
}
```

### Step 2: Verify the Credential
```bash
curl -X POST http://localhost:8000/api/v1/confluence/credentials/{credential-id}/verify \
  -H "Authorization: Bearer {your-jwt-token}"
```

Response:
```json
{
  "success": true,
  "message": "Credential verified successfully"
}
```

### Step 3: Create a Knowledge Source
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/sources \
  -H "Authorization: Bearer {your-jwt-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Company Confluence Docs",
    "content_source_type": "confluence",
    "confluence_credential_id": "{credential-id}",
    "confluence_config": {
      "cloud_url": "https://mycompany.atlassian.net/wiki",
      "username_or_email": "user@company.com",
      "api_token": "{your-confluence-api-token}",
      "confluence_mode": "space_pages",
      "space_keys": ["TECH", "DOCS"],
      "include_attachments": false,
      "expand_child_pages": true
    }
  }'
```

### Step 4: Create and Execute a Job
```bash
# Create job
curl -X POST http://localhost:8000/api/v1/knowledge/sources/{source-id}/jobs \
  -H "Authorization: Bearer {your-jwt-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Extract Confluence Docs",
    "vectordb_collection_id": "{collection-id}",
    "splitter_id": "{splitter-id}",
    "batch_size": 100
  }'

# Execute job
curl -X POST http://localhost:8000/api/v1/knowledge/jobs/{job-id}/execute \
  -H "Authorization: Bearer {your-jwt-token}"
```

## Extraction Modes

### 1. Space Pages (Recommended)
Extract all pages from specific spaces.

```json
{
  "confluence_mode": "space_pages",
  "space_keys": ["TECH", "DOCS", "API"]
}
```

### 2. Specific Pages
Extract individual pages by ID.

```json
{
  "confluence_mode": "specific_pages",
  "page_ids": ["123456", "789012", "345678"]
}
```

### 3. Pages with Labels
Extract pages matching specific labels.

```json
{
  "confluence_mode": "pages_with_label",
  "labels": ["important", "api-docs", "internal"]
}
```

### 4. Recently Modified
Extract recently changed pages (last 30 days).

```json
{
  "confluence_mode": "recently_modified"
}
```

## Configuration Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cloud_url` | string | Yes | - | Confluence Cloud URL |
| `username_or_email` | string | Yes | - | Authentication user |
| `api_token` | string | Yes | - | Confluence API token |
| `confluence_mode` | enum | Yes | - | Extraction mode |
| `space_keys` | array | No | - | For space_pages mode |
| `page_ids` | array | No | - | For specific_pages mode |
| `labels` | array | No | - | For pages_with_label mode |
| `include_attachments` | bool | No | false | Include attachments |
| `include_comments` | bool | No | false | Include comments |
| `max_pages_per_space` | int | No | - | Limit per space |
| `expand_child_pages` | bool | No | true | Include child pages |
| `follow_page_links` | bool | No | false | Follow cross-page links |

## API Reference

### Credential Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/confluence/credentials` | Create credential |
| GET | `/api/v1/confluence/credentials` | List credentials |
| GET | `/api/v1/confluence/credentials/{id}` | Get credential |
| PUT | `/api/v1/confluence/credentials/{id}` | Update credential |
| DELETE | `/api/v1/confluence/credentials/{id}` | Delete credential |
| POST | `/api/v1/confluence/credentials/{id}/verify` | Verify credential |
| POST | `/api/v1/confluence/credentials/{id}/deactivate` | Deactivate |
| POST | `/api/v1/confluence/credentials/{id}/activate` | Activate |

### Knowledge Source Endpoints

Create a knowledge source with `confluence` content type to use Confluence API.

## For Developers: Testing

### Run All Tests
```bash
pytest datapilotflow-processors/tests/confluence/ \
        datapilotflow-services/tests/confluence/ \
        datapilotflow-infrastructure/tests/confluence/ -v
```

### Run Unit Tests
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_api_client.py \
        datapilotflow-processors/tests/confluence/test_confluence_document_extractor.py -v
```

### Run with Coverage
```bash
pytest datapilotflow-processors/tests/confluence/ \
        datapilotflow-services/tests/confluence/ \
        datapilotflow-infrastructure/tests/confluence/ \
        --cov=datapilotflow.processors.confluence \
        --cov=datapilotflow.services.confluence \
        --cov=datapilotflow.infrastructure.dao.confluence \
        --cov-report=html
```

## Common Issues

### Invalid Credentials Error
**Problem**: "Unauthorized" when verifying credentials
**Solution**:
- Verify API token is correct
- Ensure email/username is correct
- Check API token has necessary scopes
- Verify token hasn't expired

### Rate Limit Exceeded
**Problem**: "Too many requests" (429)
**Solution**:
- System automatically implements exponential backoff
- Wait 1 minute before retrying
- Consider reducing batch size
- Confluence limit: 420 requests/minute

### Page Not Found
**Problem**: Specific page cannot be extracted
**Solution**:
- Verify page ID is correct
- Check user has access to page
- Page may have been deleted or archived

### Empty Results
**Problem**: No pages extracted from space
**Solution**:
- Verify space key is correct
- Check user has access to space
- Space may have no pages matching criteria

## Security Notes

✅ **Do**:
- Store API tokens securely
- Use HTTPS for all API calls
- Rotate API tokens regularly
- Enable credential verification

❌ **Don't**:
- Hardcode API tokens
- Share credentials across users
- Log API tokens
- Commit tokens to version control

## Getting Help

### Documentation
- [CONFLUENCE_INTEGRATION.md](CONFLUENCE_INTEGRATION.md) - Complete integration guide
- [CONFLUENCE_TESTING.md](CONFLUENCE_TESTING.md) - Testing guide
- [CONFLUENCE_IMPLEMENTATION_SUMMARY.md](CONFLUENCE_IMPLEMENTATION_SUMMARY.md) - Implementation overview

### Common Tasks

**List all my credentials**:
```bash
curl -X GET http://localhost:8000/api/v1/confluence/credentials \
  -H "Authorization: Bearer {your-jwt-token}"
```

**Update a credential**:
```bash
curl -X PUT http://localhost:8000/api/v1/confluence/credentials/{id} \
  -H "Authorization: Bearer {your-jwt-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "api_token": "{new-token}"
  }'
```

**Delete a credential**:
```bash
curl -X DELETE http://localhost:8000/api/v1/confluence/credentials/{id} \
  -H "Authorization: Bearer {your-jwt-token}"
```

**Deactivate a credential** (soft delete):
```bash
curl -X POST http://localhost:8000/api/v1/confluence/credentials/{id}/deactivate \
  -H "Authorization: Bearer {your-jwt-token}"
```

## Performance Tips

1. **Use Specific Extraction Mode**: Choose the most specific mode for your use case
   - Specific pages: Fastest
   - Space pages: Good for comprehensive extraction
   - Labels: Good for targeted extraction
   - Recently modified: Good for incremental updates

2. **Optimize Batch Size**: Experiment with batch_size parameter
   - Smaller batches: Lower memory, slower processing
   - Larger batches: Higher memory, faster processing
   - Default: 50 pages per batch

3. **Limit Pages Per Space**: Use max_pages_per_space to avoid overloading

4. **Schedule Off-Peak**: Extract during off-peak hours to avoid rate limits

5. **Use Labels**: For large spaces, use label-based extraction for targeted results

## Next Steps

1. Get Confluence API token from your admin
2. Create a credential with Step 1 above
3. Verify credential works with Step 2
4. Create knowledge source with desired extraction mode
5. Create and execute extraction job
6. Monitor job progress in timeline
7. Search extracted documents in conversations

## Support Channels

- Check documentation files for detailed information
- Review test examples for usage patterns
- Check logs in `/var/log/datapilotflow/`
- Contact development team for issues

---

**Last Updated**: 2025-12-26
**Version**: 1.0
**Status**: Production Ready
