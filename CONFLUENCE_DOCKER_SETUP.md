# Confluence Docker Setup for DataPilotFlow

Complete guide for running Confluence in Docker locally for testing the DataPilotFlow Confluence integration.

## Overview

This setup provides:
- **Confluence Server** - Running on `http://localhost:8090`
- **PostgreSQL Database** - Running on `localhost:5432`
- **Docker Compose** - Multi-container orchestration with health checks
- **Test Data** - Automated script to create sample spaces and pages
- **Markdown Conversion** - Support for converting Confluence content to Markdown

## Quick Start

### 1. Start Confluence

```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow

# Start Confluence and PostgreSQL database
docker-compose -f docker/confluence/docker-compose.confluence.yml up -d

# Watch startup logs (wait for "Confluence is running" message)
docker-compose -f docker/confluence/docker-compose.confluence.yml logs -f confluence
```

**Expected output:**
```
confluence-dev  | 2025-12-26 10:00:00,000 INFO [main] ... Confluence started successfully
```

### 2. Access Confluence UI

- **URL**: http://localhost:8090
- **Admin Port**: 8091
- **Wait Time**: 60-90 seconds for full startup

### 3. Complete Initial Setup Wizard

When you first access Confluence, a setup wizard will guide you through:

#### Step 1: License
- Select "Get a license" → "Use a trial license"
- Email: `test@example.com`
- Organization: `DataPilotFlow`

#### Step 2: Database Configuration
- Connection string should auto-populate:
  ```
  jdbc:postgresql://confluence-db:5432/confluence
  ```
- Username: `confluence`
- Password: `confluence`
- Click "Next" to test and proceed

#### Step 3: Site Configuration
- Site Name: `DataPilotFlow Confluence`
- Default Language: English
- Default Time Zone: UTC

#### Step 4: Administrator Account
- Full Name: `Test Admin`
- Email: `admin@example.com`
- Username: `admin`
- Password: Create a strong password (e.g., `TestConfluence123!`)

### 4. Generate API Token

