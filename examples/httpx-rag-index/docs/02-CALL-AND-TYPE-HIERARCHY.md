# 02 — Call Hierarchy, Type Hierarchy & Super-Implementations (`httpx`)

[← 00-INDEX.md](./00-INDEX.md)

| Type | Kind | Super Types | Sub Types / Implementations | Location |
| :--- | :--- | :--- | :--- | :--- |
| `httpx._auth.Auth` | class | — | `httpx._auth.FunctionAuth`, `httpx._auth.BasicAuth`, `httpx._auth.NetRCAuth`, `httpx._auth.DigestAuth`, `tests.client.test_auth.RepeatAuth`, `tests.client.test_auth.ResponseBodyAuth`, `tests.client.test_auth.SyncOrAsyncAuth` | `httpx/_auth.py:22` |
| `httpx._auth.FunctionAuth` | class | `httpx._auth.Auth` | — | `httpx/_auth.py:113` |
| `httpx._auth.BasicAuth` | class | `httpx._auth.Auth` | — | `httpx/_auth.py:126` |
| `httpx._auth.NetRCAuth` | class | `httpx._auth.Auth` | — | `httpx/_auth.py:145` |
| `httpx._auth.DigestAuth` | class | `httpx._auth.Auth` | — | `httpx/_auth.py:175` |
| `httpx._auth._DigestAuthChallenge` | class | `typing.NamedTuple` | — | `httpx/_auth.py:343` |
| `httpx._client.UseClientDefault` | class | — | — | `httpx/_client.py:94` |
| `httpx._client.ClientState` | class | `enum.Enum` | — | `httpx/_client.py:125` |
| `httpx._client.BoundSyncStream` | class | `httpx._types.SyncByteStream` | — | `httpx/_client.py:139` |
| `httpx._client.BoundAsyncStream` | class | `httpx._types.AsyncByteStream` | — | `httpx/_client.py:162` |
| `httpx._client.BaseClient` | class | — | `httpx._client.Client`, `httpx._client.AsyncClient` | `httpx/_client.py:188` |
| `httpx._client.Client` | class | `httpx._client.BaseClient` | — | `httpx/_client.py:594` |
| `httpx._client.AsyncClient` | class | `httpx._client.BaseClient` | — | `httpx/_client.py:1307` |
| `httpx._config.UnsetType` | class | — | — | `httpx/_config.py:16` |
| `httpx._config.Timeout` | class | — | — | `httpx/_config.py:72` |
| `httpx._config.Limits` | class | — | — | `httpx/_config.py:159` |
| `httpx._config.Proxy` | class | — | — | `httpx/_config.py:201` |
| `httpx._content.ByteStream` | class | `httpx._types.AsyncByteStream`, `httpx._types.SyncByteStream` | — | `httpx/_content.py:31` |
| `httpx._content.IteratorByteStream` | class | `httpx._types.SyncByteStream` | — | `httpx/_content.py:42` |
| `httpx._content.AsyncIteratorByteStream` | class | `httpx._types.AsyncByteStream` | — | `httpx/_content.py:67` |
| `httpx._content.UnattachedStream` | class | `httpx._types.AsyncByteStream`, `httpx._types.SyncByteStream` | — | `httpx/_content.py:92` |
| `httpx._decoders.ContentDecoder` | class | — | `httpx._decoders.IdentityDecoder`, `httpx._decoders.DeflateDecoder`, `httpx._decoders.GZipDecoder`, `httpx._decoders.BrotliDecoder`, `httpx._decoders.ZStandardDecoder`, `httpx._decoders.MultiDecoder` | `httpx/_decoders.py:36` |
| `httpx._decoders.IdentityDecoder` | class | `httpx._decoders.ContentDecoder` | — | `httpx/_decoders.py:44` |
| `httpx._decoders.DeflateDecoder` | class | `httpx._decoders.ContentDecoder` | — | `httpx/_decoders.py:56` |
| `httpx._decoders.GZipDecoder` | class | `httpx._decoders.ContentDecoder` | — | `httpx/_decoders.py:85` |
| `httpx._decoders.BrotliDecoder` | class | `httpx._decoders.ContentDecoder` | — | `httpx/_decoders.py:108` |
| `httpx._decoders.ZStandardDecoder` | class | `httpx._decoders.ContentDecoder` | — | `httpx/_decoders.py:161` |
| `httpx._decoders.MultiDecoder` | class | `httpx._decoders.ContentDecoder` | — | `httpx/_decoders.py:203` |
| `httpx._decoders.ByteChunker` | class | — | — | `httpx/_decoders.py:228` |
| `httpx._decoders.TextChunker` | class | — | — | `httpx/_decoders.py:267` |
| `httpx._decoders.TextDecoder` | class | — | — | `httpx/_decoders.py:306` |
| `httpx._decoders.LineDecoder` | class | — | — | `httpx/_decoders.py:321` |
| `httpx._exceptions.HTTPError` | class | `Exception` | `httpx._exceptions.RequestError`, `httpx._exceptions.HTTPStatusError` | `httpx/_exceptions.py:74` |
| `httpx._exceptions.RequestError` | class | `httpx._exceptions.HTTPError` | `httpx._exceptions.TransportError`, `httpx._exceptions.DecodingError`, `httpx._exceptions.TooManyRedirects` | `httpx/_exceptions.py:107` |
| `httpx._exceptions.TransportError` | class | `httpx._exceptions.RequestError` | `httpx._exceptions.TimeoutException`, `httpx._exceptions.NetworkError`, `httpx._exceptions.ProxyError`, `httpx._exceptions.UnsupportedProtocol`, `httpx._exceptions.ProtocolError` | `httpx/_exceptions.py:123` |
| `httpx._exceptions.TimeoutException` | class | `httpx._exceptions.TransportError` | `httpx._exceptions.ConnectTimeout`, `httpx._exceptions.ReadTimeout`, `httpx._exceptions.WriteTimeout`, `httpx._exceptions.PoolTimeout` | `httpx/_exceptions.py:132` |
| `httpx._exceptions.ConnectTimeout` | class | `httpx._exceptions.TimeoutException` | — | `httpx/_exceptions.py:140` |
| `httpx._exceptions.ReadTimeout` | class | `httpx._exceptions.TimeoutException` | — | `httpx/_exceptions.py:146` |
| `httpx._exceptions.WriteTimeout` | class | `httpx._exceptions.TimeoutException` | — | `httpx/_exceptions.py:152` |
| `httpx._exceptions.PoolTimeout` | class | `httpx._exceptions.TimeoutException` | — | `httpx/_exceptions.py:158` |

