# 02 — Call Hierarchy, Type Hierarchy & Super-Implementations (`ky`)

[← 00-INDEX.md](./00-INDEX.md)

| Type | Kind | Super Types | Sub Types / Implementations | Location |
| :--- | :--- | :--- | :--- | :--- |
| `source.core.Ky.Ky` | class | — | — | `source/core/Ky.ts:348` |
| `source.core.constants.RetryMarker` | class | — | — | `source/core/constants.ts:162` |
| `source.errors.ForceRetryError.ForceRetryError` | class | `source.errors.KyError.KyError` | — | `source/errors/ForceRetryError.ts:11` |
| `source.errors.HTTPError.HTTPError` | class | `source.errors.KyError.KyError` | — | `source/errors/HTTPError.ts:15` |
| `source.errors.KyError.KyError` | class | `Error` | `source.errors.ForceRetryError.ForceRetryError`, `source.errors.HTTPError.HTTPError`, `source.errors.NetworkError.NetworkError`, `source.errors.ResponseSizeError.ResponseSizeError`, `source.errors.TimeoutError.TimeoutError`, `test.main.CustomKyError` | `source/errors/KyError.ts:8` |
| `source.errors.NetworkError.NetworkError` | class | `source.errors.KyError.KyError` | — | `source/errors/NetworkError.ts:11` |
| `source.errors.NonError.NonError` | class | `Error` | — | `source/errors/NonError.ts:8` |
| `source.errors.ResponseSizeError.ResponseSizeError` | class | `source.errors.KyError.KyError` | — | `source/errors/ResponseSizeError.ts:20` |
| `source.errors.SchemaValidationError.SchemaValidationError` | class | `Error` | — | `source/errors/SchemaValidationError.ts:25` |
| `source.errors.TimeoutError.TimeoutError` | class | `source.errors.KyError.KyError` | — | `source/errors/TimeoutError.ts:7` |
| `source.types.ResponsePromise.Result` | interface | — | — | `source/types/ResponsePromise.ts:40` |
| `source.types.options.Options` | interface | `KyOptions`, `RequestOptions` | — | `source/types/options.ts:454` |
| `source.types.options.NormalizedOptions` | interface | `Readonly` | — | `source/types/options.ts:540` |
| `test.browser.Window` | interface | — | — | `test/browser.ts:17` |
| `test.fetch.Agent` | class | — | — | `test/fetch.ts:300` |
| `test.fetch.Agent#L323` | class | — | — | `test/fetch.ts:323` |
| `test.headers.Headers` | class | `OriginalHeaders` | — | `test/headers.ts:43` |
| `test.hooks.CustomError` | class | `Error` | — | `test/hooks.ts:2592` |
| `test.main.CustomKyError` | class | `source.errors.KyError.KyError` | — | `test/main.ts:713` |
| `test.retry.Holder` | class | — | — | `test/retry.ts:5237` |
| `test-d.fetch-extensions.RequestInit` | interface | — | — | `test-d/fetch-extensions.ts:12` |
| `test-d.normalized-options.Options` | interface | — | — | `test-d/normalized-options.ts:13` |
| `test-d.normalized-options.NormalizedOptions` | interface | — | — | `test-d/normalized-options.ts:17` |

## Super-Implementations (Method Overrides)
