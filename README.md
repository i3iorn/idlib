# idlib

A small library for generating and managing unique identifiers.

## Usage

```python
from idlib import Id
from idlib.utils import IdType

# defaults to a UUID
default_id = Id()
print(default_id._id)

# or pick a type and length
short_id = Id(IdType.HEX, id_length=20)
print(short_id._id)
```

Supported `IdType` values: `UUID`, `STR`, `INT`, `HEX`, `BASE64`, `BYTES`.
For every type except `UUID`, the requested length must fall between
`MIN_ID_LENGTH` (default 16) and `MAX_ID_LENGTH` (default 64), each
overridable via an environment variable of the same name.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```
