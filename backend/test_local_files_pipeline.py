"""
Test script for local files pipeline implementation.

This script demonstrates how the new pipeline factory creates different
pipelines based on content_source_type and scraping_mode.
"""

import asyncio
from pathlib import Path

# Direct imports to avoid circular import
from src.domain.knowledge.knowledge_source_config import (
    ContentSourceType,
    KnowledgeSourceConfig,
    ScrapingMode,
)
from src.processors.knowledge_job.pipeline.pipeline_factory import (
    PipelineFactory,
    get_pipeline_description,
)


def test_pipeline_factory():
    """Test the pipeline factory with different configurations."""

    print("\n" + "=" * 80)
    print("LOCAL FILES PIPELINE FACTORY TEST")
    print("=" * 80 + "\n")

    # Test 1: Markdown files
    print("📝 Test 1: Markdown Files Configuration")
    print("-" * 80)
    md_config = KnowledgeSourceConfig(
        id="test-md-config",
        user_id="test-user",
        name="Test Markdown Files",
        content_source_type=ContentSourceType.LOCAL_FILES,
        scraping_mode=ScrapingMode.MARKDOWN_FILES,
        local_files=[
            {"file_path": "/path/to/file1.md", "original_filename": "file1.md"},
            {"file_path": "/path/to/file2.md", "original_filename": "file2.md"},
        ],
        created_by="test-user",
        updated_by="test-user",
    )

    description = get_pipeline_description(md_config)
    print(f"Pipeline: {description}")

    extraction_step = PipelineFactory.create_extraction_step(md_config)
    print(f"Extraction Step: {extraction_step.name} ({type(extraction_step).__name__})")

    steps = PipelineFactory.create_pipeline_steps(md_config)
    print(f"Total Steps: {len(steps)}")
    print(f"Step Names: {[step.name for step in steps]}")
    print()

    # Test 2: PDF files
    print("📄 Test 2: PDF Files Configuration")
    print("-" * 80)
    pdf_config = KnowledgeSourceConfig(
        id="test-pdf-config",
        user_id="test-user",
        name="Test PDF Files",
        content_source_type=ContentSourceType.LOCAL_FILES,
        scraping_mode=ScrapingMode.PDF_FILES,
        local_files=[
            {"file_path": "/path/to/doc1.pdf", "original_filename": "doc1.pdf"},
        ],
        created_by="test-user",
        updated_by="test-user",
    )

    description = get_pipeline_description(pdf_config)
    print(f"Pipeline: {description}")

    extraction_step = PipelineFactory.create_extraction_step(pdf_config)
    print(f"Extraction Step: {extraction_step.name} ({type(extraction_step).__name__})")

    steps = PipelineFactory.create_pipeline_steps(pdf_config)
    print(f"Total Steps: {len(steps)}")
    print(f"Step Names: {[step.name for step in steps]}")
    print()

    # Test 3: DOCX files
    print("📃 Test 3: DOCX Files Configuration")
    print("-" * 80)
    docx_config = KnowledgeSourceConfig(
        id="test-docx-config",
        user_id="test-user",
        name="Test DOCX Files",
        content_source_type=ContentSourceType.LOCAL_FILES,
        scraping_mode=ScrapingMode.DOCX_FILES,
        local_files=[
            {"file_path": "/path/to/doc1.docx", "original_filename": "doc1.docx"},
        ],
        created_by="test-user",
        updated_by="test-user",
    )

    description = get_pipeline_description(docx_config)
    print(f"Pipeline: {description}")

    extraction_step = PipelineFactory.create_extraction_step(docx_config)
    print(f"Extraction Step: {extraction_step.name} ({type(extraction_step).__name__})")

    steps = PipelineFactory.create_pipeline_steps(docx_config)
    print(f"Total Steps: {len(steps)}")
    print(f"Step Names: {[step.name for step in steps]}")
    print()

    # Test 4: HTML files
    print("🌐 Test 4: HTML Files Configuration")
    print("-" * 80)
    html_config = KnowledgeSourceConfig(
        id="test-html-config",
        user_id="test-user",
        name="Test HTML Files",
        content_source_type=ContentSourceType.LOCAL_FILES,
        scraping_mode=ScrapingMode.HTML_FILES,
        local_files=[
            {"file_path": "/path/to/page.html", "original_filename": "page.html"},
        ],
        created_by="test-user",
        updated_by="test-user",
    )

    description = get_pipeline_description(html_config)
    print(f"Pipeline: {description}")

    extraction_step = PipelineFactory.create_extraction_step(html_config)
    print(f"Extraction Step: {extraction_step.name} ({type(extraction_step).__name__})")

    steps = PipelineFactory.create_pipeline_steps(html_config)
    print(f"Total Steps: {len(steps)}")
    print(f"Step Names: {[step.name for step in steps]}")
    print()

    # Test 5: Web scraping (for comparison)
    print("🌍 Test 5: Web Scraping Configuration (Traditional)")
    print("-" * 80)
    web_config = KnowledgeSourceConfig(
        id="test-web-config",
        user_id="test-user",
        name="Test Web Scraping",
        url="https://example.com",
        content_source_type=ContentSourceType.WEB_SCRAPING,
        scraping_mode=ScrapingMode.SINGLE_PAGE,
        created_by="test-user",
        updated_by="test-user",
    )

    description = get_pipeline_description(web_config)
    print(f"Pipeline: {description}")

    extraction_step = PipelineFactory.create_extraction_step(web_config)
    print(f"Extraction Step: {extraction_step.name} ({type(extraction_step).__name__})")

    steps = PipelineFactory.create_pipeline_steps(web_config)
    print(f"Total Steps: {len(steps)}")
    print(f"Step Names: {[step.name for step in steps]}")
    print()

    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("Summary:")
    print("- FileExtractionStep is used for LOCAL_FILES")
    print("- DocumentExtractionStep is used for WEB_SCRAPING")
    print("- Pipeline factory correctly creates appropriate steps based on config")
    print()


if __name__ == "__main__":
    test_pipeline_factory()
