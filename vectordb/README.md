# DataPilotFlow VectorDB

Milvus vector database integration for DataPilotFlow.

Contains:
- MilvusClientWrapper (generic vector database client)
- Milvus utilities and schemas
- Vector storage and retrieval operations

## Installation

```bash
pip install datapilotflow-vectordb
```

## Usage

```python
from datapilotflow.vectordb import MilvusClientWrapper

# Create Milvus client
vectordb = MilvusClientWrapper()

# Store embeddings
await vectordb.store_embeddings(collection_name, embeddings)

# Search
results = await vectordb.search(collection_name, query_vector)
```

## License

MIT
