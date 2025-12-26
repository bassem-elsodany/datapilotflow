# Confluence Integration - Quick Reference

Fast reference for working with Confluence in DataPilotFlow.

## File Locations

### Docker Setup (in `docker/confluence/`)
- `docker-compose.confluence.yml` - Docker Compose configuration
- `confluence-init.sql` - PostgreSQL initialization script

### Backend Implementation
- `datapilotflow-processors/src/datapilotflow/processors/confluence/`
  - `confluence_document_extractor.py` - Document extraction from Confluence API
  - `confluence_markdown_converter.py` - XHTML to Markdown conversion
- `datapilotflow-infrastructure/src/datapilotflow/infrastructure/dao/model_provider/`
  - `confluence_credential_dao.py` - Credential storage
- `datapilotflow-domain/src/datapilotflow/domain/knowledge/`
  - `knowledge_source_config.py` - Configuration schemas

### Frontend Components
- `dashboard/src/pages/dashboard/management/knowledge-sources/config-create/`
  - `index.tsx` - Create RAG Configuration form (includes Confluence section)
- `dashboard/src/api/resources/`
  - `confluence-credentials.ts` - API hooks for credentials
  - `model-providers.ts` - Updated with Confluence provider

### Setup & Testing
- `confluence_test_data_setup.py` - Create test spaces and pages
- `CONFLUENCE_DOCKER_SETUP.md` - Complete setup guide
- `CONFLUENCE_MARKDOWN_GENERATION.md` - Markdown conversion details
- Tests in `datapilotflow-processors/tests/confluence/`

## Common Tasks

### Start Local Confluence Instance
```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow
docker-compose -f docker/confluence/docker-compose.confluence.yml up -d
```

### Create Test Data
```bash
python3 confluence_test_data_setup.py \
  --url http://localhost:8090 \
  --username admin@example.com \
  --api-token YOUR_TOKEN
```

### Run Tests
```bash
# All Confluence tests
pytest datapilotflow-processors/tests/confluence/ -v

# Markdown converter tests only
pytest datapilotflow-processors/tests/confluence/test_confluence_markdown_converter.py -v
```

### Stop Confluence
```bash
docker-compose -f docker/confluence/docker-compose.confluence.yml down
```

## API Endpoints

### Confluence Credentials
```bash
# List credentials
GET /api/v1/confluence/credentials

# Create credential
POST /api/v1/confluence/credentials
Body: {
  "name": "string",
  "cloud_url": "string",
  "username_or_email": "string",
  "api_token": "string"
}

# Get credential
GET /api/v1/confluence/credentials/{id}

# Delete credential
DELETE /api/v1/confluence/credentials/{id}
```

### Knowledge Source Configuration
```bash
# Create Confluence source (in create RAG config)
POST /api/v1/knowledge/sources
Body: {
  "name": "string",
  "description": "string",
  "content_source_type": "confluence",
  "confluence_credential_id": "string",
  "confluence_mode": "space_pages|specific_pages|pages_with_label",
  "confluence_config": {
    "cloud_url": "string",
    "space_keys": ["TECH", "DOCS"],  // for space_pages mode
    "page_ids": ["123", "456"],       // for specific_pages mode
    "labels": ["api-docs"],           // for pages_with_label mode
    "output_format": "html|markdown",
    "markdown_generation": "standard|llm"
  }
}
```

## Configuration Modes

### space_pages
Extract all pages from specified spaces
- `space_keys`: Array of space keys (e.g., ["TECH", "DOCS"])

### specific_pages
Extract specific pages by ID
- `page_ids`: Array of page IDs (e.g., ["123456", "789012"])

### pages_with_label
Extract pages with specific labels
- `labels`: Array of label names (e.g., ["api-docs", "important"])
- `include_attachments` (optional): Boolean to include attachments

## Output Formats

### HTML
- Raw Confluence XHTML storage format
- Useful for preserving formatting nuances
- Larger file size
- Faster extraction (no conversion overhead)

### Markdown
- Converted from XHTML using custom converter
- Better for embeddings and LLM processing
- Supports Confluence macros:
  - Alerts (info, warning, tip, note, panel) → GitHub-style alerts
  - Expandable content → HTML `<details>` tags
  - JIRA references → Markdown links
  - Tables with colspan/rowspan handling
  - Code blocks with language detection

