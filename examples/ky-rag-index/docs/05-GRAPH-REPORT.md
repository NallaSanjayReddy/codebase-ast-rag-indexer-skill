# 05 — Knowledge Graph Report (`ky`)

[← 00-INDEX.md](./00-INDEX.md) | [Interactive Graph (`graph.html`)](./graph.html)

## God Nodes (Most-Connected Core Abstractions)

| Symbol | Kind | Community | Degree | File |
| :--- | :--- | :--- | :--- | :--- |
| `source.core.Ky.Ky.create` | method | `source/core` | `18` | `source/core/Ky.ts` |
| `source.core.Ky.Ky.constructor` | method | `source/core` | `8` | `source/core/Ky.ts` |
| `source.errors.HTTPError.HTTPError` | class | `source/errors` | `8` | `source/errors/HTTPError.ts` |
| `source.errors.KyError.KyError` | class | `source/errors` | `7` | `source/errors/KyError.ts` |
| `source.core.constants.RetryMarker.constructor` | method | `source/core` | `6` | `source/core/constants.ts` |
| `source.types.options.Options` | interface | `source/core` | `6` | `source/types/options.ts` |
| `source.core.Ky.cloneInitHookOptions` | function | `source/core` | `3` | `source/core/Ky.ts` |
| `source.errors.HTTPError.HTTPError.constructor` | method | `source/types` | `2` | `source/errors/HTTPError.ts` |
| `source.errors.NonError.NonError.wrap` | method | `source/errors` | `2` | `source/errors/NonError.ts` |
| `source.errors.ResponseSizeError.ResponseSizeError` | class | `source/errors` | `2` | `source/errors/ResponseSizeError.ts` |
| `source.errors.TimeoutError.TimeoutError` | class | `source/core` | `2` | `source/errors/TimeoutError.ts` |
| `source.types.options.NormalizedOptions` | interface | `source/types` | `2` | `source/types/options.ts` |

## Detected Subsystem Communities (Production-Isolated)

| Community | Label | Symbols | Cohesion | Sample Nodes |
| :--- | :--- | :--- | :--- | :--- |
| `#0` | `source/errors` | `16` | `0.058` | `ForceRetryError`, `constructor`, `HTTPError`, `KyError` |
| `#1` | `source/core` | `10` | `0.133` | `cloneInitHookOptions`, `Ky`, `create`, `constructor` |
| `#2` | `source/utils` | `5` | `0.0` | `flush`, `value`, `value#L149`, `transform#L186` |
| `#3` | `source/types` | `3` | `0.333` | `constructor`, `Result`, `NormalizedOptions` |
| `#4` | `tests` | `624` | `0.001` | `RequestInit`, `fetch`, `Options`, `NormalizedOptions` |

## Surprising Cross-Community Bridges

- `source.errors.TimeoutError.TimeoutError` (`source/core`) **`--inherits-->`** `source.errors.KyError.KyError` (`source/errors`) [`EXTRACTED`]

## Import Cycles

- *No module import cycles detected.*

## Extracted Rationale & Design Notes (`0` found)

- *No `# WHY:` / `# NOTE:` / `// ADR:` rationale comments found.*

## Incremental File Manifest Delta
- Added: `98` | Modified: `0` | Unchanged: `0` | Deleted: `0`
