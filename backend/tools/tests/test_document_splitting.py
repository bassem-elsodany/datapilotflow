#!/usr/bin/env python3
"""
Test script to demonstrate document splitting behavior and graph data preservation.
Shows how documents are split and how they maintain their relationships.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document
from loguru import logger

from config import settings
from src.processors.splitters import get_splitter


class DocumentSplittingTester:
    """Test document splitting behavior and graph data preservation."""

    def __init__(self):
        self.splitter = get_splitter(chunk_size=500)  # Small chunks for demonstration

    def create_sample_document(self) -> Document:
        """Create a sample document with rich content and graph data."""
        sample_content = """
# DataWeave 2.0 Reference

## Overview
DataWeave is a powerful data transformation language used in MuleSoft applications. It provides a declarative way to transform data between different formats.

## Basic Syntax

### Variables
Variables in DataWeave are declared using the `var` keyword:

```dataweave
var myVariable = "Hello World"
```

### Functions
Functions are defined using the `fun` keyword:

```dataweave
fun add(a: Number, b: Number) = a + b
```

## Data Types

### Strings
Strings are enclosed in double quotes:

```dataweave
"Hello World"
```

### Numbers
Numbers can be integers or decimals:

```dataweave
42
3.14
```

### Arrays
Arrays are ordered collections:

```dataweave
[1, 2, 3, 4, 5]
```

### Objects
Objects are key-value pairs:

```dataweave
{
    name: "John",
    age: 30
}
```

## Advanced Features

### Mapping
Mapping allows you to transform data structures:

```dataweave
payload map {
    id: $.id,
    fullName: $.firstName ++ " " ++ $.lastName
}
```

### Filtering
Filtering allows you to select specific elements:

```dataweave
payload filter ($.active == true)
```

### Reducing
Reducing allows you to aggregate data:

```dataweave
payload reduce (item, acc = 0) -> acc + item.value
```

## Best Practices

### Performance
- Use `map` instead of `for` loops when possible
- Avoid nested loops
- Use `filter` before `map` to reduce processing

### Readability
- Use meaningful variable names
- Break complex transformations into smaller functions
- Add comments for complex logic

## Common Patterns

### Data Validation
```dataweave
payload map {
    id: $.id,
    name: $.name default "Unknown",
    age: $.age match {
        case age if age > 0 -> age
        else -> 0
    }
}
```

### Error Handling
```dataweave
try {
    payload transform
} catch (e) {
    {
        error: e.message,
        timestamp: now()
    }
}
```

## Integration with MuleSoft

### HTTP Requests
DataWeave can be used to transform HTTP request payloads:

```dataweave
%dw 2.0
output application/json
---
{
    requestId: uuid(),
    data: payload,
    timestamp: now()
}
```

### Database Operations
DataWeave can transform database query results:

```dataweave
%dw 2.0
output application/json
---
payload map {
    id: $.ID,
    name: $.NAME,
    email: $.EMAIL
}
```