## Testing Confluence Integration

### Manual Testing Flow
1. Start local Confluence:
   ```bash
   docker-compose -f docker/confluence/docker-compose.confluence.yml up -d
   ```

2. Complete Confluence setup wizard
   - License: Trial (auto-generated)
   - Database: auto-detected PostgreSQL
   - Admin account: admin@example.com / password

3. Create API token from Confluence UI
   - Settings → Admin → Users → Security → Create API token

4. Create test data:
   ```bash
   python3 confluence_test_data_setup.py \
     --url http://localhost:8090 \
     --username admin@example.com \
     --api-token TOKEN
   ```

5. In DataPilotFlow:
   - Create Confluence credential
   - Create knowledge source with Confluence
   - Select "Markdown" output format
   - Execute extraction job
   - Verify converted Markdown content

### Automated Testing
```bash
# Run all Confluence tests
pytest datapilotflow-processors/tests/confluence/ -v

# Test markdown converter specifically
pytest datapilotflow-processors/tests/confluence/test_confluence_markdown_converter.py::TestBasicMarkdownConversion -v

# Test with coverage
pytest datapilotflow-processors/tests/confluence/ --cov=datapilotflow.processors.confluence --cov-report=html
```

## Troubleshooting

### "Cannot connect to Confluence"
- Check Confluence is running: `docker-compose -f docker/confluence/docker-compose.confluence.yml ps`
- Check URL format: `http://localhost:8090` (with protocol)
- Check credentials: test with `curl` first

### "401 Unauthorized" with API token
- Verify token is recent (create new one if old)
- Ensure username matches email address exactly
- Check token is not truncated or has extra spaces

### "Markdown conversion failed"
- Check XHTML content is valid (malformed HTML is auto-repaired)
- Review converter output in logs
- Check for unsupported Confluence macros

### "Port 8090 already in use"
- Find process: `lsof -i :8090`
- Use different port: edit `docker-compose.confluence.yml`
- Or stop other service using the port

## Performance Tips

### Extraction Speed
- `space_pages` mode is faster than `specific_pages` (batch API call)
- HTML format extracts faster than Markdown (no conversion)
- Large spaces benefit from pagination/chunking

### Markdown Conversion
- Small pages (<10KB): <10ms conversion
- Medium pages (10-100KB): 10-50ms
- Large pages (>100KB): 50-200ms
- Complex tables with rowspan/colspan slower but reliable

### Memory Usage
- Confluence Docker: Default 512MB min, 1024MB max
- For pages >100KB: increase JVM heap to 1024MB-2048MB
- PostgreSQL: Minimal (~40MB container, plus data volume)

## Knowledge Articles

- [Confluence API Docs](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796537.html)
- [Cloud REST API v2](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-content/)
- [Markdown Conversion Implementation](CONFLUENCE_MARKDOWN_GENERATION.md)
- [Docker Setup Guide](CONFLUENCE_DOCKER_SETUP.md)

## Git Status

Current branch: `feat/package-refactoring`

Key commits:
- `b0dc2fb` - Add Confluence to Create RAG Configuration form
- `0ed92a6` - Add Generation step for Confluence
- `7a7f8c7` - Implement ConfluenceMarkdownConverter
- `2d8a92a` - Add inline credential creation modal
- Current - Docker setup and test data automation

## Next Steps

After complete integration testing:
1. Merge feature branch to main
2. Deploy to staging environment
3. Conduct end-to-end testing with real Confluence instances
4. Gather user feedback on markdown conversion quality
5. Plan Phase 2: LLM-powered markdown generation

## Support

For issues or questions:
1. Check [CONFLUENCE_DOCKER_SETUP.md](CONFLUENCE_DOCKER_SETUP.md) troubleshooting section
2. Review test cases in `tests/confluence/`
3. Check backend logs: `docker-compose -f docker/confluence/docker-compose.confluence.yml logs confluence`
4. Check API logs in DataPilotFlow API container
5. Test API directly with curl before creating tickets

---

Last Updated: 2025-12-26