## Super-Implementations (Method Overrides)

- `httpx._auth.FunctionAuth.auth_flow` **overrides** → `httpx._auth.Auth.auth_flow`
- `httpx._auth.BasicAuth.auth_flow` **overrides** → `httpx._auth.Auth.auth_flow`
- `httpx._auth.NetRCAuth.auth_flow` **overrides** → `httpx._auth.Auth.auth_flow`
- `httpx._auth.DigestAuth.auth_flow` **overrides** → `httpx._auth.Auth.auth_flow`
- `httpx._client.BoundSyncStream.__iter__` **overrides** → `httpx._types.SyncByteStream.__iter__`
- `httpx._client.BoundSyncStream.close` **overrides** → `httpx._types.SyncByteStream.close`
- `httpx._client.BoundAsyncStream.__aiter__` **overrides** → `httpx._types.AsyncByteStream.__aiter__`
- `httpx._client.BoundAsyncStream.aclose` **overrides** → `httpx._types.AsyncByteStream.aclose`
- `httpx._client.Client.__init__` **overrides** → `httpx._client.BaseClient.__init__`
- `httpx._client.AsyncClient.__init__` **overrides** → `httpx._client.BaseClient.__init__`
- `httpx._content.ByteStream.__iter__` **overrides** → `httpx._types.SyncByteStream.__iter__`
- `httpx._content.ByteStream.__aiter__` **overrides** → `httpx._types.AsyncByteStream.__aiter__`
- `httpx._content.IteratorByteStream.__iter__` **overrides** → `httpx._types.SyncByteStream.__iter__`
- `httpx._content.AsyncIteratorByteStream.__aiter__` **overrides** → `httpx._types.AsyncByteStream.__aiter__`
- `httpx._content.UnattachedStream.__iter__` **overrides** → `httpx._types.SyncByteStream.__iter__`
- `httpx._content.UnattachedStream.__aiter__` **overrides** → `httpx._types.AsyncByteStream.__aiter__`
- `httpx._decoders.IdentityDecoder.decode` **overrides** → `httpx._decoders.ContentDecoder.decode`
- `httpx._decoders.IdentityDecoder.flush` **overrides** → `httpx._decoders.ContentDecoder.flush`
- `httpx._decoders.DeflateDecoder.decode` **overrides** → `httpx._decoders.ContentDecoder.decode`
- `httpx._decoders.DeflateDecoder.flush` **overrides** → `httpx._decoders.ContentDecoder.flush`
- `httpx._decoders.GZipDecoder.decode` **overrides** → `httpx._decoders.ContentDecoder.decode`
- `httpx._decoders.GZipDecoder.flush` **overrides** → `httpx._decoders.ContentDecoder.flush`
- `httpx._decoders.BrotliDecoder.decode` **overrides** → `httpx._decoders.ContentDecoder.decode`
- `httpx._decoders.BrotliDecoder.flush` **overrides** → `httpx._decoders.ContentDecoder.flush`
- `httpx._decoders.ZStandardDecoder.decode` **overrides** → `httpx._decoders.ContentDecoder.decode`
- `httpx._decoders.ZStandardDecoder.flush` **overrides** → `httpx._decoders.ContentDecoder.flush`
- `httpx._decoders.MultiDecoder.decode` **overrides** → `httpx._decoders.ContentDecoder.decode`
- `httpx._decoders.MultiDecoder.flush` **overrides** → `httpx._decoders.ContentDecoder.flush`
- `httpx._exceptions.RequestError.__init__` **overrides** → `httpx._exceptions.HTTPError.__init__`
- `httpx._exceptions.HTTPStatusError.__init__` **overrides** → `httpx._exceptions.HTTPError.__init__`