## Conclusion
DataWeave is a powerful and flexible language for data transformation in MuleSoft applications. Understanding its syntax and patterns is essential for building robust integration solutions.
"""

        # Create rich graph data
        graph_data = {
            "page_title": "DataWeave 2.0 Reference",
            "page_url": "https://docs.mulesoft.com/dataweave/2.4/dataweave-reference",
            "headers": [
                {
                    "level": 1,
                    "text": "DataWeave 2.0 Reference",
                    "header_id": "dataweave-20-reference",
                },
                {"level": 2, "text": "Overview", "header_id": "overview"},
                {"level": 2, "text": "Basic Syntax", "header_id": "basic-syntax"},
                {"level": 3, "text": "Variables", "header_id": "variables"},
                {"level": 3, "text": "Functions", "header_id": "functions"},
                {"level": 2, "text": "Data Types", "header_id": "data-types"},
                {"level": 3, "text": "Strings", "header_id": "strings"},
                {"level": 3, "text": "Numbers", "header_id": "numbers"},
                {"level": 3, "text": "Arrays", "header_id": "arrays"},
                {"level": 3, "text": "Objects", "header_id": "objects"},
                {
                    "level": 2,
                    "text": "Advanced Features",
                    "header_id": "advanced-features",
                },
                {"level": 3, "text": "Mapping", "header_id": "mapping"},
                {"level": 3, "text": "Filtering", "header_id": "filtering"},
                {"level": 3, "text": "Reducing", "header_id": "reducing"},
                {"level": 2, "text": "Best Practices", "header_id": "best-practices"},
                {"level": 3, "text": "Performance", "header_id": "performance"},
                {"level": 3, "text": "Readability", "header_id": "readability"},
                {"level": 2, "text": "Common Patterns", "header_id": "common-patterns"},
                {"level": 3, "text": "Data Validation", "header_id": "data-validation"},
                {"level": 3, "text": "Error Handling", "header_id": "error-handling"},
                {
                    "level": 2,
                    "text": "Integration with MuleSoft",
                    "header_id": "integration-with-mulesoft",
                },
                {"level": 3, "text": "HTTP Requests", "header_id": "http-requests"},
                {
                    "level": 3,
                    "text": "Database Operations",
                    "header_id": "database-operations",
                },
                {"level": 2, "text": "Conclusion", "header_id": "conclusion"},
            ],
            "internal_links": [
                {
                    "href": "/dataweave/2.4/dataweave-syntax",
                    "text": "DataWeave Syntax",
                    "title": "DataWeave Syntax Guide",
                    "base_domain": "docs.mulesoft.com",
                },
                {
                    "href": "/dataweave/2.4/dataweave-types",
                    "text": "Data Types",
                    "title": "DataWeave Data Types",
                    "base_domain": "docs.mulesoft.com",
                },
                {
                    "href": "/dataweave/2.4/dataweave-functions",
                    "text": "Functions",
                    "title": "DataWeave Functions",
                    "base_domain": "docs.mulesoft.com",
                },
            ],
            "code_blocks": [
                {
                    "language": "dataweave",
                    "code": 'var myVariable = "Hello World"',
                    "lines": 1,
                },
                {
                    "language": "dataweave",
                    "code": "fun add(a: Number, b: Number) = a + b",
                    "lines": 1,
                },
                {"language": "dataweave", "code": '"Hello World"', "lines": 1},
                {"language": "dataweave", "code": "42\n3.14", "lines": 2},
                {"language": "dataweave", "code": "[1, 2, 3, 4, 5]", "lines": 1},
                {
                    "language": "dataweave",
                    "code": '{\n    name: "John",\n    age: 30\n}',
                    "lines": 4,
                },
                {
                    "language": "dataweave",
                    "code": 'payload map {\n    id: $.id,\n    fullName: $.firstName ++ " " ++ $.lastName\n}',
                    "lines": 4,
                },
                {
                    "language": "dataweave",
                    "code": "payload filter ($.active == true)",
                    "lines": 1,
                },
                {
                    "language": "dataweave",
                    "code": "payload reduce (item, acc = 0) -> acc + item.value",
                    "lines": 1,
                },
            ],
            "breadcrumbs": [
                {"text": "Home", "href": "/"},
                {"text": "Documentation", "href": "/docs"},
                {"text": "DataWeave", "href": "/dataweave"},
                {"text": "Reference", "href": "/dataweave/2.4/dataweave-reference"},
            ],
            "metadata": {
                "title": "DataWeave 2.0 Reference",
                "description": "Complete reference guide for DataWeave 2.0 transformation language",
                "keywords": "dataweave, transformation, mulesoft, integration",
                "author": "MuleSoft Documentation Team",
            },
        }

        # Create document with graph_data in metadata (as per your actual structure)
        return Document(
            page_content=sample_content,
            metadata={
                "source": "https://docs.mulesoft.com/dataweave/2.4/dataweave-reference",
                "knowledge_source": "mulesoft_docs",
                "title": "DataWeave 2.0 Reference",
                "description": "Complete reference guide for DataWeave 2.0 transformation language",
                "keywords": "dataweave, transformation, mulesoft, integration",
                "author": "MuleSoft Documentation Team",
                "timestamp": "2024-01-15T10:30:00Z",
                "graph_data": graph_data,
            },
        )

    def test_document_splitting(self) -> None:
        """Test document splitting and analyze the results."""
        logger.info("🧪 Testing document splitting behavior...")

        # Create sample document
        original_doc = self.create_sample_document()
        logger.info(f"📄 Original document:")
        logger.info(f"   Content length: {len(original_doc.page_content)} characters")
        logger.info(
            f"   Headers: {len(original_doc.metadata['graph_data']['headers'])}"
        )
        logger.info(
            f"   Code blocks: {len(original_doc.metadata['graph_data']['code_blocks'])}"
        )
        logger.info(
            f"   Internal links: {len(original_doc.metadata['graph_data']['internal_links'])}"
        )

        # Split the document
        chunked_docs = self.splitter.split_documents([original_doc])
        logger.info(f"\n✂️  Split into {len(chunked_docs)} chunks")

        # Analyze each chunk
        for i, chunk in enumerate(chunked_docs):
            logger.info(f"\n📄 Chunk {i+1}:")
            logger.info(f"   Content length: {len(chunk.page_content)} characters")
            logger.info(f"   Content preview: {chunk.page_content[:100]}...")

            # Check metadata preservation
            logger.info(
                f"   Metadata preserved: {chunk.metadata == original_doc.metadata}"
            )

            # Check graph data preservation
            if "graph_data" in chunk.metadata and chunk.metadata["graph_data"]:
                logger.info(f"   Graph data preserved: ✅")
                logger.info(
                    f"   Headers in chunk: {len(chunk.metadata['graph_data'].get('headers', []))}"
                )
                logger.info(
                    f"   Code blocks in chunk: {len(chunk.metadata['graph_data'].get('code_blocks', []))}"
                )
            else:
                logger.info(f"   Graph data preserved: ❌")

            # Check for specific content in this chunk
            if "DataWeave" in chunk.page_content:
                logger.info(f"   Contains 'DataWeave': ✅")
            if "```dataweave" in chunk.page_content:
                logger.info(f"   Contains code blocks: ✅")
            if "##" in chunk.page_content:
                logger.info(f"   Contains headers: ✅")

    def analyze_chunk_correlations(self, chunked_docs: List[Document]) -> None:
        """Analyze how chunks are correlated and can be reassembled."""
        logger.info(f"\n🔗 Analyzing chunk correlations...")

        # Check for overlapping content (due to chunk overlap)
        overlap_count = 0
        for i in range(len(chunked_docs) - 1):
            chunk1_content = chunked_docs[i].page_content
            chunk2_content = chunked_docs[i + 1].page_content

            # Simple overlap detection (first 50 chars of chunk2 in chunk1)
            if chunk2_content[:50] in chunk1_content:
                overlap_count += 1
                logger.info(f"   Chunks {i+1} and {i+2} have overlapping content")

        logger.info(f"   Total overlapping chunk pairs: {overlap_count}")

        # Check metadata consistency
        all_metadata_consistent = all(
            chunk.metadata == chunked_docs[0].metadata for chunk in chunked_docs
        )
        logger.info(
            f"   All metadata consistent: {'✅' if all_metadata_consistent else '❌'}"
        )

        # Check graph data consistency
        all_graph_data_consistent = all(
            "graph_data" in chunk.metadata
            and chunk.metadata["graph_data"] == chunked_docs[0].metadata["graph_data"]
            for chunk in chunked_docs
        )
        logger.info(
            f"   All graph data consistent: {'✅' if all_graph_data_consistent else '❌'}"
        )

        # Show how chunks can be reassembled
        logger.info(f"\n🔄 Chunk reassembly strategy:")
        logger.info(
            f"   1. All chunks share the same source URL: {chunked_docs[0].metadata['source']}"
        )
        logger.info(f"   2. All chunks share the same graph_data structure")
        logger.info(f"   3. Chunks can be ordered by their content position")
        logger.info(f"   4. Overlapping content helps maintain context between chunks")

    def demonstrate_weaviate_structure(self, chunked_docs: List[Document]) -> None:
        """Demonstrate how chunks would be stored in Weaviate."""
        logger.info(f"\n🗄️  Weaviate Storage Structure:")

        for i, chunk in enumerate(chunked_docs):
            logger.info(f"\n📄 Chunk {i+1} Weaviate Object:")

            # Show the structure that would be stored in Weaviate
            weaviate_object = {
                "page_content": chunk.page_content,
                "source": chunk.metadata["source"],
                "knowledge_source": chunk.metadata["knowledge_source"],
                "title": chunk.metadata["title"],
                "description": chunk.metadata["description"],
                "keywords": chunk.metadata["keywords"],
                "author": chunk.metadata["author"],
                "timestamp": chunk.metadata["timestamp"],
                "graph_data": chunk.metadata["graph_data"],
            }

            logger.info(f"   Top-level properties: {list(weaviate_object.keys())}")
            logger.info(
                f"   Graph data structure: {list(weaviate_object['graph_data'].keys())}"
            )
            logger.info(
                f"   Headers count: {len(weaviate_object['graph_data']['headers'])}"
            )
            logger.info(
                f"   Code blocks count: {len(weaviate_object['graph_data']['code_blocks'])}"
            )
            logger.info(
                f"   Internal links count: {len(weaviate_object['graph_data']['internal_links'])}"
            )

    def demonstrate_search_scenarios(self, chunked_docs: List[Document]) -> None:
        """Demonstrate different search scenarios with split documents."""
        logger.info(f"\n🔍 Search scenario demonstrations:")

        # Scenario 1: Semantic search across all chunks
        logger.info(f"\n1️⃣  Semantic Search:")
        logger.info(f"   Query: 'DataWeave functions and variables'")
        logger.info(
            f"   Result: Would match chunks containing function/variable content"
        )
        logger.info(f"   Graph context: Headers, code blocks, and links preserved")

        # Scenario 2: Code-specific search
        logger.info(f"\n2️⃣  Code Language Search:")
        logger.info(f"   Query: 'dataweave code examples'")
        logger.info(f"   Result: Would match chunks with ```dataweave blocks")
        logger.info(f"   Graph context: Code block metadata preserved")

        # Scenario 3: Header-based search
        logger.info(f"\n3️⃣  Header-based Search:")
        logger.info(f"   Query: 'DataWeave syntax'")
        logger.info(f"   Result: Would match chunks with 'Basic Syntax' headers")
        logger.info(f"   Graph context: Header hierarchy preserved")

        # Scenario 4: Related document search
        logger.info(f"\n4️⃣  Related Document Search:")
        logger.info(f"   Query: 'Find documents linking to DataWeave syntax'")
        logger.info(f"   Result: Would find chunks with internal_links to syntax docs")
        logger.info(f"   Graph context: Link relationships preserved")

    def run_comprehensive_test(self) -> None:
        """Run comprehensive document splitting test."""
        logger.info("🚀 Starting comprehensive document splitting test...")

        # Test basic splitting
        self.test_document_splitting()

        # Create sample document for correlation analysis
        original_doc = self.create_sample_document()
        chunked_docs = self.splitter.split_documents([original_doc])

        # Analyze correlations
        self.analyze_chunk_correlations(chunked_docs)

        # Demonstrate Weaviate structure
        self.demonstrate_weaviate_structure(chunked_docs)

        # Demonstrate search scenarios
        self.demonstrate_search_scenarios(chunked_docs)

        logger.success("\n🎉 Document splitting test completed!")


def main():
    """Main function to run the document splitting test."""
    tester = DocumentSplittingTester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
