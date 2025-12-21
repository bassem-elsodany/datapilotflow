# DataPilotFlow Persistence

MongoDB data access layer for DataPilotFlow.

Contains:
- MongoDB client wrapper
- Data access objects (DAOs) for all entities
- MongoDB index definitions

## Installation

```bash
pip install datapilotflow-persistence
```

## Usage

```python
from datapilotflow.persistence import MongoClientWrapper

# Create MongoDB client
mongo = MongoClientWrapper()

# Access DAOs
users_dao = mongo.users
conversations_dao = mongo.conversations
```

## License

MIT