1. Log in with admin account at http://localhost:8090
2. Click gear icon (⚙️) → Settings → Admin
3. Click Users → Find your admin user
4. Click "..." menu → Security
5. Under "API Tokens", click "Create API token"
6. Copy the token and save it (you won't see it again!)

### 5. Create Test Data

Install Python requests library:
```bash
pip install requests
```

Create test spaces and pages:

```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow

# Using command-line arguments
python3 confluence_test_data_setup.py \
  --url http://localhost:8090 \
  --username admin@example.com \
  --api-token YOUR_API_TOKEN_HERE

# Or using environment variables
export CONFLUENCE_URL=http://localhost:8090
export CONFLUENCE_USERNAME=admin@example.com
export CONFLUENCE_API_TOKEN=YOUR_API_TOKEN_HERE
python3 confluence_test_data_setup.py
```

**What gets created:**

| Space | Key | Pages |
|-------|-----|-------|
| Technical Documentation | TECH | Getting Started, Advanced Topics |
| User Documentation | DOCS | User Guide |
| REST API Reference | API | REST API Reference |

Each page includes:
- Headings and paragraphs
- Bold, italic, underlined text
- Lists (ordered and unordered)
- Code blocks with language highlighting
- Tables (simple and complex)
- Confluence macros (alerts, expandable content)
- Links and cross-references

### 6. Test with DataPilotFlow

#### Create Confluence Credential
1. In DataPilotFlow dashboard, navigate to **Integrations** → **Confluence Credentials**
2. Click **Create Credential**
3. Enter:
   - **Name**: Local Confluence Dev
   - **Cloud URL**: `http://localhost:8090` (or `http://confluence:8090` if running in Docker)
   - **Username**: `admin@example.com`
   - **API Token**: (paste token from step 4)
4. Click **Create**

#### Create Knowledge Source
1. Navigate to **Knowledge Sources** → **Create Configuration**
2. **Step 1: Basic Info**
   - Name: Confluence Test Source
   - Content Source: Confluence
   - Credential: Local Confluence Dev
   - Extraction Mode: Space Pages
   - Spaces: TECH, DOCS, API
3. **Step 2: Generation**
   - Output Format: **Markdown** (to test conversion)
   - Markdown Generation: Standard
4. **Step 3: Review** → Click Create

#### Execute Extraction Job
1. Find the created knowledge source
2. Click **Extract/Update**
3. Monitor job progress
4. Verify documents show:
   - Converted Markdown content
   - Proper formatting
   - Tables and code blocks rendered correctly
   - Confluence macros converted to alerts

## Docker Commands

### View Logs
```bash
# View Confluence logs
docker-compose -f docker/confluence/docker-compose.confluence.yml logs -f confluence

# View PostgreSQL logs
docker-compose -f docker/confluence/docker-compose.confluence.yml logs -f confluence-db

# View all logs
docker-compose -f docker/confluence/docker-compose.confluence.yml logs -f
```

### Stop Services
```bash
docker-compose -f docker/confluence/docker-compose.confluence.yml down
```

### Restart Services
```bash
docker-compose -f docker/confluence/docker-compose.confluence.yml restart
```

### Clean Up (Remove volumes)
```bash
# This will delete all Confluence data
docker-compose -f docker/confluence/docker-compose.confluence.yml down -v
```

### Rebuild Images
```bash
docker-compose -f docker/confluence/docker-compose.confluence.yml build --no-cache
```

### Execute Commands in Container
```bash
# Access Confluence container
docker-compose -f docker/confluence/docker-compose.confluence.yml exec confluence bash

# Access PostgreSQL
docker-compose -f docker/confluence/docker-compose.confluence.yml exec confluence-db psql -U confluence -d confluence
```

## Troubleshooting

### Issue: Confluence Takes Too Long to Start
**Symptoms**: Port 8090 not accessible after 5 minutes

**Solutions**:
1. Check logs: `docker-compose -f docker/confluence/docker-compose.confluence.yml logs confluence`
2. Check disk space: `df -h`
3. Increase JVM memory in `docker-compose.confluence.yml`:
   ```yaml
   JVM_MINIMUM_MEMORY: 1024m
   JVM_MAXIMUM_MEMORY: 2048m
   ```
4. Restart: `docker-compose -f docker/confluence/docker-compose.confluence.yml restart`

### Issue: PostgreSQL Connection Error
**Symptoms**: "Cannot connect to database" in setup wizard

**Solutions**:
1. Check PostgreSQL is running: `docker-compose -f docker/confluence/docker-compose.confluence.yml ps`
2. Check PostgreSQL logs: `docker-compose -f docker/confluence/docker-compose.confluence.yml logs confluence-db`
3. Verify database exists:
   ```bash
   docker-compose -f docker/confluence/docker-compose.confluence.yml exec confluence-db \
     psql -U confluence -l | grep confluence
   ```

### Issue: API Token Not Working
**Symptoms**: 401 Unauthorized when running `confluence_test_data_setup.py`

**Solutions**:
1. Verify token is correct (copy again from UI)
2. Check username matches admin account email
3. Test with curl:
   ```bash
   curl -u admin@example.com:YOUR_TOKEN \
     http://localhost:8090/rest/api/user/current
   ```
   Should return user JSON, not 401 error

### Issue: Markdown Conversion Not Working
**Symptoms**: Content extracted as HTML instead of Markdown

**Check**:
1. Verify `output_format` is set to `markdown` in knowledge source config
2. Check extraction job logs for conversion errors
3. Ensure `confluence_markdown_converter.py` is in processor pipeline
4. Review sample content - complex Confluence macros may have conversion issues

### Issue: Port Already in Use
**Symptoms**: `Error: Port 8090 is already allocated`

**Solutions**:
1. Check what's using port 8090:
   ```bash
   lsof -i :8090
   ```
2. Stop the other service or change port in `docker-compose.confluence.yml`:
   ```yaml
   ports:
     - "8099:8090"  # Access at http://localhost:8099
   ```

## Performance Tips

### Memory Management
- Default: 512MB minimum, 1024MB maximum JVM heap
- For large pages (>100KB): Increase to 1024MB/2048MB
- For test data only: Default is fine

### Database Performance
- PostgreSQL 15 Alpine is lightweight (~40MB)
- Named volumes persist data between restarts
- Initial startup slower due to schema creation

### Network Configuration
- Services communicate via `confluence-network` bridge
- From DataPilotFlow container: Use `http://confluence:8090`
- From host machine: Use `http://localhost:8090`

### Cleanup
- Remove volumes with `-v` flag to start fresh:
  ```bash
  docker-compose -f docker/confluence/docker-compose.confluence.yml down -v
  ```
- Takes 60-90 seconds on next start for database initialization

## Architecture

```
┌─────────────────────────────────────────┐
│         DataPilotFlow API               │
│  (running on host or in Docker)         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    confluence-network (Docker bridge)   │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Confluence Server               │  │
│  │  - Port: 8090 (mapped)           │  │
│  │  - Data: confluence-home volume  │  │
│  │  - JVM: 512MB-1024MB             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  PostgreSQL 15                   │  │
│  │  - Port: 5432 (mapped)           │  │
│  │  - Data: confluence-db-data vol. │  │
│  │  - User: confluence              │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Files

### Configuration Files
- `docker/confluence/docker-compose.confluence.yml` - Main Docker Compose config
- `docker/confluence/confluence-init.sql` - Database initialization script

### Setup Scripts
- `confluence_test_data_setup.py` - Automated test data creation (TECH, DOCS, API spaces)

### Documentation
- `CONFLUENCE_DOCKER_SETUP.md` - This file
- `CONFLUENCE_MARKDOWN_GENERATION.md` - Markdown conversion implementation details

## Next Steps

### After Setup
1. ✅ Start Confluence with Docker
2. ✅ Complete initial setup wizard
3. ✅ Generate API token
4. ✅ Create test data with Python script
5. ✅ Test with DataPilotFlow

### For Development
1. Create custom test pages with specific Confluence macros
2. Test markdown conversion with edge cases
3. Verify extraction performance with large spaces
4. Test incremental updates and re-extraction

### Cleanup
When done testing:
```bash
# Stop and remove containers (keeps volumes)
docker-compose -f docker/confluence/docker-compose.confluence.yml down

# Full cleanup including data
docker-compose -f docker/confluence/docker-compose.confluence.yml down -v
```

## Support

### Documentation References
- [Confluence API Documentation](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796537.html)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)

### Common Issues
- Review logs: `docker-compose -f docker/confluence/docker-compose.confluence.yml logs`
- Check containers running: `docker-compose -f docker/confluence/docker-compose.confluence.yml ps`
- Verify network connectivity: `docker network ls`

## Status

- ✅ Docker Compose setup complete
- ✅ PostgreSQL database configured
- ✅ Health checks implemented
- ✅ Test data setup script created
- ✅ Markdown conversion integrated
- ✅ Full integration testing ready

Last Updated: 2025-12-26
Version: 1.0
