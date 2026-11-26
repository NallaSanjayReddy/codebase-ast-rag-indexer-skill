# 05 — Knowledge Graph Report (`pgvector-python`)

[← 00-INDEX.md](./00-INDEX.md) | [Interactive Graph (`graph.html`)](./graph.html)

## God Nodes (Most-Connected Core Abstractions)

| Symbol | Kind | Community | Degree | File |
| :--- | :--- | :--- | :--- | :--- |
| `pgvector.vector.Vector` | class | `pgvector/psycopg` | `154` | `pgvector/vector.py` |
| `pgvector.sparsevec.SparseVector` | class | `pgvector/psycopg` | `124` | `pgvector/sparsevec.py` |
| `pgvector.halfvec.HalfVector` | class | `pgvector/psycopg` | `75` | `pgvector/halfvec.py` |
| `pgvector.sqlalchemy.vector.VECTOR` | class | `pgvector/sqlalchemy` | `69` | `pgvector/sqlalchemy/vector.py` |
| `pgvector.bit.Bit` | class | `pgvector/psycopg` | `65` | `pgvector/bit.py` |
| `pgvector.halfvec.HalfVector.to_list` | method | `pgvector` | `64` | `pgvector/halfvec.py` |
| `pgvector.bit.Bit.to_list` | method | `pgvector/psycopg` | `61` | `pgvector/bit.py` |
| `pgvector.peewee.halfvec.HalfVectorField._distance` | method | `pgvector/peewee` | `61` | `pgvector/peewee/halfvec.py` |
| `pgvector.sparsevec.SparseVector.to_list` | method | `pgvector` | `60` | `pgvector/sparsevec.py` |
| `pgvector.peewee.bit.FixedBitField._distance` | method | `pgvector/peewee` | `59` | `pgvector/peewee/bit.py` |
| `pgvector.sparsevec.SparseVector.from_binary` | method | `pgvector/psycopg` | `55` | `pgvector/sparsevec.py` |
| `pgvector.bit.Bit.from_binary` | method | `pgvector/psycopg` | `54` | `pgvector/bit.py` |

## Detected Subsystem Communities (Production-Isolated)

| Community | Label | Symbols | Cohesion | Sample Nodes |
| :--- | :--- | :--- | :--- | :--- |
| `#0` | `pgvector` | `88` | `0.035` | `is_ndarray`, `is_sparse_array`, `__init__`, `__eq__` |
| `#1` | `pgvector/psycopg` | `81` | `0.053` | `register_vector`, `Bit`, `__repr__`, `to_list` |
| `#2` | `pgvector/django` | `38` | `0.048` | `BitField`, `deconstruct`, `db_type`, `formfield` |
| `#3` | `pgvector/sqlalchemy` | `27` | `0.0` | `BIT`, `process_bind_param`, `Comparator`, `hamming_distance` |
| `#4` | `pgvector/peewee` | `26` | `0.043` | `FixedBitField`, `get_modifiers`, `_distance`, `hamming_distance` |
| `#5` | `examples/implicit` | `8` | `0.429` | `Base`, `User`, `Item`, `Base` |
| `#6` | `examples/hybrid_search` | `6` | `0.333` | `create_schema`, `insert_data`, `semantic_search`, `keyword_search` |
| `#7` | `examples/openai` | `4` | `0.5` | `embed`, `embed`, `embed`, `embed` |
| `#8` | `pgvector/psycopg2` | `3` | `0.0` | `HalfvecAdapter`, `SparsevecAdapter`, `VectorAdapter` |
| `#9` | `examples/colpali` | `1` | `0.0` | `generate_embeddings` |
| `#10` | `examples/image_search` | `1` | `0.0` | `generate_embeddings` |
| `#11` | `examples/imagehash` | `1` | `0.0` | `hash_image` |
| `#12` | `examples/rdkit` | `1` | `0.0` | `generate_fingerprint` |
| `#13` | `examples/surprise` | `1` | `0.0` | `Base` |
| `#14` | `tests` | `389` | `0.002` | `TestAsyncpg`, `setup_connection`, `test_vector`, `test_halfvec` |

## Surprising Cross-Community Bridges

- `examples.hybrid_search.cross_encoder.create_schema` (`examples/hybrid_search`) **`--calls-->`** `pgvector.psycopg.register.register_vector_async` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.halfvec.HalfVector.to_text` (`pgvector/psycopg`) **`--calls-->`** `pgvector.halfvec.HalfVector.to_list` (`pgvector`) [`EXTRACTED`]
- `pgvector.halfvec.HalfVector.from_text` (`pgvector/psycopg`) **`--calls-->`** `pgvector.halfvec.HalfVector._from_text` (`pgvector`) [`EXTRACTED`]
- `pgvector.halfvec.HalfVector._to_db` (`pgvector`) **`--calls-->`** `pgvector.halfvec.HalfVector.to_text` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.sparsevec.SparseVector._to_db` (`pgvector`) **`--calls-->`** `pgvector.sparsevec.SparseVector.to_text` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.sparsevec.SparseVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.sparsevec.SparseVector.from_text` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.sparsevec.SparseVector._from_db` (`pgvector`) **`--uses_type-->`** `pgvector.sparsevec.SparseVector` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.vector.Vector.from_text` (`pgvector`) **`--uses_type-->`** `pgvector.vector.Vector` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.django.sparsevec.SparseVectorField.from_db_value` (`pgvector`) **`--uses_type-->`** `pgvector.sparsevec.SparseVector` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.django.sparsevec.SparseVectorField.to_python` (`pgvector`) **`--uses_type-->`** `pgvector.sparsevec.SparseVector` (`pgvector/psycopg`) [`EXTRACTED`]
- `pgvector.peewee.sparsevec.SparseVectorField.python_value` (`pgvector`) **`--uses_type-->`** `pgvector.sparsevec.SparseVector` (`pgvector/psycopg`) [`EXTRACTED`]

## Import Cycles

- *No module import cycles detected.*

## Extracted Rationale & Design Notes (`1` found)

- **`[NOTE]`** `pgvector.psycopg2.register.register_vector` (L8): register_adapter is always global

## Incremental File Manifest Delta
- Added: `0` | Modified: `0` | Unchanged: `74` | Deleted: `0`
