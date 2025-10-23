import asyncio
from functools import wraps

import click

from skillpilot.application.conversation.graph_response_handler import (
    get_streaming_response,
)


def async_command(f):
    """Decorator to run an async click command."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.command()
@click.option(
    "--candidate-id",
    type=str,
    required=True,
    help="ID of the candidate to call.",
)
@click.option(
    "--query",
    type=str,
    required=True,
    help="Query to call the agent with.",
)
@async_command
async def main(candidate_id: str, query: str) -> None:
    """CLI command to query a candidate.

    Args:
        candidate_id: ID of the candidate to call.
        query: Query to call the agent with.
    """

    print(
        f"\033[32mCalling agent with candidate_id: `{candidate_id}` and query: `{query}`\033[0m"
    )
    print("\033[32mResponse:\033[0m")
    print("\033[32m--------------------------------\033[0m")
    async for chunk in get_streaming_response(
        messages=query,
        candidate_id=candidate_id,
        interview_context={
            "role": "Senior Software Engineer",
            "level": "Senior",
            "domains": ["System Design", "Distributed Systems", "Scalability"],
        },
    ):
        print(f"\033[32m{chunk}\033[0m", end="", flush=True)
    print("\033[32m--------------------------------\033[0m")


if __name__ == "__main__":
    main()
