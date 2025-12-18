# MuleSoft Technical Assistant - User Query Examples

This document provides realistic examples of user queries that the MuleSoft Technical Assistant can handle. Use these to test and validate the agent's capabilities.

---

## 1. Basic Flow Generation

```
Create a simple REST API endpoint that returns Hello World

I need an HTTP listener that accepts POST requests and logs the payload

Build a flow that queries a PostgreSQL database and returns results as JSON

Create an API that receives XML input and converts it to JSON

I need a flow that reads a CSV file and processes each row

Generate a flow with HTTP listener on port 8081 at path /api/users

Create a simple proxy that forwards requests to another API

I need a flow that responds with static JSON data
```

---

## 2. DataWeave Transformations

```
How do I transform this JSON structure to flatten nested arrays?

I need to map customer data from API format to database format

Help me write DataWeave to filter an array where status equals 'active'

How do I combine two arrays in DataWeave and remove duplicates?

I need to convert ISO date strings to MM/DD/YYYY format

How do I handle null values in DataWeave transformations?

Group an array of orders by customer ID using DataWeave

Transform XML payload to JSON with field mapping

I need to merge two JSON objects in DataWeave

How do I extract specific fields from nested JSON structure?

Calculate sum of all order amounts using DataWeave reduce

Remove empty or null fields from JSON output

Convert string array to comma-separated string

How do I sort an array by date field in descending order?
```

---

## 3. Integration Patterns

```
I need to call three external APIs in parallel and combine their responses

How do I implement scatter-gather pattern for calling multiple services?

Create a flow that processes 10,000 records from a database in batches

I need to route messages to different endpoints based on payload content

Implement a choice router that sends to API A if country is US, otherwise API B

How do I implement retry logic for failed API calls?

I need async processing - call an API without waiting for response

Create a flow that fans out to multiple systems and aggregates results

I need round-robin load balancing across three backend services

Implement content-based routing based on message type

How do I use Until Successful for retrying operations?

Create a flow that processes messages from a queue asynchronously
```

---

## 4. Database Operations

```
Create a flow that inserts records into MySQL database

I need to update customer records in PostgreSQL based on email

How do I perform a JOIN query across two database tables?

Create an API that does CRUD operations on a database table

I need bulk insert - insert 5000 records efficiently

How do I handle database connection pooling?

Query Oracle database and transform results to JSON

I need to call a stored procedure with parameters

Create a flow that does upsert (insert or update)

How do I execute multiple database operations in a transaction?

Query database with dynamic WHERE clause from request parameters

I need to paginate database results - 50 records per page
```

---

## 5. Error Handling

```
Add error handling to catch database connection failures

How do I implement global error handler for all flows?

I need to retry failed operations 3 times with exponential backoff

What's the difference between on-error-continue and on-error-propagate?

How do I handle partial failures in scatter-gather?

I need to log errors and return custom error messages to clients

Create a flow with graceful degradation - return cached data if API fails

How do I catch specific error types like HTTP 404 or 500?

I need to transform errors into a standard error response format

Implement circuit breaker pattern for failing external service

How do I rollback database transaction on error?

Add error handling that sends alerts on critical failures
```

---

## 6. File Processing

```
Read a CSV file, transform each row, and write to database

I need to process large XML files without loading entire file in memory

Create a flow that monitors a folder and processes new files

How do I split a large file into smaller chunks?

Read Excel file and convert to JSON

I need to write JSON data to a file on SFTP server

Process files from S3 bucket and upload results back

How do I read files with different encodings (UTF-8, ISO-8859-1)?

Create a flow that archives processed files to a different folder

I need to merge multiple CSV files into one

Read JSON file line by line and process each record

Generate PDF report from database data
```

---

## 7. API Integration

```
Call a REST API with OAuth 2.0 authentication

I need to consume a SOAP web service and convert response to JSON

How do I add API key authentication to HTTP requests?

Create a flow that calls an external API with retry on 5xx errors

I need to handle rate limiting from external API - wait and retry

How do I send multipart form data to an API?

Call external API with custom headers and query parameters

I need to implement Basic Authentication for HTTP requests

How do I handle API pagination - get all pages of results?

Create a flow that polls an API every 5 minutes for new data

I need to send webhook notifications to external systems

Call GraphQL API and process the response
```

