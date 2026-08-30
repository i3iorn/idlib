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

| Type        | Output                                       | Notes                                                              |
|-------------|-----------------------------------------------|---------------------------------------------------------------------|
| `UUID`      | `uuid.UUID`                                   | Length argument is ignored. Random; not coordinated, but collision-negligible.                                       |
| `SNOWFLAKE` | `int`                                          | Length argument is ignored. **The only type with an actual uniqueness guarantee** — see below.        |
| `STR`       | `str` of exactly `n` ASCII letters            | Random; no uniqueness guarantee.                                                     |
| `INT`       | `int` with exactly `n` significant digits     | Random; no uniqueness guarantee. The first digit is chosen from 1-9 so the value never has a leading zero. |
| `HEX`       | `str` of exactly `n` lowercase hex digits (`0-9a-f`) | Random; no uniqueness guarantee.                                              |
| `BASE64`    | `str` of exactly `n` base64-alphabet characters | Random; no uniqueness guarantee.                                                    |
| `BYTES`     | `bytes` of exactly `n` bytes                  | Random; no uniqueness guarantee. Opaque ASCII-derived bytes, not raw random bytes — don't use where full byte-value entropy is required. |

For every type except `UUID` and `SNOWFLAKE`, the requested length must
fall between `MIN_ID_LENGTH` (default 16) and `MAX_ID_LENGTH` (default 64),
each overridable via an environment variable of the same name.

### Guaranteed uniqueness: `IdType.SNOWFLAKE`

Every other `IdType` is random and, while collisions are unlikely, carries
no actual guarantee — two threads, processes, or hosts could in principle
produce the same value. `IdType.SNOWFLAKE` is different: it's built from a
millisecond timestamp, a machine/process id, and a per-millisecond sequence
number (the classic Twitter "Snowflake" layout: 41 + 10 + 12 bits), so ids
are unique by construction — no shared storage or locking required.

```python
from idlib import Id
from idlib.utils import IdType

a = Id(IdType.SNOWFLAKE)
b = Id(IdType.SNOWFLAKE)
assert a.id != b.id
```

- **Within one process**, uniqueness across threads is enforced by a lock
  around the sequence counter (`idlib.snowflake.SnowflakeGenerator`).
- **Across processes and hosts**, uniqueness relies on each process
  deriving a different 10-bit machine id from its hostname and pid
  (`idlib.snowflake.default_machine_id`) — collisions are possible in
  principle (only 1024 values) but very unlikely in practice. For a hard
  guarantee across a large fleet, construct your own
  `SnowflakeGenerator(machine_id=...)` with ids assigned out-of-band (e.g.
  from your deployment tooling) instead of relying on the default.
- If the system clock moves backwards, generation raises
  `idlib.exceptions.ClockMovedBackwardsException` rather than risking a
  duplicate id.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```
