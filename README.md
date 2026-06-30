# TrashDB Python SDK

[![PyPI version](https://img.shields.io/pypi/v/trashdb)](https://pypi.org/project/trashdb/)
[![Python versions](https://img.shields.io/pypi/pyversions/trashdb)](https://pypi.org/project/trashdb/)
[![License](https://img.shields.io/pypi/l/trashdb)](LICENSE)

Official Python SDK for [TrashDB](https://trashdb.dev) — ephemeral database containers on demand.

```python
from trashdb import TrashDB, TrashDBOptions, CreateContainerParams

db = TrashDB(TrashDBOptions(api_key="trdb_your_key_here"))
container = db.create_container(CreateContainerParams(engine="postgres", ttl_minutes=5))
print(container.connection_string)
```

## Installation

```bash
pip install trashdb
```

## Documentation

See https://docs.trashdb.dev/sdks/python
