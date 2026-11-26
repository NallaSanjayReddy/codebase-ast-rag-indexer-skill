# 05 — Knowledge Graph Report (`httpx`)

[← 00-INDEX.md](./00-INDEX.md) | [Interactive Graph (`graph.html`)](./graph.html)

## God Nodes (Most-Connected Core Abstractions)

| Symbol | Kind | Community | Degree | File |
| :--- | :--- | :--- | :--- | :--- |
| `httpx._models.Response` | class | `httpx` | `383` | `httpx/_models.py` |
| `httpx._client.AsyncClient.get` | method | `httpx` | `283` | `httpx/_client.py` |
| `httpx._client.Client.get` | method | `httpx` | `283` | `httpx/_client.py` |
| `httpx._api.get` | function | `httpx` | `279` | `httpx/_api.py` |
| `httpx._client.Client` | class | `httpx` | `259` | `httpx/_client.py` |
| `httpx._models.Request` | class | `httpx` | `247` | `httpx/_models.py` |
| `httpx._urls.URL` | class | `httpx` | `236` | `httpx/_urls.py` |
| `httpx._transports.mock.MockTransport` | class | `httpx` | `206` | `httpx/_transports/mock.py` |
| `httpx._client.AsyncClient` | class | `httpx` | `145` | `httpx/_client.py` |
| `httpx._models.Response.json` | method | `httpx` | `132` | `httpx/_models.py` |
| `httpx._urls.URL.join` | method | `httpx` | `97` | `httpx/_urls.py` |
| `httpx._models.Request.read` | method | `httpx` | `85` | `httpx/_models.py` |

## Detected Subsystem Communities (Production-Isolated)

| Community | Label | Symbols | Cohesion | Sample Nodes |
| :--- | :--- | :--- | :--- | :--- |
| `#0` | `httpx` | `519` | `0.009` | `request`, `stream`, `get`, `options` |
| `#1` | `httpx/_transports` | `8` | `0.036` | `__init__`, `__init__`, `__init__`, `__init__` |
| `#2` | `tests` | `623` | `0.001` | `test_get`, `test_get_invalid_url`, `test_build_request`, `test_post` |

## Surprising Cross-Community Bridges

- *No cross-community bridges detected.*

## Import Cycles

- *No module import cycles detected.*

## Extracted Rationale & Design Notes (`4` found)

- **`[NOTE]`** `httpx._decoders.ZStandardDecoder` (L197): this is a no-op
- **`[NOTE]`** `httpx._decoders.ZStandardDecoder.flush` (L197): this is a no-op
- **`[NOTE]`** `httpx._decoders.LineDecoder` (L346): the edge case input of empty text doesn't occur in practice,
- **`[NOTE]`** `httpx._decoders.LineDecoder.decode` (L346): the edge case input of empty text doesn't occur in practice,

## Incremental File Manifest Delta
- Added: `60` | Modified: `0` | Unchanged: `0` | Deleted: `0`
