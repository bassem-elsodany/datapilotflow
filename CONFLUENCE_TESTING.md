# Confluence Integration Testing Guide

## Overview

This document describes the comprehensive test suite for the Confluence API integration. The test suite covers unit tests, integration tests, and end-to-end tests across all layers of the system.

## Test Structure

### Unit Tests

#### Confluence API Client Tests
**File**: `datapilotflow-processors/tests/confluence/test_confluence_api_client.py`

Tests for the API client include:
- **Initialization**: Client setup and configuration
- **Credential Verification**: Basic Auth header construction and token verification
- **Space Pages Retrieval**: Fetching pages from spaces with pagination
- **Page by ID Retrieval**: Direct page access and error handling
- **Pages by Label**: Label-based searching
- **Recently Modified Pages**: Fetching recent updates
- **Rate Limiting**: Handling 429 responses and retry logic
- **Storage Format Conversion**: XHTML to Markdown conversion with edge cases
- **Error Handling**: Connection errors, timeouts, malformed responses

**Key Test Classes**:
- `TestConfluenceApiClientInitialization` - Client setup
- `TestVerifyCredentials` - Authentication validation
- `TestGetSpacePages` - Space retrieval with pagination
- `TestGetPageById` - Direct page access
- `TestGetPagesByLabel` - Label-based searches
- `TestGetRecentlyModifiedPages` - Recent pages
- `TestRateLimiting` - Rate limit handling
- `TestStorageFormatConversion` - XHTML conversion
- `TestErrorHandling` - Error scenarios

**Run Tests**:
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_api_client.py -v
```

#### Confluence Document Extractor Tests
**File**: `datapilotflow-processors/tests/confluence/test_confluence_document_extractor.py`

Tests for document extraction include:
- **Initialization**: Extractor setup with batch size configuration
- **Specific Pages Mode**: Extracting individual pages
- **Space Pages Mode**: Extracting all pages from spaces
- **Pages with Label Mode**: Label-based extraction
- **Recently Modified Mode**: Time-based extraction
- **Batch Processing**: Document batching and yields
- **Metadata Inclusion**: Required metadata fields
- **Error Handling**: Empty spaces, missing pages
- **Async Generator**: Proper async iterator behavior

**Key Test Classes**:
- `TestConfluenceDocumentExtractorInitialization` - Setup
- `TestExtractSpecificPages` - Page ID extraction
- `TestExtractSpacePages` - Space-level extraction
- `TestExtractPagesWithLabel` - Label extraction
- `TestExtractRecentlyModified` - Time-based extraction
- `TestBatchProcessing` - Batch size handling
- `TestDocumentMetadata` - Metadata validation
- `TestErrorHandling` - Error scenarios
- `TestAsyncGeneratorBehavior` - Generator protocol

**Run Tests**:
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_document_extractor.py -v
```

### Integration Tests

#### Confluence Credential Service Tests
**File**: `datapilotflow-services/tests/confluence/test_confluence_credential_service.py`

Tests for credential management include:
- **Credential Creation**: Creating new credentials with auto-verification
- **Credential Retrieval**: Getting credentials by ID
- **Credential Listing**: Listing user's credentials
- **Credential Updates**: Modifying existing credentials
- **Credential Deletion**: Removing credentials
- **Credential Verification**: Testing API connection
- **Activate/Deactivate**: Soft deletion operations
- **User Isolation**: Preventing cross-user access
- **Validation**: Data validation and constraints

**Key Test Classes**:
- `TestCreateCredential` - Credential creation
- `TestGetCredential` - Retrieval by ID
- `TestListCredentials` - Listing operations
- `TestUpdateCredential` - Updates
- `TestDeleteCredential` - Deletion
- `TestVerifyCredential` - Connection testing
- `TestActivateDeactivate` - State management
- `TestCredentialValidation` - Input validation

**Run Tests**:
```bash
pytest datapilotflow-services/tests/confluence/test_confluence_credential_service.py -v
```

#### Confluence DAO Tests
**File**: `datapilotflow-infrastructure/tests/confluence/test_confluence_dao.py`

