# Orchestration package
#
# Multi-agent orchestration now uses official langgraph-supervisor library
# See generate_response_supervisor.py for implementation
#
# Official pattern:
# supervisor_graph = create_supervisor(
#     agents=[agent1, agent2],
#     model=llm_client,
#     prompt="System instructions..."
# )
