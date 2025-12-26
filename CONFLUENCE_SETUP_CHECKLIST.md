# Confluence Docker Setup - Verification Checklist

Quick verification that everything is set up and ready to use.

## Files Present ✅

- [x] `docker/confluence/docker-compose.confluence.yml` - Docker Compose config
- [x] `docker/confluence/confluence-init.sql` - Database init script
- [x] `confluence_test_data_setup.py` - Test data setup script (executable)
- [x] `CONFLUENCE_DOCKER_SETUP.md` - Complete setup guide
- [x] `CONFLUENCE_QUICK_REFERENCE.md` - Quick reference

## Setup Steps

### Step 1: Start Confluence (5 min)
```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow
docker-compose -f docker/confluence/docker-compose.confluence.yml up -d
```
- [ ] Confluence container started
- [ ] PostgreSQL container started
- [ ] Ports 8090 and 5432 accessible

### Step 2: Access Confluence (5 min)
- [ ] Visit http://localhost:8090
- [ ] Complete setup wizard (license, database, admin account)
- [ ] Create admin password

### Step 3: Generate API Token (5 min)
- [ ] Log in to Confluence
- [ ] Go to Settings → Admin → Users
- [ ] Find admin user, click Security
- [ ] Click "Create API token"
- [ ] Copy token and save safely

### Step 4: Create Test Data (2 min)
```bash
python3 confluence_test_data_setup.py \
  --url http://localhost:8090 \
  --username admin@example.com \
  --api-token YOUR_TOKEN_HERE
```
- [ ] Script runs without errors
- [ ] 3 spaces created (TECH, DOCS, API)
- [ ] 4 pages created with content

### Step 5: Verify in DataPilotFlow (10 min)
- [ ] Create Confluence credential
  - URL: http://localhost:8090
  - Username: admin@example.com
  - API Token: (from step 3)
- [ ] Create knowledge source
  - Content Source: Confluence
  - Credential: (from above)
  - Mode: Space Pages
  - Spaces: TECH, DOCS, API
  - Output Format: Markdown
- [ ] Execute extraction job
- [ ] Verify documents show Markdown content

## Troubleshooting

### Port 8090 not accessible
```bash
# Check containers are running
docker-compose -f docker/confluence/docker-compose.confluence.yml ps

# View Confluence logs
docker-compose -f docker/confluence/docker-compose.confluence.yml logs confluence

# Wait 60-90 seconds for full startup
```

### API Token not working
```bash
# Test with curl
curl -u admin@example.com:YOUR_TOKEN \
  http://localhost:8090/rest/api/user/current

# Should return user JSON, not 401 error
# If 401: Token may be invalid, create new one
```

### Port already in use
```bash
# Find what's using port 8090
lsof -i :8090

# Or use different port in docker-compose.confluence.yml
# Change "8090:8090" to "8099:8090"
# Then access at http://localhost:8099
```

## Commands Reference

```bash
# Start services
docker-compose -f docker/confluence/docker-compose.confluence.yml up -d

# View logs
docker-compose -f docker/confluence/docker-compose.confluence.yml logs -f confluence

# Stop services
docker-compose -f docker/confluence/docker-compose.confluence.yml down

# Full cleanup (remove volumes)
docker-compose -f docker/confluence/docker-compose.confluence.yml down -v

# Restart services
docker-compose -f docker/confluence/docker-compose.confluence.yml restart
```

## Performance Expectations

- **Startup time**: 60-90 seconds for Confluence to be ready
- **Test data creation**: 5-10 seconds
- **Extraction job**: 30-60 seconds for 3 spaces with 4 pages
- **Markdown conversion**: <50ms per page for test content

## Next Steps

After verification:
1. Run integration tests if needed
2. Test markdown conversion quality
3. Verify embeddings generation works
4. Check document retrieval functionality
5. Ready for staging deployment

---

**Quick Start Command:**
```bash
cd /Users/bassem.elsodany/workspaces/datapilotflow && \
docker-compose -f docker/confluence/docker-compose.confluence.yml up -d && \
echo "Confluence starting... wait 60-90 seconds then visit http://localhost:8090"
```
