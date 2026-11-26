# 04 — KV-Cache Prefix Stability & PagedAttention Packing (`ky`)

[← 00-INDEX.md](./00-INDEX.md)

| KV Page | Used / Cap Tokens | Util % | Prefix SHA-256 | Packed AST Chunks |
| :--- | :--- | :--- | :--- | :--- |
| `page-000` | `457/512` | `89.3%` | `937e9d7e333445d4` | `source.core.Ky.cloneInitHookOptions`, `source.core.Ky.Ky` |
| `page-001` | `512/512` | `100.0%` | `499dc6c1bdc00f19` | `source.core.Ky.Ky.create` |
| `page-002` | `173/512` | `33.8%` | `dda2891f6971ac3f` | `source.core.Ky.Ky.constructor`, `source.core.constants.duplex`, `source.core.constants.RetryMarker`, `source.core.constants.RetryMarker.isRetryMarker` (+1) |
| `page-003` | `475/512` | `92.8%` | `6686b43a2de2d002` | `source.errors.ForceRetryError.ForceRetryError` |
| `page-004` | `429/512` | `83.8%` | `6d3667f0c92ca0f0` | `source.errors.ForceRetryError.ForceRetryError.constructor` |
| `page-005` | `428/512` | `83.6%` | `64ea97fe37d3867f` | `source.errors.HTTPError.HTTPError`, `source.errors.HTTPError.HTTPError.constructor`, `source.errors.KyError.KyError`, `source.errors.KyError.KyError.isKyError` (+2) |
| `page-006` | `485/512` | `94.7%` | `6ee7d279afa985e6` | `source.errors.NonError.NonError`, `source.errors.NonError.NonError.wrap`, `source.errors.NonError.NonError.constructor`, `source.errors.ResponseSizeError.ResponseSizeError` (+1) |
| `page-007` | `203/512` | `39.6%` | `3198d1177d2deae1` | `source.errors.SchemaValidationError.SchemaValidationError`, `source.errors.SchemaValidationError.SchemaValidationError.constructor`, `source.errors.TimeoutError.TimeoutError`, `source.errors.TimeoutError.TimeoutError.constructor` (+1) |
| `page-008` | `499/512` | `97.5%` | `b7f3f428294b282b` | `source.types.options.Options` |
| `page-009` | `491/512` | `95.9%` | `43947f25ff91fa84` | `source.types.options.NormalizedOptions`, `source.utils.body.transform`, `source.utils.body.flush` |
| `page-010` | `509/512` | `99.4%` | `f30b295b3beb0fd5` | `source.utils.body.value`, `source.utils.body.value#L149`, `source.utils.body.transform#L186`, `source.utils.delay.abortHandler` (+12) |
| `page-011` | `494/512` | `96.5%` | `2d2c640f16c7c877` | `test.browser.Window.onDownloadProgress#L497`, `test.browser.Window.get`, `test.browser.Window.fetch`, `test.browser.Window.onUploadProgress` (+14) |
| `page-012` | `456/512` | `89.1%` | `5dc040acedbd69be` | `test.error-data.parseJson`, `test.error-data.parseJson#L206`, `test.errors.message`, `test.errors.fetch` (+15) |
| `page-013` | `488/512` | `95.3%` | `e6925c6a13d706f6` | `test.fetch.Agent.cancel#L452`, `test.fetch.Agent.cancel#L490`, `test.fetch.Agent.fetch#L513`, `test.fetch.Agent.fetch#L538` (+10) |
| `page-014` | `509/512` | `99.4%` | `2741b315d41413a0` | `test.fetch.Agent.fetch#L712`, `test.fetch.Agent.pull`, `test.fetch.Agent.fetch#L745`, `test.fetch.Agent.fetch#L765` (+8) |
| `page-015` | `500/512` | `97.7%` | `5d2e21df216cf036` | `test.formdata-searchparams.onUploadProgress`, `test.headers.Headers`, `test.headers.Headers.constructor`, `test.headers.Headers.fetch` (+19) |
| `page-016` | `509/512` | `99.4%` | `58c866149d0dccc5` | `test.hooks.parseJson`, `test.hooks.fetch#L302`, `test.hooks.fetch#L327`, `test.hooks.fetch#L352` (+11) |
| `page-017` | `482/512` | `94.1%` | `d1ffac1d0c553820` | `test.hooks.parseJson#L1002`, `test.hooks.cancel#L1122`, `test.hooks.cancel#L1163`, `test.hooks.fetch#L1210` (+12) |
| `page-018` | `466/512` | `91.0%` | `3c6419657f07a27b` | `test.hooks.fetch#L2410`, `test.hooks.fetch#L2477`, `test.hooks.fetch#L2510`, `test.hooks.fetch#L2539` (+18) |
| `page-019` | `507/512` | `99.0%` | `83a6adcb62c82fc4` | `test.hooks.CustomError.fetch#L3152`, `test.hooks.CustomError.fetch#L3176`, `test.hooks.CustomError.start`, `test.hooks.CustomError.fetch#L3384` (+14) |
| `page-020` | `496/512` | `96.9%` | `80f20a0025c63ac9` | `test.hooks.CustomError.shouldRetry#L5103`, `test.hooks.CustomError.fetch#L5108`, `test.hooks.CustomError.fetch#L5142`, `test.hooks.CustomError.fetch#L5173` (+14) |
| `page-021` | `498/512` | `97.3%` | `c2392b557ddb402f` | `test.hooks.CustomError.fetch#L5960`, `test.hooks.CustomError.fetch#L5981`, `test.hooks.CustomError.fetch#L6266`, `test.hooks.CustomError.fetch#L6296` (+19) |
| `page-022` | `492/512` | `96.1%` | `a46c361d38999e44` | `test.hooks.CustomError.clone`, `test.hooks.CustomError.fetch#L7386`, `test.hooks.CustomError.onUploadProgress`, `test.hooks.CustomError.fetch#L7439` (+18) |
| `page-023` | `480/512` | `93.8%` | `ba5b74c46597b3db` | `test.hooks.CustomError.fetch#L8023`, `test.hooks.CustomError.fetch#L8047`, `test.hooks.CustomError.parseJson#L8051`, `test.http-error.createFakeResponse` (+14) |
| `page-024` | `500/512` | `97.7%` | `aacb73efc1463011` | `test.http-error.start#L574`, `test.http-error.cancel`, `test.http-error.start#L604`, `test.http-error.start#L628` (+12) |
| `page-025` | `500/512` | `97.7%` | `878c9df8d2969fbb` | `test.http-response-bodies.pull`, `test.http-response-bodies.onDownloadProgress`, `test.http-response-bodies.parseJson`, `test.http-semantics.onDownloadProgress` (+17) |
| `page-026` | `505/512` | `98.6%` | `828bdf8ce481a89a` | `test.main.schemaValidationCaller`, `test.main.schemaValidationEntryPoint`, `test.main.asyncValidationCaller`, `test.main.fetch` (+9) |
| `page-027` | `474/512` | `92.6%` | `170d2fbba3a220c9` | `test.main.CustomKyError.start`, `test.main.CustomKyError.start#L1340`, `test.main.CustomKyError.start#L1367`, `test.main.CustomKyError.fetch#L1476` (+8) |
| `page-028` | `490/512` | `95.7%` | `b063c12588e644d0` | `test.main.CustomKyError.fetch#L2020`, `test.main.CustomKyError.fetch#L2037`, `test.main.CustomKyError.fetch#L2053`, `test.main.CustomKyError.fetch#L2428` (+6) |
| `page-029` | `472/512` | `92.2%` | `6c8545672f15dce5` | `test.main.CustomKyError.parseJson#L3856`, `test.main.CustomKyError.parseJson#L3877`, `test.main.CustomKyError.parseJson#L3900`, `test.main.CustomKyError.parseJson#L3922` (+11) |
| `page-030` | `468/512` | `91.4%` | `2a8abf430c918e49` | `test.memory-leak.isKyLeaking`, `test.memory-leak.isStreamLeaking`, `test.merge.fetch`, `test.merge.ownKeys` (+7) |
| `page-031` | `391/512` | `76.4%` | `cb607fda6c0d3bb1` | `test.request-body-serialization.assertBytes`, `test.request-body-serialization.stringifyJson`, `test.request-construction.fetch`, `test.request-options.fetch` (+5) |
| `page-032` | `295/512` | `57.6%` | `8e6472497fe68c9a` | `test.resilience.scriptedFetch` |
| `page-033` | `499/512` | `97.5%` | `ecb7940924175375` | `test.resilience.fetch`, `test.resilience.client`, `test.resilience.shouldRetry`, `test.resilience.shouldRetry#L698` (+7) |
| `page-034` | `483/512` | `94.3%` | `412dc68da6a5ebb9` | `test.resilience.await`, `test.resilience.start#L1113`, `test.response-consumption.onDownloadProgress`, `test.response-consumption.onDownloadProgress#L51` (+17) |