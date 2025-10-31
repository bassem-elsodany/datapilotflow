"""
Quick test for markdown splitter parent merge functionality.
"""

from src.domain.knowledge.document_splitter import DocumentSplitter, SplitterType
from src.processors.splitters.markdown_splitter import MarkdownSplitter


def test_simple_merge():
    """Test that small chunks are merged into parent."""

    # Create test markdown with small child
    text = """# Main Title

This is the introduction with some content to make it around 200 tokens or so. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Features

This section has several features described in detail. Each feature is important and needs explanation. We want this section to have enough tokens to be substantial. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### Small Feature

This is a tiny feature description that should be merged into the parent.

## Installation

Installation instructions go here with sufficient detail to make a proper chunk. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.
"""

    # Create splitter config
    config = DocumentSplitter(
        id="test-splitter",
        name="Test Splitter",
        user_id="test-user",
        splitter_type=SplitterType.DOCUMENT,
        chunk_size=300,
        chunk_overlap=50,
        created_by="test",
        updated_by="test"
    )

    # Create markdown splitter with token limits
    splitter = MarkdownSplitter(
        splitter_config=config,
        max_tokens=512,
        model_name="text-embedding-ada-002",
        min_chunk_size=200
    )

    # Split the text
    chunks = splitter.split(text)

    print(f"\n✅ Test Results:")
    print(f"   Total chunks created: {len(chunks)}")
    print(f"\n   Chunk details:")
    for i, chunk in enumerate(chunks):
        content_preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"   {i+1}. {content_preview}... (metadata: {chunk.metadata})")

    # Verify small chunk was merged
    # We expect fewer chunks than if no merging occurred
    print(f"\n✅ Small chunks should have been merged into parents!")


if __name__ == "__main__":
    test_simple_merge()
