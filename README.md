# idlib

A small library for generating and managing unique identifiers.

## Usage

```python
from idlib import Id
from idlib.utils import IdType

# defaults to a UUID
default_id = Id()
print(default_id.id)

# or pick a type and length
short_id = Id(IdType.HEX, id_length=20)
print(short_id.id)
```

The id value is generated lazily on first access and is then immutable —
assigning to `.id` again raises `IdAlreadySetException`. You can instead
provide the value up front, before it's ever read:

```python
custom_id = Id()
custom_id.id = "my-custom-value"
```

Supported `IdType` values, and what each one guarantees about its output:

| Type     | Output                                       | Notes                                                              |
|----------|-----------------------------------------------|---------------------------------------------------------------------|
| `UUID`   | `uuid.UUID`                                   | Length argument is ignored.                                        |
| `STR`    | `str` of exactly `n` ASCII letters            |                                                                      |
| `INT`    | `int`                                          | Built from `n` random digits; a leading `0` shortens the effective numeric range, so the result isn't guaranteed to have `n` significant digits. |
| `HEX`    | `str` of exactly `n` lowercase hex digits (`0-9a-f`) |                                                               |
| `BASE64` | `str` of exactly `n` base64-alphabet characters |                                                                     |
| `BYTES`  | `bytes` of exactly `n` bytes                  | Opaque ASCII-derived bytes, not raw random bytes — don't use where full byte-value entropy is required. |

For every type except `UUID`, the requested length must fall between
`MIN_ID_LENGTH` (default 16) and `MAX_ID_LENGTH` (default 64), each
overridable via an environment variable of the same name.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```
