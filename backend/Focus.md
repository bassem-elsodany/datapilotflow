# Project Focus: backend

**Current Goal:** Project directory structure and information

**Project Context:**
Type: Language: python
Target Users: Users of backend
Main Functionality: Project directory structure and information
Key Requirements:
- Type: Python Project
- Language: python
- Framework: docker
- File and directory tracking
- Automatic updates

**Development Guidelines:**
- Keep code modular and reusable
- Follow best practices for the project type
- Maintain clean separation of concerns

# 📁 Project Structure
├─ 📄 run_all_event_listeners.py (273 lines) - Python script containing project logic
├─ 📄 run_api_server.py (28 lines) - Python script containing project logic
├─ 📄 run_file_listener.py (32 lines) - Python script containing project logic
├─ 📄 run_file_upload_event_listener.py (59 lines) - Python script containing project logic
├─ 📄 run_job_event_listener.py (59 lines) - Python script containing project logic
├─ 📄 run_notification_event_listener.py (59 lines) - Python script containing project logic
├─ 📄 run_notification_listener.py (33 lines) - Python script containing project logic
├─ 📄 run_notification_websocket_service.py (46 lines) - Python script containing project logic
├─ 📄 run_process_cleanup_service.py (35 lines) - Python script containing project logic
├─ 📄 run_timeline_event_listener.py (62 lines) - Python script containing project logic
├─ 📁 postman
│  └─ 📄 setup_postman_collection.js (164 lines) - JavaScript file for client-side functionality
├─ 📁 src
│  ├─ 📄 __init__.py (9 lines) - Python script containing project logic
│  ├─ 📄 api_server.py (198 lines) - Python script containing project logic
│  ├─ 📄 config.py (341 lines) - Python script containing project logic
│  ├─ 📁 api
│  │  ├─ 📄 __init__.py (10 lines) - Python script containing project logic
│  │  ├─ 📄 constants.py (19 lines) - Python script containing project logic
│  │  └─ 📁 routers
│  │     └─ 📄 __init__.py (31 lines) - Python script containing project logic
│  ├─ 📁 application
│  │  ├─ 📄 __init__.py (17 lines) - Python script containing project logic
│  │  ├─ 📁 conversation
│  │  │  ├─ 📄 __init__.py (3 lines) - Python script containing project logic
│  │  │  ├─ 📄 graph_response_handler.py (322 lines) - Python script containing project logic
│  │  │  └─ 📄 reset_conversation_state.py (156 lines) - Python script containing project logic
│  │  ├─ 📁 data
│  │  │  ├─ 📄 __init__.py (77 lines) - Python script containing project logic
│  │  │  └─ 📄 deduplicate_documents.py (106 lines) - Python script containing project logic
│  │  └─ 📁 rag
│  │     ├─ 📄 __init__.py (5 lines) - Python script containing project logic
│  │     ├─ 📄 retrievers.py (397 lines) - Python script containing project logic
│  │     └─ 📄 splitters.py (28 lines) - Python script containing project logic
│  ├─ 📁 domain
│  │  ├─ 📄 __init__.py (34 lines) - Python script containing project logic
│  │  ├─ 📁 core
│  │  │  ├─ 📄 __init__.py (21 lines) - Python script containing project logic
│  │  │  └─ 📄 exceptions.py (179 lines) - Python script containing project logic
│  │  ├─ 📁 embedding
│  │  │  ├─ 📄 __init__.py (13 lines) - Python script containing project logic
│  │  │  └─ 📄 embedding_model.py (47 lines) - Python script containing project logic
│  │  ├─ 📁 events
│  │  │  ├─ 📄 __init__.py (41 lines) - Python script containing project logic
│  │  │  ├─ 📄 base.py (198 lines) - Python script containing project logic
│  │  │  ├─ 📄 job_events.py (145 lines) - Python script containing project logic
│  │  │  └─ 📄 timeline_events.py (73 lines) - Python script containing project logic
│  │  ├─ 📁 generative
│  │  │  ├─ 📄 __init__.py (13 lines) - Python script containing project logic
│  │  │  └─ 📄 generative_model.py (47 lines) - Python script containing project logic
│  │  ├─ 📁 knowledge
│  │  │  ├─ 📄 __init__.py (49 lines) - Python script containing project logic
│  │  │  ├─ 📄 job_timeline.py (81 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge.py (126 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_factory.py (7 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_job.py (105 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_source_config.py (121 lines) - Python script containing project logic
│  │  │  └─ 📄 vectordb_collection.py (66 lines) - Python script containing project logic
│  │  ├─ 📁 llm_prompts
│  │  │  ├─ 📄 __init__.py (52 lines) - Python script containing project logic
│  │  │  ├─ 📄 ai_responses.py (47 lines) - Python script containing project logic
│  │  │  ├─ 📄 base.py (54 lines) - Python script containing project logic
│  │  │  ├─ 📄 conversation.py (264 lines) - Python script containing project logic
│  │  │  └─ 📄 knowledge_base.py (75 lines) - Python script containing project logic
│  │  ├─ 📁 model_provider
│  │  │  ├─ 📄 __init__.py (21 lines) - Python script containing project logic
│  │  │  └─ 📄 model_provider.py (212 lines) - Python script containing project logic
│  │  ├─ 📁 notification
│  │  │  ├─ 📄 __init__.py (23 lines) - Python script containing project logic
│  │  │  └─ 📄 notification.py (119 lines) - Python script containing project logic
│  │  ├─ 📁 process
│  │  │  └─ 📄 process_registry.py (98 lines) - Python script containing project logic
│  │  ├─ 📁 rag
│  │  │  ├─ 📄 __init__.py (24 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_chunk.py (42 lines) - Python script containing project logic
│  │  │  ├─ 📄 rag_file_upload.py (132 lines) - Python script containing project logic
│  │  │  └─ 📄 weaviate_chunk.py (49 lines) - Python script containing project logic
│  │  └─ 📁 user
│  │     ├─ 📄 __init__.py (19 lines) - Python script containing project logic
│  │     ├─ 📄 role_model.py (125 lines) - Python script containing project logic
│  │     ├─ 📄 roles.py (132 lines) - Python script containing project logic
│  │     └─ 📄 user.py (96 lines) - Python script containing project logic
│  ├─ 📁 handlers
│  │  └─ 📄 timeline_event_handler.py (95 lines) - Python script containing project logic
│  ├─ 📁 infrastructure
│  │  ├─ 📄 __init__.py (11 lines) - Python script containing project logic
│  │  ├─ 📄 opik_utils.py (61 lines) - Python script containing project logic
│  │  ├─ 📁 milvus
│  │  │  ├─ 📄 __init__.py (12 lines) - Python script containing project logic
│  │  │  ├─ 📄 client.py (607 lines) - Python script containing project logic
│  │  │  ├─ 📄 examples.py (218 lines) - Python script containing project logic
│  │  │  ├─ 📄 indexes.py (249 lines) - Python script containing project logic
│  │  │  └─ 📄 utils.py (441 lines) - Python script containing project logic
│  │  ├─ 📁 mongo
│  │  │  ├─ 📄 __init__.py (12 lines) - Python script containing project logic
│  │  │  ├─ 📄 client.py (258 lines) - Python script containing project logic
│  │  │  └─ 📄 indexes.py (30 lines) - Python script containing project logic
│  │  └─ 📁 utils
│  │     ├─ 📄 __init__.py (6 lines) - Python script containing project logic
│  │     └─ 📄 notification_utils.py (207 lines) - Python script containing project logic
│  ├─ 📁 processors
│  │  ├─ 📄 __init__.py (19 lines) - Python script containing project logic
│  │  ├─ 📁 crawler
│  │  │  ├─ 📄 __init__.py (16 lines) - Python script containing project logic
│  │  │  ├─ 📄 crawler_config.py (140 lines) - Python script containing project logic
│  │  │  └─ 📄 crawler_processor.py (356 lines) - Python script containing project logic
│  │  ├─ 📁 document
│  │  │  ├─ 📄 __init__.py (37 lines) - Python script containing project logic
│  │  │  ├─ 📄 base_processor.py (199 lines) - Python script containing project logic
│  │  │  ├─ 📄 file_processor.py (796 lines) - Python script containing project logic
│  │  │  └─ 📄 web_document_processor.py (429 lines) - Python script containing project logic
│  │  ├─ 📁 file_upload
│  │  │  ├─ 📄 __init__.py (13 lines) - Python script containing project logic
│  │  │  └─ 📄 file_upload_processor.py (227 lines) - Python script containing project logic
│  │  ├─ 📁 knowledge_job
│  │  │  ├─ 📄 __init__.py (16 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_job_event_processor.py (217 lines) - Python script containing project logic
│  │  │  └─ 📄 knowledge_job_processor.py (559 lines) - Python script containing project logic
│  │  └─ 📁 notifications
│  │     ├─ 📄 __init__.py (13 lines) - Python script containing project logic
│  │     └─ 📄 notification_processor.py (67 lines) - Python script containing project logic
│  ├─ 📁 services
│  │  ├─ 📄 __init__.py (40 lines) - Python script containing project logic
│  │  ├─ 📁 auth
│  │  │  ├─ 📄 __init__.py (22 lines) - Python script containing project logic
│  │  │  ├─ 📄 admin_initialization_service.py (133 lines) - Python script containing project logic
│  │  │  └─ 📄 auth_service.py (425 lines) - Python script containing project logic
│  │  ├─ 📁 conversation
│  │  │  ├─ 📄 __init__.py (16 lines) - Python script containing project logic
│  │  │  └─ 📄 conversation_history_service.py (422 lines) - Python script containing project logic
│  │  ├─ 📁 events
│  │  │  ├─ 📄 __init__.py (77 lines) - Python script containing project logic
│  │  │  └─ 📄 constants.py (65 lines) - Python script containing project logic
│  │  ├─ 📁 events_listeners
│  │  │  ├─ 📄 __init__.py (42 lines) - Python script containing project logic
│  │  │  ├─ 📄 base_event_listener.py (233 lines) - Python script containing project logic
│  │  │  ├─ 📄 file_upload_event_listener.py (92 lines) - Python script containing project logic
│  │  │  ├─ 📄 job_event_listener.py (159 lines) - Python script containing project logic
│  │  │  ├─ 📄 notification_event_listener.py (87 lines) - Python script containing project logic
│  │  │  └─ 📄 timeline_event_listener.py (199 lines) - Python script containing project logic
│  │  ├─ 📁 events_publisher
│  │  │  ├─ 📄 __init__.py (21 lines) - Python script containing project logic
│  │  │  ├─ 📄 base_event_publisher.py (174 lines) - Python script containing project logic
│  │  │  ├─ 📄 file_upload_event_publisher.py (81 lines) - Python script containing project logic
│  │  │  ├─ 📄 job_event_publisher.py (84 lines) - Python script containing project logic
│  │  │  └─ 📄 notification_event_publisher.py (81 lines) - Python script containing project logic
│  │  ├─ 📁 file_management
│  │  │  ├─ 📄 __init__.py (19 lines) - Python script containing project logic
│  │  │  └─ 📄 file_upload_service.py (128 lines) - Python script containing project logic
│  │  ├─ 📁 knowledge
│  │  │  ├─ 📄 __init__.py (31 lines) - Python script containing project logic
│  │  │  ├─ 📄 job_timeline_service.py (171 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_ingestion_service.py (84 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_job_service.py (333 lines) - Python script containing project logic
│  │  │  ├─ 📄 knowledge_source_service.py (128 lines) - Python script containing project logic
│  │  │  └─ 📄 vectordb_collection_service.py (139 lines) - Python script containing project logic
│  │  ├─ 📁 model_provider
│  │  │  ├─ 📄 __init__.py (7 lines) - Python script containing project logic
│  │  │  ├─ 📄 model_provider_initialization_service.py (354 lines) - Python script containing project logic
│  │  │  └─ 📄 model_provider_service.py (164 lines) - Python script containing project logic
│  │  ├─ 📁 notification
│  │  │  ├─ 📄 __init__.py (35 lines) - Python script containing project logic
│  │  │  ├─ 📄 notification_event_service.py (335 lines) - Python script containing project logic
│  │  │  ├─ 📄 notification_listener_service.py (257 lines) - Python script containing project logic
│  │  │  └─ 📄 notification_websocket_service.py (145 lines) - Python script containing project logic
│  │  ├─ 📁 process
│  │  │  ├─ 📄 __init__.py (21 lines) - Python script containing project logic
│  │  │  ├─ 📄 process_assignment_service.py (265 lines) - Python script containing project logic
│  │  │  ├─ 📄 process_cleanup_service.py (162 lines) - Python script containing project logic
│  │  │  ├─ 📄 process_heartbeat_service.py (123 lines) - Python script containing project logic
│  │  │  └─ 📄 process_registry_service.py (265 lines) - Python script containing project logic
│  │  ├─ 📁 rag
│  │  │  └─ 📄 __init__.py (13 lines) - Python script containing project logic
│  │  ├─ 📁 users
│  │  │  ├─ 📄 __init__.py (10 lines) - Python script containing project logic
│  │  │  ├─ 📄 roles_service.py (322 lines) - Python script containing project logic
│  │  │  └─ 📄 user_service.py (284 lines) - Python script containing project logic
│  │  └─ 📁 websocket
│  │     └─ 📄 __init__.py (13 lines) - Python script containing project logic
│  └─ 📁 workflow
│     ├─ 📄 __init__.py (5 lines) - Python script containing project logic
│     ├─ 📄 graph.py (132 lines) - Python script containing project logic
│     ├─ 📄 state.py (84 lines) - Python script containing project logic
│     ├─ 📁 nodes
│     │  ├─ 📄 __init__.py (19 lines) - Python script containing project logic
│     │  ├─ 📄 answer_generator.py (75 lines) - Python script containing project logic
│     │  ├─ 📄 document_judger.py (95 lines) - Python script containing project logic
│     │  ├─ 📄 document_retriever.py (63 lines) - Python script containing project logic
│     │  └─ 📄 query_rewriter.py (70 lines) - Python script containing project logic
│     ├─ 📁 prompts
│     │  ├─ 📄 __init__.py (22 lines) - Python script containing project logic
│     │  ├─ 📄 base_prompt.py (36 lines) - Python script containing project logic
│     │  ├─ 📄 generation_prompts.py (50 lines) - Python script containing project logic
│     │  ├─ 📄 judge_prompts.py (55 lines) - Python script containing project logic
│     │  └─ 📄 rewrite_prompts.py (30 lines) - Python script containing project logic
│     └─ 📁 tools
│        ├─ 📄 __init__.py (27 lines) - Python script containing project logic
│        └─ 📄 retrieval_tools.py (525 lines) - Python script containing project logic
└─ 📁 tools
   ├─ 📄 __init__.py (42 lines) - Python script containing project logic
   ├─ 📄 call_agent.py (62 lines) - Python script containing project logic
   ├─ 📄 create_long_term_memory.py (30 lines) - Python script containing project logic
   ├─ 📄 delete_long_term_memory.py (54 lines) - Python script containing project logic
   ├─ 📁 core
   │  ├─ 📄 __init__.py (16 lines) - Python script containing project logic
   │  ├─ 📄 create_long_term_memory.py (276 lines) - Python script containing project logic
   │  ├─ 📄 delete_long_term_memory.py (73 lines) - Python script containing project logic
   │  └─ 📄 run_extraction.py (144 lines) - Python script containing project logic
   ├─ 📁 data
   │  ├─ 📄 __init__.py (18 lines) - Python script containing project logic
   │  └─ 📄 extract_nav_urls.py (82 lines) - Python script containing project logic
   ├─ 📁 examples
   │  ├─ 📄 __init__.py (13 lines) - Python script containing project logic
   │  ├─ 📄 batch_extraction_example.py (205 lines) - Python script containing project logic
   │  └─ 📄 example_mongo_schemas.py (260 lines) - Python script containing project logic
   ├─ 📁 search
   │  └─ 📄 __init__.py (13 lines) - Python script containing project logic
   ├─ 📁 testing
   │  ├─ 📄 __init__.py (14 lines) - Python script containing project logic
   │  └─ 📄 run_tests.py (32 lines) - Python script containing project logic
   └─ 📁 tests
      ├─ 📄 __init__.py (8 lines) - Python script containing project logic
      ├─ 📄 analyze_graph_data.py (219 lines) - Python script containing project logic
      ├─ 📄 run_tests.py (243 lines) - Python script containing project logic
      ├─ 📄 test_document_splitting.py (417 lines) - Python script containing project logic
      ├─ 📄 test_file_saving.py (319 lines) - Python script containing project logic
      ├─ 📄 test_graph_data_in_results.py (70 lines) - Python script containing project logic
      ├─ 📄 test_llm_memory_fix.py (119 lines) - Python script containing project logic
      ├─ 📄 test_llm_server.py (86 lines) - Python script containing project logic
      ├─ 📄 test_memory_optimization.py (148 lines) - Python script containing project logic
      └─ 📄 test_sync_llm.py (102 lines) - Python script containing project logic

# 🔍 Key Files with Methods

`src/services/auth/admin_initialization_service.py` (133 lines)
Functions:
- AdminInitializationService
- get_admin_initialization_service
- initialize_admin_user_if_needed
- initialize_system_if_needed
- initialize_system_roles_if_needed

`tools/tests/analyze_graph_data.py` (219 lines)
Functions:
- analyze_hierarchy
- analyze_links
- analyze_pages
- generate_graph_insights
- load_graph_data
- main
- values

`src/workflow/nodes/answer_generator.py` (75 lines)
Functions:
- answer_generator

`src/api_server.py` (198 lines)
Functions:
- global_exception_handler
- health_check
- http_exception_handler
- initialize_system_if_needed
- lifespan
- root
- signal_handler

`src/services/auth/auth_service.py` (425 lines)
Functions:
- AuthService
- authenticate_user
- change_user_password
- check_email_exists
- check_username_exists
- create_access_token
- create_password_reset_token
- decode_access_token
- delete_user
- get_all_users
- get_user_by_email
- get_user_by_id
- get_user_by_username
- get_users_count
- invalidate_password_reset_token
- invalidate_token
- register_user
- update_user_profile
- validate_password_reset_token
- validate_token_and_get_user

`src/domain/llm_prompts/base.py` (54 lines)
Functions:
- Prompt
- prompt

`src/domain/events/base.py` (198 lines)
Functions:
- Config
- DomainEvent
- EventDispatcher
- EventHandler
- can_handle
- clear_handlers
- dispatch
- dispatch_event
- dispatch_events
- dispatch_multiple
- get_event_dispatcher
- get_handlers_for_event
- handle
- register_handler
- register_handlers

`src/services/events_listeners/base_event_listener.py` (233 lines)
Functions:
- BaseEventListener
- _get_connection_url
- _process_message
- handle_event
- process
- setup_queues
- start_listening
- stop_listening
- str

`src/services/events_publisher/base_event_publisher.py` (174 lines)
Functions:
- BaseEventPublisher
- _get_connection_url
- publish_event
- publish_specific_event
- publish_to_dlq

`src/processors/document/base_processor.py` (199 lines)
Functions:
- BaseDocumentProcessor
- extract_documents
- process_documents_with_batch_callback

`src/workflow/prompts/base_prompt.py` (36 lines)
Functions:
- Prompt
- prompt

`tools/examples/batch_extraction_example.py` (205 lines)
Functions:
- batch_callback_example
- callback_example
- generator_example
- main
- that
- traditional_example

`tools/call_agent.py` (62 lines)
Functions:
- async_command
- get_streaming_response
- main
- wrapper

`src/infrastructure/mongo/client.py` (258 lines)
Functions:
- MongoClientWrapper
- User
- _parse_single_document
- clear_collection
- close_mongo_client
- documents
- fetch_documents
- get_collection_count
- get_mongo_client
- hasattr
- ingest_documents
- limit
- model

`src/infrastructure/milvus/client.py` (607 lines)
Functions:
- MilvusClientWrapper
- _create_collection
- _initialize_collection
- clear_collection
- close
- create_index
- drop_index
- fetch_documents
- field_name
- get_collection_count
- has_collection
- has_connection
- hasattr
- ingest_documents
- len
- limit
- query_text
- query_vector
- search_with_text
- search_with_vector

`src/config.py` (341 lines)
Functions:
- EXTRACTION_METADATA_FILE_PATH
- MONGO_CONN_STR
- Settings
- suppress_resource_warnings
- suppresses
- when

`src/services/events/constants.py` (65 lines)
Functions:
- EventCategories
- EventTypes
- MessageHeaders
- RetryConfig

`src/domain/llm_prompts/conversation.py` (264 lines)
Functions:
- Prompt
- RESULTS

`src/services/conversation/conversation_history_service.py` (422 lines)
Functions:
- ConversationHistoryService
- ConversationMessage
- ConversationSession
- add_message
- cleanup_old_conversations
- create_conversation
- delete_conversation
- get_conversation
- get_conversation_context
- get_conversation_messages
- get_recent_context
- get_session_messages
- get_user_conversations
- message_count
- rename_conversation
- reset_conversation_messages
- strip
- update_context_summary

`src/processors/crawler/crawler_config.py` (140 lines)
Functions:
- CrawlerKnowledgeConfig
- get_crawler_config
- get_deep_crawler_strategy

`src/processors/crawler/crawler_processor.py` (356 lines)
Functions:
- AsyncWebCrawler
- arun
- debug
- get_knowledge_source_documents
- lower
- range
- str

`tools/core/create_long_term_memory.py` (276 lines)
Functions:
- captures
- force_garbage_collection
- log_memory_usage
- main
- stage
- triggers

`tools/create_long_term_memory.py` (30 lines)
Functions:
- main

`src/application/data/deduplicate_documents.py` (106 lines)
Functions:
- deduplicate_documents
- find_duplicates

`tools/core/delete_long_term_memory.py` (73 lines)
Functions:
- list_collection_names
- main

`tools/delete_long_term_memory.py` (54 lines)
Functions:
- list_collection_names
- main

`src/workflow/nodes/document_judger.py` (95 lines)
Functions:
- document_judger

`src/workflow/nodes/document_retriever.py` (63 lines)
Functions:
- document_retriever

`src/domain/embedding/embedding_model.py` (47 lines)
Functions:
- EmbeddingModel
- EmbeddingModelCreate
- EmbeddingModelUpdate

`tools/examples/example_mongo_schemas.py` (260 lines)
Functions:
- create_failed_event
- example_error_handling
- example_generic_mongo_wrapper
- example_queries
- example_specialized_services
- main
- update_status

`src/infrastructure/milvus/examples.py` (218 lines)
Functions:
- DocumentModel
- example_advanced_search
- example_basic_usage
- example_batch_operations
- example_index_management
- range
- warning

`src/domain/core/exceptions.py` (179 lines)
Functions:
- DocumentRetrievalError
- EntitySearchError
- HybridSearchError
- InvalidSearchParametersError
- KnowledgeConfigNotFound
- KnowledgeConfigRequiredError
- KnowledgeConfigValidationError
- KnowledgeContextNotFound
- KnowledgeGraphSearchError
- KnowledgeNameNotFound
- KnowledgePerspectiveNotFound
- KnowledgeSchemaNotFound
- KnowledgeStyleNotFound
- KnowledgeURLNotFound
- RelationshipSearchError
- SemanticSearchError
- VectorSearchError
- WeaviateConnectionError
- WorkflowToolError

`tools/data/extract_nav_urls.py` (82 lines)
Functions:
- extract_base_and_version

`src/processors/document/file_processor.py` (796 lines)
Functions:
- FileProcessor
- _create_fallback_converter
- _create_minimal_converter
- create_file_knowledge_source
- extract_content
- extract_documents
- extract_markdown
- extract_text
- get_file_documents
- hasattr
- process_uploaded_file
- process_uploaded_file_async
- process_uploaded_files_batch
- startswith
- strip

`src/services/events_listeners/file_upload_event_listener.py` (92 lines)
Functions:
- FileUploadEventListener
- get_file_upload_event_listener
- handle_event
- start_file_upload_event_listener

`src/services/events_publisher/file_upload_event_publisher.py` (81 lines)
Functions:
- FileUploadEventPublisher
- get_file_upload_event_publisher
- publish_file_upload_event
- publish_specific_event

`src/processors/file_upload/file_upload_processor.py` (227 lines)
Functions:
- FileUploadEventProcessor
- _move_file
- get_file_upload_event_processor
- info
- process_file_upload

`src/services/file_management/file_upload_service.py` (128 lines)
Functions:
- handle_file_upload
- move_file

`src/domain/generative/generative_model.py` (47 lines)
Functions:
- GenerativeModel
- GenerativeModelCreate
- GenerativeModelUpdate

`src/workflow/graph.py` (132 lines)
Functions:
- get_graph
- set_checkpointer
- should_continue_after_judger
- should_continue_after_retriever
- should_continue_after_rewriter
- str

`src/application/conversation/graph_response_handler.py` (322 lines)
Functions:
- _debug_state_messages
- _ensure_messages_in_input
- _process_graph
- _stream_graph
- astream
- get_response
- get_streaming_response
- isinstance
- str

`src/infrastructure/mongo/indexes.py` (30 lines)
Functions:
- MongoIndex
- create

`src/infrastructure/milvus/indexes.py` (249 lines)
Functions:
- MilvusIndex
- create_hybrid_index
- create_scalar_index
- create_vector_index
- drop_index
- field_name
- get_index_stats
- list_indexes
- milvus_client
- vector_field

`src/services/events_listeners/job_event_listener.py` (159 lines)
Functions:
- JobEventListener
- _assign_job_to_process
- _register_process
- _unassign_job_from_process
- get_job_event_listener
- handle_event
- start_job_event_listener

`src/services/events_publisher/job_event_publisher.py` (84 lines)
Functions:
- JobEventPublisher
- get_job_event_publisher
- publish_job_execution_requested
- publish_specific_event

`src/domain/events/job_events.py` (145 lines)
Functions:
- JobCancelled
- JobCompleted
- JobExecutionRequested
- JobExecutionScheduled
- JobFailed
- JobStarted

`src/domain/knowledge/job_timeline.py` (81 lines)
Functions:
- Config
- JobTimeline
- JobTimelineCreate
- JobTimelineUpdate

`src/services/knowledge/job_timeline_service.py` (171 lines)
Functions:
- JobTimelineService
- complete_job_execution
- create_timeline_entry
- fail_job_execution
- get_job_timeline_service
- get_latest_timeline_entry
- get_timeline_entry
- get_timeline_statistics
- list_timeline_entries
- start_job_execution
- update_timeline_entry

`src/domain/knowledge/knowledge.py` (126 lines)
Functions:
- Knowledge
- KnowledgeExtract
- from_json
- load_all

`src/domain/rag/knowledge_chunk.py` (42 lines)
Functions:
- KnowledgeChunk

`src/services/knowledge/knowledge_ingestion_service.py` (84 lines)
Functions:
- KnowledgeIngestionService
- clear_knowledge_base
- get_statistics
- ingest_documents

`src/domain/knowledge/knowledge_job.py` (105 lines)
Functions:
- Config
- JobStatus
- KnowledgeJob
- KnowledgeJobCreate
- KnowledgeJobUpdate

`src/processors/knowledge_job/knowledge_job_event_processor.py` (217 lines)
Functions:
- KnowledgeJobEventProcessor
- enhanced_status_callback
- error
- get_knowledge_job_event_processor
- locals
- process_job_execution_requested

`src/processors/knowledge_job/knowledge_job_processor.py` (559 lines)
Functions:
- KnowledgeJobProcessor
- _check_cancellation
- _create_milvus_processor
- _create_text_splitter
- _generate_embeddings_for_chunks
- _generate_embeddings_for_chunks_sync
- _generate_embeddings_with_litellm
- _process_knowledge_source
- _setup_signal_handlers
- _update_job_status_to_cancelled
- batch_callback
- get_knowledge_job_processor
- hasattr
- isinstance
- process_job
- signal_handler

`src/services/knowledge/knowledge_job_service.py` (333 lines)
Functions:
- KnowledgeJobService
- _validate_chunking_config
- _validate_embedding_model
- create_knowledge_job
- delete_knowledge_job
- execute_knowledge_job
- get_knowledge_job
- get_knowledge_job_service
- isinstance
- list_knowledge_jobs
- update_knowledge_job

`src/domain/knowledge/knowledge_source_config.py` (121 lines)
Functions:
- Config
- KnowledgeSourceConfig
- KnowledgeSourceConfigCreate
- KnowledgeSourceConfigUpdate
- ScrapingMode
- UrlSourceConfig
- UrlSourceConfigCreate
- UrlSourceType

`src/services/knowledge/knowledge_source_service.py` (128 lines)
Functions:
- KnowledgeSourceService
- create_knowledge_source_config
- delete_knowledge_source_config
- get_knowledge_source_config
- get_knowledge_source_service
- get_url_source_config
- list_knowledge_source_configs
- update_knowledge_source_config

`src/domain/model_provider/model_provider.py` (212 lines)
Functions:
- ModelProvider
- ModelProviderCreate
- ModelProviderResponse
- ModelProviderUpdate
- ModelType
- ModelTypeConfig
- api_key_required
- embedding_models
- generative_models
- get_api_key_env_var
- requires_api_key
- supported_model_types

`src/services/model_provider/model_provider_initialization_service.py` (354 lines)
Functions:
- ModelProviderInitializationService
- get_predefined_model_providers
- get_provider_config_for_model_type
- get_provider_summary
- get_providers_by_api_key_requirement
- initialize_predefined_model_providers

`src/services/model_provider/model_provider_service.py` (164 lines)
Functions:
- ModelProviderService
- create_model_provider
- get_active_model_providers
- get_model_provider
- get_model_provider_response
- get_model_provider_service
- get_provider_by_name
- get_providers_by_type
- list_model_providers
- update_model_provider

`src/domain/notification/notification.py` (119 lines)
Functions:
- Notification
- NotificationCreate
- NotificationListResponse
- NotificationPriority
- NotificationResponse
- NotificationStats
- NotificationStatus
- NotificationType
- NotificationUpdate

`src/services/events_listeners/notification_event_listener.py` (87 lines)
Functions:
- NotificationEventListener
- get_notification_event_listener
- handle_event
- start_notification_event_listener

`src/services/events_publisher/notification_event_publisher.py` (81 lines)
Functions:
- NotificationEventPublisher
- get_notification_event_publisher
- publish_notification_event
- publish_specific_event

`src/services/notification/notification_event_service.py` (335 lines)
Functions:
- fire_error_event
- fire_interview_started_event
- fire_job_analysis_completed_event
- fire_job_deleted_event
- fire_resume_analysis_completed_event
- fire_resume_deleted_event
- fire_session_created_event
- fire_session_deleted_event
- publish_notification_event
- publish_to_notification_dlq

`src/services/notification/notification_listener_service.py` (257 lines)
Functions:
- notification_event_listener
- process_message
- process_notification_event
- setup_notification_queues
- start_notification_listener

`src/processors/notifications/notification_processor.py` (67 lines)
Functions:
- NotificationEventProcessor
- get_notification_event_processor
- process_notification_event

`src/infrastructure/utils/notification_utils.py` (207 lines)
Functions:
- NotificationManager
- fire_error_notification
- fire_interview_created_notification
- fire_interview_deleted_notification
- fire_interview_started_notification
- fire_job_analysis_completed_notification
- fire_job_deleted_notification
- fire_resume_analysis_completed_notification
- fire_resume_deleted_notification
- fire_session_created_notification
- fire_session_deleted_notification

`src/services/notification/notification_websocket_service.py` (145 lines)
Functions:
- NotificationWebSocketService
- broadcast_notification
- connect_user
- create_and_broadcast_notification
- disconnect_user
- subscribe_user
- unsubscribe_user

`src/infrastructure/opik_utils.py` (61 lines)
Functions:
- configure
- create_dataset
- get_dataset

`src/services/process/process_assignment_service.py` (265 lines)
Functions:
- ProcessAssignmentService
- assign_job_to_best_process
- assign_job_to_process
- balance_process_loads
- get_best_process_for_job
- get_process_assignment_stats
- get_process_health_score
- get_process_load
- reassign_jobs_from_process

`src/services/process/process_cleanup_service.py` (162 lines)
Functions:
- ProcessCleanupService
- _perform_cleanup_cycle
- _setup_signal_handlers
- force_cleanup_process
- get_cleanup_service
- get_cleanup_statistics
- get_process_health
- get_system_health
- main
- signal_handler
- start
- start_cleanup_service

`src/services/process/process_heartbeat_service.py` (123 lines)
Functions:
- ProcessHeartbeatService
- _send_heartbeat
- _setup_signal_handlers
- add_job
- get_active_jobs
- get_heartbeat_service
- main
- remove_job
- signal_handler
- start
- start_heartbeat_service
- stop
- update_active_jobs

`src/domain/process/process_registry.py` (98 lines)
Functions:
- Config
- ListenerProcessInstance
- ListenerType
- ProcessAssignment
- ProcessCleanupResult
- ProcessHealthMetrics
- ProcessHeartbeat
- ProcessStatus

`src/services/process/process_registry_service.py` (265 lines)
Functions:
- ProcessRegistryService
- assign_job_to_process
- cancel_orphaned_jobs
- cleanup_crashed_process
- cleanup_old_data
- detect_crashed_processes
- generate_process_id
- get_least_loaded_process
- get_process_health_metrics
- get_system_health
- graceful_shutdown
- mark_process_crashed
- register_process
- send_heartbeat
- unassign_job_from_process

`src/workflow/nodes/query_rewriter.py` (70 lines)
Functions:
- query_rewriter

`src/domain/rag/rag_file_upload.py` (132 lines)
Functions:
- ErrorDetails
- FileLocations
- FileMetadata
- FileUploadStatus
- ProcessingResults
- RagFailedEvent
- RagFileUpload
- StatusHistoryEntry

`src/application/conversation/reset_conversation_state.py` (156 lines)
Functions:
- cleanup_problematic_checkpoints
- fix_checkpoint_indexes
- list_collection_names
- reset_conversation_messages_state
- will

`src/workflow/tools/retrieval_tools.py` (525 lines)
Functions:
- _serialize_documents_for_llm
- entity_search
- get_document_by_id
- hybrid_search
- isinstance
- knowledge_graph_search
- lower
- relationship_search
- semantic_search
- strip
- vector_search

`src/application/rag/retrievers.py` (397 lines)
Functions:
- RetrievalMetrics
- milvus_entity_search
- milvus_knowledge_graph_search
- milvus_relationship_search
- milvus_semantic_search

`src/domain/user/role_model.py` (125 lines)
Functions:
- Role
- RoleType
- UserRoleAssignment
- add_permission
- can_be_deleted
- can_be_modified
- get_permissions_set
- has_permission
- is_expired
- is_valid
- remove_permission

`src/domain/user/roles.py` (132 lines)
Functions:
- UserRole
- UserRoles
- get_default_roles
- get_permissions
- get_role_description
- has_permission
- is_valid_role

`src/services/users/roles_service.py` (322 lines)
Functions:
- RolesService
- create_role
- delete_role
- get_active_roles
- get_all_permission_names
- get_all_permissions
- get_all_roles
- get_custom_roles
- get_permissions_by_category
- get_role_by_id
- get_role_by_name
- get_roles_count
- get_system_roles
- initialize_system_roles
- role_exists
- update_role

`run_all_event_listeners.py` (273 lines)
Functions:
- EventListenerManager
- _check_process_health
- _monitor_status
- _shutdown_all_processes
- _start_listener_process
- main
- signal_handler
- start_all_listeners
- wait

`run_api_server.py` (28 lines)
Functions:
- signal_handler

`tools/core/run_extraction.py` (144 lines)
Functions:
- asyncio
- get_knowledge_source_documents
- main
- that

`run_file_listener.py` (32 lines)
Functions:
- main

`run_file_upload_event_listener.py` (59 lines)
Functions:
- main

`run_job_event_listener.py` (59 lines)
Functions:
- main

`run_notification_event_listener.py` (59 lines)
Functions:
- main

`run_notification_listener.py` (33 lines)
Functions:
- main

`run_notification_websocket_service.py` (46 lines)
Functions:
- main

`run_process_cleanup_service.py` (35 lines)
Functions:
- main

`tools/tests/run_tests.py` (243 lines)
Functions:
- TestRunner
- list_tests
- main
- run_all_tests
- run_category
- run_interactive
- run_test
- sorted
- values

`tools/testing/run_tests.py` (32 lines)
Functions:
- main

`run_timeline_event_listener.py` (62 lines)
Functions:
- main

`postman/setup_postman_collection.js` (164 lines)
Functions:
- extractConfigId
- extractConversationId
- extractFileId
- extractJobId
- extractNotificationId
- extractRoleId
- forEach
- function
- json
- log
- property
- status
- test
- testRequiredFields
- testResponseStatus

`src/application/rag/splitters.py` (28 lines)
Functions:
- get_splitter

`src/workflow/state.py` (84 lines)
Functions:
- WorkflowState
- create_initial_state

`tools/tests/test_document_splitting.py` (417 lines)
Functions:
- DocumentSplittingTester
- analyze_chunk_correlations
- create_sample_document
- demonstrate_search_scenarios
- demonstrate_weaviate_structure
- main
- run_comprehensive_test
- test_document_splitting

`tools/tests/test_file_saving.py` (319 lines)
Functions:
- isinstance
- len
- test_enriched_documents_file_saving
- test_enriched_markdown_file_saving
- test_file_structure
- test_markdown_file_saving

`tools/tests/test_graph_data_in_results.py` (70 lines)
Functions:
- test_graph_data_in_results

`tools/tests/test_llm_memory_fix.py` (119 lines)
Functions:
- create_test_documents
- log_memory_usage
- main
- range
- test_llm_memory_fix

`tools/tests/test_llm_server.py` (86 lines)
Functions:
- main
- test_llm_server

`tools/tests/test_memory_optimization.py` (148 lines)
Functions:
- log_memory_usage
- main
- test_memory_optimization

`tools/tests/test_sync_llm.py` (102 lines)
Functions:
- create_test_documents
- main
- range
- test_sync_llm

`src/handlers/timeline_event_handler.py` (95 lines)
Functions:
- TimelineEventHandler
- _handle_batch_progress_updated
- _handle_status_changed
- _notify_ui_update
- can_handle
- handle

`src/services/events_listeners/timeline_event_listener.py` (199 lines)
Functions:
- TimelineEventListener
- _handle_batch_progress_updated
- _handle_status_changed
- _register_process
- get_timeline_event_listener
- handle_event
- start_timeline_event_listener

`src/domain/events/timeline_events.py` (73 lines)
Functions:
- TimelineBatchProgressUpdated
- TimelineEvent
- TimelineStatusChanged
- to_timeline_update

`src/domain/user/user.py` (96 lines)
Functions:
- User
- add_role_id
- clear_roles
- get_profile_value
- get_role_ids
- has_role_id
- is_active_user
- remove_role_id
- set_profile_value
- update_last_login

`src/services/users/user_service.py` (284 lines)
Functions:
- UserService
- assign_role_to_user
- change_user_password
- delete_user
- get_all_users
- get_user_by_email
- get_user_by_id
- get_user_by_username
- get_user_permissions
- get_user_role_names
- get_user_roles
- get_users_count
- get_users_with_role
- remove_role_from_user
- set_user_roles
- update_user_profile
- user_can_manage_interviews
- user_can_manage_knowledge
- user_can_manage_users
- user_can_read_interviews
- user_can_read_knowledge
- user_can_read_users
- user_has_permission
- user_has_role
- user_has_role_id
- user_is_admin
- user_is_interviewer

`src/infrastructure/milvus/utils.py` (441 lines)
Functions:
- batch_insert_data
- build_filter_expression
- create_bool_field_schema
- create_document_collection_schema
- create_float_field_schema
- create_int_field_schema
- create_varchar_field_schema
- create_vector_field_schema
- data
- document_id
- filters
- get_optimal_batch_size
- hasattr
- isinstance
- name
- parse_search_results
- prepare_document_data
- results
- validate_vector_dimension
- vector
- vector_dim

`src/domain/knowledge/vectordb_collection.py` (66 lines)
Functions:
- Config
- VectorDBCollection
- VectorDBCollectionCreate
- VectorDBCollectionUpdate

`src/services/knowledge/vectordb_collection_service.py` (139 lines)
Functions:
- VectorDBCollectionService
- _validate_chunking_config
- _validate_embedding_model
- create_collection
- delete_collection
- get_collection
- get_collection_by_name
- get_vectordb_collection_service
- list_collections
- update_collection

`src/domain/rag/weaviate_chunk.py` (49 lines)
Functions:
- KnowledgeChunk

`src/processors/document/web_document_processor.py` (429 lines)
Functions:
- WebDocumentProcessor
- collect_batch
- create_file_knowledge_source
- creates
- extract
- extract_with_batch_processing_callback
- get_extraction_generator
- get_file_type
- get_web_documents
- leverages
- process_knowledge_source_with_batch_callback
- process_uploaded_file
- process_uploaded_files_batch

# 📊 Project Overview
**Files:** 175  |  **Lines:** 21,444

## 📁 File Distribution
- .js: 1 files (164 lines)
- .py: 174 files (21,280 lines)

*Updated: October 14, 2025 at 09:06 AM*