Tests for data persistence include:
- **Credential DAO**: Create, read, update, delete, listing
- **Space Cache DAO**: Space metadata caching and retrieval
- **Page Cache DAO**: Page metadata caching with pagination
- **Token Encryption**: Encryption/decryption roundtrip
- **Bulk Operations**: Batch upserts for pages
- **Singleton Pattern**: DAO singleton instances
- **Error Handling**: Database operation errors

**Key Test Classes**:
- `TestConfluenceCredentialDAO` - Credential persistence
- `TestConfluenceSpaceDAO` - Space caching
- `TestConfluencePageDAO` - Page caching with pagination
- `TestDAOErrorHandling` - Error recovery

**Run Tests**:
```bash
pytest datapilotflow-infrastructure/tests/confluence/test_confluence_dao.py -v
```

### End-to-End Tests

#### Confluence Pipeline E2E Tests
**File**: `datapilotflow-processors/tests/confluence/test_confluence_e2e.py`

Tests for complete pipeline workflows include:
- **Complete Extraction**: Full workflow from config to documents
- **Multi-Space Extraction**: Extracting from multiple spaces
- **Large Batch Processing**: Handling 250+ pages efficiently
- **Metadata Consistency**: Metadata across batches
- **Mode-Specific Metadata**: Mode information in documents
- **Partial Failure Recovery**: Continuing after some failures
- **Timeout Handling**: Network timeout recovery
- **Empty Space Handling**: Handling spaces with no pages
- **Memory Efficiency**: Large dataset handling
- **API Call Efficiency**: Minimizing redundant API calls
- **Service Routing**: Integration with extraction service

**Key Test Classes**:
- `TestConfluencePipelineE2E` - Complete workflows
- `TestPipelineErrorRecovery` - Error handling
- `TestPipelinePerformance` - Performance characteristics
- `TestDocumentExtractionService` - Service routing

**Run Tests**:
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_e2e.py -v
```

## Running Test Suites

### All Confluence Tests
```bash
pytest datapilotflow-processors/tests/confluence/ \
        datapilotflow-services/tests/confluence/ \
        datapilotflow-infrastructure/tests/confluence/ -v
```

### Unit Tests Only
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_api_client.py \
        datapilotflow-processors/tests/confluence/test_confluence_document_extractor.py -v
```

### Integration Tests Only
```bash
pytest datapilotflow-services/tests/confluence/ \
        datapilotflow-infrastructure/tests/confluence/ -v
```

### E2E Tests Only
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_e2e.py -v
```

### With Coverage Report
```bash
pytest datapilotflow-processors/tests/confluence/ \
        datapilotflow-services/tests/confluence/ \
        datapilotflow-infrastructure/tests/confluence/ \
        --cov=datapilotflow.processors.confluence \
        --cov=datapilotflow.services.confluence \
        --cov=datapilotflow.infrastructure.dao.confluence \
        --cov-report=html
```

## Test Coverage Goals

### Target Coverage
- **Overall**: 85%+
- **API Client**: 90%+ (critical component)
- **Document Extractor**: 85%+
- **Services**: 80%+
- **DAOs**: 80%+

### Coverage by Component
```
datapilotflow/processors/confluence/
  - confluence_api_client.py: 90% target
  - confluence_document_extractor.py: 85% target
  - __init__.py: 100% target

datapilotflow/services/confluence/
  - confluence_credential_service.py: 80% target
  - confluence_metadata_service.py: 80% target
  - __init__.py: 100% target

datapilotflow/infrastructure/dao/confluence/
  - confluence_credential_dao.py: 85% target
  - confluence_space_dao.py: 80% target
  - confluence_page_dao.py: 85% target
  - __init__.py: 100% target
```

## Mock Fixtures

### API Client Fixtures
```python
@pytest.fixture
def confluence_config():
    """Complete Confluence configuration."""
    return {
        "cloud_url": "https://test.atlassian.net/wiki",
        "username_or_email": "test@example.com",
        "api_token": "test-token-123",
    }

@pytest.fixture
def sample_pages():
    """Sample Confluence pages for testing."""
    # Returns list of ConfluencePage objects
