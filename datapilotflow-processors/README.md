# DataPilotFlow Processors

Document processing and text splitting for DataPilotFlow.

Contains:
- Document processors (file, web, PDF, text)
- Text splitters (semantic, token-based, language-aware)
- Web crawlers
- Document extractors

## Installation

```bash
pip install datapilotflow-processors
```

## Usage

```python
from datapilotflow.processors import FileProcessor, TextSplitter

# Process documents
processor = FileProcessor()
documents = await processor.process("path/to/file.pdf")

# Split text
splitter = TextSplitter(chunk_size=1000)
chunks = splitter.split(documents)
```

## License

MIT
