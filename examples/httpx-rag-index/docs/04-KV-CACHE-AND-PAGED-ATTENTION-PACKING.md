# 04 — KV-Cache Prefix Stability & PagedAttention Packing (`httpx`)

[← 00-INDEX.md](./00-INDEX.md)

| KV Page | Used / Cap Tokens | Util % | Prefix SHA-256 | Packed AST Chunks |
| :--- | :--- | :--- | :--- | :--- |
| `page-000` | `512/512` | `100.0%` | `bad00ed527d895e4` | `httpx._api.request` |
| `page-001` | `342/512` | `66.8%` | `330e670d1a884181` | `httpx._api.stream` |
| `page-002` | `476/512` | `93.0%` | `80e4a7fda7a87b73` | `httpx._api.get`, `httpx._api.options` |
| `page-003` | `493/512` | `96.3%` | `53744b1f7d9c99b0` | `httpx._api.head`, `httpx._api.post` |
| `page-004` | `512/512` | `100.0%` | `77c7195bdd1f3e7d` | `httpx._api.put`, `httpx._api.patch` |
| `page-005` | `239/512` | `46.7%` | `3e296eaf7126883b` | `httpx._api.delete` |
| `page-006` | `512/512` | `100.0%` | `0a068cc27c980399` | `httpx._auth.Auth` |
| `page-007` | `347/512` | `67.8%` | `93fb456e54ef4a4d` | `httpx._auth.Auth.auth_flow`, `httpx._auth.Auth.sync_auth_flow` |
| `page-008` | `349/512` | `68.2%` | `35c397bfc15c1d7e` | `httpx._auth.Auth.async_auth_flow`, `httpx._auth.FunctionAuth`, `httpx._auth.FunctionAuth.__init__`, `httpx._auth.FunctionAuth.auth_flow` |
| `page-009` | `319/512` | `62.3%` | `b34dfa0f95c18a44` | `httpx._auth.BasicAuth`, `httpx._auth.BasicAuth.__init__`, `httpx._auth.BasicAuth.auth_flow`, `httpx._auth.BasicAuth._build_auth_header` |
| `page-010` | `503/512` | `98.2%` | `cd303c248ac4252a` | `httpx._auth.NetRCAuth`, `httpx._auth.NetRCAuth.__init__`, `httpx._auth.NetRCAuth.auth_flow` |
| `page-011` | `59/512` | `11.5%` | `05afbb5b2760dc84` | `httpx._auth.NetRCAuth._build_auth_header` |
| `page-012` | `512/512` | `100.0%` | `e8c07440c59d9e72` | `httpx._auth.DigestAuth` |
| `page-013` | `367/512` | `71.7%` | `98d7b8c7eb202517` | `httpx._auth.DigestAuth.__init__`, `httpx._auth.DigestAuth.auth_flow` |
| `page-014` | `338/512` | `66.0%` | `d03c6d1202fb403d` | `httpx._auth.DigestAuth._parse_challenge` |
| `page-015` | `488/512` | `95.3%` | `2551a6dd021fc1df` | `httpx._auth.DigestAuth._build_auth_header`, `httpx._auth.DigestAuth._get_client_nonce` |
| `page-016` | `504/512` | `98.4%` | `f5c36fdd65573dcb` | `httpx._auth.DigestAuth._get_header_value`, `httpx._auth.DigestAuth._resolve_qop`, `httpx._auth._DigestAuthChallenge`, `httpx._client._is_https_redirect` (+2) |
| `page-017` | `499/512` | `97.5%` | `fe3cdb8973199bef` | `httpx._client.UseClientDefault`, `httpx._client.ClientState`, `httpx._client.BoundSyncStream` |
| `page-018` | `432/512` | `84.4%` | `04e4185096092e8d` | `httpx._client.BoundSyncStream.__init__`, `httpx._client.BoundSyncStream.__iter__`, `httpx._client.BoundSyncStream.close`, `httpx._client.BoundAsyncStream` (+3) |
| `page-019` | `512/512` | `100.0%` | `ac401b1dedf030b7` | `httpx._client.BaseClient` |
| `page-020` | `429/512` | `83.8%` | `67ad9d29ec2a7b84` | `httpx._client.BaseClient.__init__`, `httpx._client.BaseClient.is_closed`, `httpx._client.BaseClient.trust_env`, `httpx._client.BaseClient._enforce_trailing_slash` |
| `page-021` | `437/512` | `85.4%` | `d7268abb812fbc6b` | `httpx._client.BaseClient._get_proxy_map`, `httpx._client.BaseClient.timeout`, `httpx._client.BaseClient.timeout#L258`, `httpx._client.BaseClient.event_hooks` (+6) |
| `page-022` | `228/512` | `44.5%` | `6f24c191ce9acbd6` | `httpx._client.BaseClient.headers#L306`, `httpx._client.BaseClient.cookies`, `httpx._client.BaseClient.cookies#L326`, `httpx._client.BaseClient.params` (+1) |
| `page-023` | `425/512` | `83.0%` | `e706eb7ef50bb690` | `httpx._client.BaseClient.build_request` |
| `page-024` | `451/512` | `88.1%` | `6da6124348980255` | `httpx._client.BaseClient._merge_url`, `httpx._client.BaseClient._merge_cookies`, `httpx._client.BaseClient._merge_headers` |
| `page-025` | `352/512` | `68.8%` | `2b70296f3f5ee78e` | `httpx._client.BaseClient._merge_queryparams`, `httpx._client.BaseClient._build_auth`, `httpx._client.BaseClient._build_request_auth` |
| `page-026` | `398/512` | `77.7%` | `8f95c463bf7796b5` | `httpx._client.BaseClient._build_redirect_request`, `httpx._client.BaseClient._redirect_method` |
| `page-027` | `272/512` | `53.1%` | `4ef4f3111bde4149` | `httpx._client.BaseClient._redirect_url` |
| `page-028` | `456/512` | `89.1%` | `9b094601d4a81238` | `httpx._client.BaseClient._redirect_headers`, `httpx._client.BaseClient._redirect_stream`, `httpx._client.BaseClient._set_timeout` |
| `page-029` | `512/512` | `100.0%` | `785cf1d396c267b2` | `httpx._client.Client` |
| `page-030` | `512/512` | `100.0%` | `fdfef4f4d11bbcee` | `httpx._client.Client.__init__` |
| `page-031` | `391/512` | `76.4%` | `de205385a8ab3a17` | `httpx._client.Client._init_transport`, `httpx._client.Client._init_proxy_transport`, `httpx._client.Client._transport_for_url` |
| `page-032` | `479/512` | `93.6%` | `77fc8409eb9360f5` | `httpx._client.Client.request` |
| `page-033` | `394/512` | `77.0%` | `fac3fd377f943d85` | `httpx._client.Client.stream` |
| `page-034` | `367/512` | `71.7%` | `d287ac4d4c06d079` | `httpx._client.Client.send` |