---

## 8. Performance & Optimization

```
How do I optimize this flow for high throughput?

My DataWeave transformation is slow with large payloads - help optimize

Should I use batch processing or foreach for 50,000 records?

How do I implement caching for expensive API calls?

I need to process messages asynchronously to improve response time

What's the best way to handle large file uploads?

How do I configure thread pools for better performance?

I need to stream large responses instead of loading in memory

How do I implement connection pooling for database queries?

Optimize DataWeave to avoid nested map operations

What's the recommended batch size for database operations?

How do I use parallel processing with scatter-gather?
```

---

## 9. Configuration & Best Practices

```
How should I structure my global configurations?

What's the best practice for managing environment-specific properties?

How do I externalize database credentials?

Show me how to configure connection pooling for HTTP requests

What are the naming conventions for flows and configurations?

How do I organize multiple flows in one application?

How do I secure sensitive configuration values?

What's the recommended way to structure error handlers?

How do I implement logging best practices?

Show me how to configure timeout values for HTTP requests

How do I set up multiple environments (dev, test, prod)?

What's the best way to handle API versioning?
```

---

## 10. Complex Scenarios

```
I need an order processing system: receive order, validate, check inventory, call payment API, update database, send confirmation email

Create a data synchronization flow that runs every hour, queries database A, transforms data, and upserts into database B

Build a webhook receiver that validates signature, processes payload, stores in database, and triggers downstream processes

I need a file ingestion pipeline: read from SFTP, validate format, transform, split into batches, load to database

Implement a circuit breaker pattern - stop calling failed service for 5 minutes

Create an event-driven architecture with message queues and async processing

Build a real-time data pipeline: receive events, enrich with API calls, transform, write to data warehouse

I need a middleware that aggregates data from 5 different systems and provides unified API

Create a microservices orchestration layer that handles service discovery and routing

Build an ETL pipeline with data validation, transformation, and error recovery

Implement saga pattern for distributed transactions across multiple services

Create a multi-tenant API gateway with tenant-specific routing
```

---

## 11. Troubleshooting & Debugging

```
My flow is throwing 'Payload is not JSON' error - how do I fix it?

Database connection keeps timing out - what should I check?

Getting 'null pointer exception' in DataWeave - how do I debug?

My scatter-gather is failing when one route has error - how to handle?

HTTP request returning 401 Unauthorized - how to debug authentication?

Why is my batch job processing only 100 records instead of all?

I'm getting memory out of heap error with large files - how to fix?

DataWeave transformation is failing with 'Unable to coerce' error

My flow is running slowly - how do I identify bottlenecks?

Getting connection refused error when calling external API

Why are my variable values not persisting between processors?

My foreach is not iterating over all items - what's wrong?
```

---

## 12. Specific MuleSoft Components

```
How do I use the Object Store to share data between flows?

Explain how to use Until Successful scope with retry configuration

I need to use VM connector for decoupling flows - show me an example

How does the Choice router work? Show me a practical example

What's the difference between Async scope and VM queue?

How do I use watermark for incremental database queries?

Show me how to use the Scheduler component for recurring jobs

How do I implement request-reply pattern with VM queues?

Explain how to use the Validation module to validate JSON schema

How do I use the Aggregator pattern to collect responses?

Show me how to configure the HTTP Request connector with connection pooling

How do I use the Idempotent Message Validator?
```

---

## 13. Testing & Validation

```
How do I test this flow locally before deploying?

What's the best way to mock external API responses during development?

I need to validate incoming JSON against a schema

How do I set up test data for database queries?

Show me how to add logging at each step for debugging

How do I unit test DataWeave transformations?

What's the best way to simulate error conditions for testing?

How do I validate XML against XSD schema?

I need to test batch processing with sample data

How do I verify database transactions in testing?

Show me how to test async flows

How do I validate API responses match expected format?
```

---

## 14. Questions About Best Practices

```
When should I use batch processing vs regular foreach?

What's the recommended way to handle large payloads?

How do I structure a MuleSoft application for microservices?

What are the security best practices for API development?

How should I handle versioning in MuleSoft APIs?

What's the difference between stateless and stateful flows?

When should I use synchronous vs asynchronous processing?

What's the best practice for error logging and monitoring?

How do I design APIs for high availability?

What's the recommended approach for data transformation layers?

How should I organize flows in a large enterprise application?

What are the best practices for managing API dependencies?
```

