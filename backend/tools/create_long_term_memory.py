from pathlib import Path

import click

from skillpilot.application import LongTermMemoryCreator
from skillpilot.config import settings
from skillpilot.domain.philosopher import PhilosopherExtract


@click.command()
@click.option(
    "--metadata-file",
    type=click.Path(exists=True, path_type=Path),
    default=settings.EXTRACTION_METADATA_FILE_PATH,
    help="Path to the candidates extraction metadata JSON file.",
)
def main(metadata_file: Path) -> None:
    """CLI command to create long-term memory for candidates.

    Args:
        metadata_file: Path to the candidates extraction metadata JSON file.
    """
    candidates = PhilosopherExtract.from_json(metadata_file)

    long_term_memory_creator = LongTermMemoryCreator.build_from_settings()
    long_term_memory_creator(candidates)


if __name__ == "__main__":
    main()
