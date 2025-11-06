# Orchestration package (deprecated)
#
# Multi-agent orchestration now uses official langgraph-supervisor library
# See: src/services/conversation/generate_response_supervisor.py
#
# Direct usage pattern:
# supervisor_graph = create_supervisor(
#     agents=[agent1_graph, agent2_graph],
#     model=llm_client,
#     prompt="System instructions..."
# )
#
# Reference: https://github.com/langchain-ai/langgraph-supervisor-py
