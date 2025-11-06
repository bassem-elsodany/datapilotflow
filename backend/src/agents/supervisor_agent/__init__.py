# Supervisor Agent package
#
# NOTE: Supervisor is now implemented using official langgraph-supervisor library
# See: https://github.com/langchain-ai/langgraph-supervisor-py
#
# Usage in generate_response_supervisor.py:
# supervisor_graph = create_supervisor(
#     agents=[rag_agent.rag_graph, task_agent.task_graph],
#     model=llm_client,
#     prompt="You are a supervisor managing multiple agents..."
# )