```

### Service Fixtures
```python
@pytest.fixture
def user_id():
    """Test user ID."""
    return str(uuid4())

@pytest.fixture
def credential_data():
    """Sample credential data."""
    # Returns dict with credential fields
```

### DAO Fixtures
```python
@pytest.fixture
def confluence_credential(user_id):
    """Sample credential for persistence tests."""
    # Returns ConfluenceCredential instance
```

## Error Scenarios Tested

### Authentication Errors
- Invalid credentials (401)
- Expired API token
- Missing authentication headers
- Malformed Basic Auth

### Rate Limiting
- 429 Too Many Requests
- Retry-After header handling
- Exponential backoff behavior

### Page Access Errors
- 404 Page Not Found
- 403 Forbidden (access denied)
- 500 Server Error
- Connection timeouts

### Data Errors
- Malformed API responses
- Missing required fields
- Invalid JSON responses
- Empty result sets

### Validation Errors
- Invalid Confluence URL format
- Missing required configuration fields
- Invalid credential data
- Concurrent credential conflicts

## Best Practices

### Test Organization
- One test class per major component
- Clear test names describing what is being tested
- Arrange-Act-Assert (AAA) pattern

### Mocking Strategy
- Mock external API calls (ConfluenceApiClient)
- Mock database operations (DAOs)
- Use AsyncMock for async operations
- Verify mock calls to ensure correct behavior

### Async Testing
- Use `@pytest.mark.asyncio` decorator
- Use AsyncMock for async methods
- Test async generator behavior
- Verify proper awaiting of coroutines

### Fixtures
- Use parametrized fixtures for multiple variations
- Create fixtures at appropriate scope
- Clean up resources in fixture teardown
- Document fixture purpose

## Continuous Integration

### GitHub Actions Configuration
Tests should run automatically on:
- Pull requests to main branch
- Commits to main branch
- Manual workflow dispatch

### Test Requirements
- All tests must pass
- Minimum 80% code coverage
- No deprecation warnings
- No flaky tests

### Pre-commit Hooks
```bash
# Run tests before commit
pytest datapilotflow-processors/tests/confluence/ \
        datapilotflow-services/tests/confluence/ \
        datapilotflow-infrastructure/tests/confluence/
```

## Debugging Tests

### Verbose Output
```bash
pytest datapilotflow-processors/tests/confluence/ -vv
```

### Show Print Statements
```bash
pytest datapilotflow-processors/tests/confluence/ -s
```

### Stop on First Failure
```bash
pytest datapilotflow-processors/tests/confluence/ -x
```

### Run Specific Test
```bash
pytest datapilotflow-processors/tests/confluence/test_confluence_api_client.py::TestVerifyCredentials::test_verify_credentials_success -v
```

### Debug with pdb
```bash
pytest datapilotflow-processors/tests/confluence/ --pdb
```

## Test Maintenance

### Regular Updates
- Update tests when API contract changes
- Add tests for new features
- Remove tests for deprecated functionality
- Refresh mock responses with actual API behavior

### Performance Monitoring
- Track test execution time
- Identify slow tests
- Optimize database mocks
- Consider test parallelization

### Documentation
- Maintain clear test documentation
- Document complex mocking scenarios
- Explain non-obvious test assertions
- Keep this guide updated

## Future Enhancements

### Additional Test Coverage
- UI component tests for Confluence credential management
- API endpoint integration tests
- Pipeline factory routing tests
- Event handler tests

### Performance Tests
- Load testing with many credentials
- Stress testing with large spaces
- Memory profiling for batch processing
- Database query performance tests

### Security Tests
- Token encryption/decryption verification
- User isolation enforcement
- Permission boundary tests
- SQL injection prevention tests

## Support

For test-related issues:
1. Check this documentation
2. Review test examples in test files
3. Consult pytest documentation
4. Check pytest-asyncio documentation for async tests

## Summary

The Confluence integration test suite provides comprehensive coverage across:
- 40+ unit tests for API client and extractor
- 30+ integration tests for services and DAOs
- 10+ end-to-end tests for complete workflows

Total: 80+ test cases covering all major functionality and error scenarios.