---

## 15. Real-World Use Cases

```
Build a Salesforce to Database sync - get updated records every 15 minutes

Create an ETL pipeline for migrating data from legacy system to cloud

I need a middleware layer that transforms between two different ERP systems

Build an API gateway that routes requests to different microservices

Create a notification service that sends emails and SMS based on events

Implement an audit logging system that captures all API transactions

Build a customer 360 view by aggregating data from CRM, billing, and support systems

Create a real-time inventory sync between e-commerce platform and warehouse system

Build a payment processing orchestration layer with multiple payment providers

Implement a data replication system between on-premise and cloud databases

Create an order fulfillment workflow with multiple third-party integrations

Build a master data management solution that syncs customer data across systems
```

---

## 16. Batch Processing

```
Process 1 million records from database in batches of 1000

How do I implement batch job with commit and rollback?

I need to read large CSV file and process in batches

Create a batch flow with on-complete phase for cleanup

How do I track batch job progress and failures?

I need batch processing with parallel processing of records

How do I filter records in batch accept phase?

Create a batch job that processes files from a directory

How do I handle partial batch failures?

I need to aggregate batch results and send summary email

How do I schedule batch jobs to run daily at midnight?

Create a batch flow with custom aggregator
```

---

## 17. Message Routing

```
Route messages to different queues based on priority

I need content-based routing using message headers

Create a router that distributes load across multiple endpoints

How do I implement message filtering based on criteria?

Route messages to different processors based on message type

I need a dynamic router that reads routing rules from database

Create a multicast router that sends to all endpoints

How do I implement recipient list pattern?

Route messages based on regex pattern matching

I need conditional routing with default fallback endpoint

Create a router that validates before routing

How do I route based on time of day or business rules?
```

---

## 18. Security & Authentication

```
How do I implement OAuth 2.0 client credentials flow?

I need to validate JWT tokens in incoming requests

How do I encrypt sensitive data in payload?

Show me how to implement API key authentication

I need to add HMAC signature validation for webhooks

How do I implement role-based access control?

Show me how to use secure properties for passwords

How do I implement TLS/SSL for HTTP connections?

I need to validate IP whitelist for incoming requests

How do I implement basic authentication with encoded credentials?

Show me how to hash passwords before storing in database

How do I implement SAML authentication?
```

---

## 19. Monitoring & Logging

```
Add comprehensive logging to track flow execution

How do I log request and response payloads?

I need to send metrics to external monitoring system

Create custom log format with correlation IDs

How do I implement request tracing across multiple flows?

I need to log only errors with full stack trace

How do I measure flow execution time and performance?

Create alerts when error rate exceeds threshold

How do I implement structured logging with JSON format?

I need to log to both file and external logging service

How do I mask sensitive data in logs?

Create dashboards for API usage and performance metrics
```

---

## 20. Advanced Patterns

```
Implement event sourcing pattern for audit trail

Create a saga pattern for distributed transactions

How do I implement CQRS pattern with read and write models?

Build a message queue consumer with dead letter handling

Implement bulkhead pattern for resource isolation

Create a throttling mechanism to limit request rate

How do I implement priority queue processing?

Build a request aggregation pattern - batch multiple requests

Implement compensating transaction for rollback

Create a service mesh with retry and circuit breaker

How do I implement the strangler pattern for legacy migration?

Build a publish-subscribe pattern with topic-based routing
```

---

## Usage Tips

### Simple Queries
- Direct, single-task requests
- Clear about what component or feature is needed
- Example: "Create a flow that [does X]"

### Complex Queries
- Multi-step workflows
- Integration of multiple systems
- Example: "Build a pipeline that reads from [source], transforms to [format], and writes to [destination]"

### Troubleshooting Queries
- Include error message or symptom
- Describe expected vs actual behavior
- Example: "I'm getting [error] when [doing X] - how to fix?"

### Best Practice Queries
- Ask for guidance on approach
- Compare different patterns
- Example: "What's the best way to [achieve X]?"

---

**Note:** The MuleSoft Technical Assistant will use the toolkit examples and knowledge_expert to answer these queries, generating production-ready code with proper error handling, configuration, and best practices.

