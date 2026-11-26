# 03 — Cross-File References & Test Traceability (`ky`)

[← 00-INDEX.md](./00-INDEX.md)

| Production Symbol | Linked Tests |
| :--- | :--- |
| `source.utils.body.value` | `test.bytes.value` (name_match), `test.error-data.value` (name_match) |
| `source.utils.body.value#L149` | `test.bytes.value` (name_match), `test.error-data.value` (name_match) |
| `source.errors.HTTPError.HTTPError` | `test.error-data.throwHttpErrors` (name_match), `test.error-data.throwHttpErrors#L173` (name_match), `test.hooks.CustomError.throwHttpErrors` (name_match), `test.hooks.CustomError.throwHttpErrors#L5492` (name_match) |
| `source.core.Ky.Ky.constructor` | `test.fetch.Agent.constructor` (name_match), `test.fetch.Agent.constructor#L324` (name_match), `test.headers.Headers.constructor` (name_match), `test.hooks.CustomError.constructor` (name_match) |
| `source.core.constants.RetryMarker.constructor` | `test.fetch.Agent.constructor` (name_match), `test.fetch.Agent.constructor#L324` (name_match), `test.headers.Headers.constructor` (name_match), `test.hooks.CustomError.constructor` (name_match) |
| `source.core.Ky.Ky.create` | `test.http-error.createFakeResponse` (name_match), `test.request-body-serialization.createBodyServer` (name_match), `test.helpers.create-large-file.createLargeBlob` (name_match) |
| `source.errors.KyError.KyError` | `test.main.CustomKyError` (name_match) |
| `source.types.options.Options` | `test-d.normalized-options.Options` (name_match), `test-d.normalized-options.NormalizedOptions` (name_match) |
| `source.types.options.NormalizedOptions` | `test-d.normalized-options.NormalizedOptions` (name_match) |