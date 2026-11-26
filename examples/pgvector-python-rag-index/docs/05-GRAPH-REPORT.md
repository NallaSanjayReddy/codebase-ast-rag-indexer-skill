# 05 — Knowledge Graph Report (`pgvector-python`)

[← 00-INDEX.md](./00-INDEX.md) | [Interactive Graph (`graph.html`)](./graph.html)

## God Nodes (Most-Connected Core Abstractions)

| Symbol | Kind | Community | Degree | File |
| :--- | :--- | :--- | :--- | :--- |
| `pgvector.vector.Vector` | class | `tests` | `154` | `pgvector/vector.py` |
| `examples.implicit.example.Item` | class | `tests` | `140` | `examples/implicit/example.py` |
| `examples.lightfm.example.Item` | class | `tests` | `140` | `examples/lightfm/example.py` |
| `examples.surprise.example.Item` | class | `tests` | `134` | `examples/surprise/example.py` |
| `pgvector.sparsevec.SparseVector` | class | `tests` | `124` | `pgvector/sparsevec.py` |
| `pgvector.halfvec.HalfVector` | class | `tests` | `75` | `pgvector/halfvec.py` |
| `pgvector.peewee.bit.FixedBitField._distance` | method | `tests` | `71` | `pgvector/peewee/bit.py` |
| `pgvector.peewee.halfvec.HalfVectorField._distance` | method | `tests` | `71` | `pgvector/peewee/halfvec.py` |
| `pgvector.bit.Bit.to_list` | method | `tests` | `70` | `pgvector/bit.py` |
| `pgvector.sqlalchemy.vector.VECTOR` | class | `tests` | `69` | `pgvector/sqlalchemy/vector.py` |
| `pgvector.halfvec.HalfVector.to_list` | method | `tests` | `66` | `pgvector/halfvec.py` |
| `pgvector.sparsevec.SparseVector.to_list` | method | `tests` | `66` | `pgvector/sparsevec.py` |

## Detected Subsystem Communities

| Community | Label | Symbols | Cohesion | Sample Nodes |
| :--- | :--- | :--- | :--- | :--- |
| `#0` | `tests` | `477` | `0.028` | `register_vector`, `Bit`, `to_list`, `to_numpy` |
| `#1` | `pgvector` | `175` | `0.023` | `is_ndarray`, `is_sparse_array`, `__init__`, `__repr__` |
| `#2` | `examples` | `23` | `0.079` | `embed`, `generate_embeddings`, `create_schema`, `insert_data` |

## Surprising Cross-Community Bridges

- `examples.hybrid_search.cross_encoder.create_schema` (`examples`) **`--calls-->`** `pgvector.psycopg.register.register_vector_async` (`pgvector`) [`EXTRACTED`]
- `pgvector.bit.Bit.to_list` (`tests`) **`--calls-->`** `pgvector.bit.Bit.to_text` (`pgvector`) [`AMBIGUOUS`]
- `pgvector.bit.Bit.to_list` (`tests`) **`--calls-->`** `pgvector.halfvec.HalfVector.to_text` (`pgvector`) [`AMBIGUOUS`]
- `pgvector.bit.Bit.to_list` (`tests`) **`--calls-->`** `pgvector.sparsevec.SparseVector.to_text` (`pgvector`) [`AMBIGUOUS`]
- `pgvector.bit.Bit.to_list` (`tests`) **`--calls-->`** `pgvector.vector.Vector.to_text` (`pgvector`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector.to_text` (`pgvector`) **`--calls-->`** `pgvector.bit.Bit.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector.to_text` (`pgvector`) **`--calls-->`** `pgvector.halfvec.HalfVector.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector.to_text` (`pgvector`) **`--calls-->`** `pgvector.sparsevec.SparseVector.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector.to_text` (`pgvector`) **`--calls-->`** `pgvector.vector.Vector.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.halfvec.HalfVector._from_text` (`tests`) [`INFERRED`]
- `pgvector.halfvec.HalfVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.vector.Vector._from_text` (`tests`) [`INFERRED`]
- `pgvector.halfvec.HalfVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.bit.Bit.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.halfvec.HalfVector.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.sparsevec.SparseVector.to_list` (`tests`) [`AMBIGUOUS`]
- `pgvector.halfvec.HalfVector._from_db` (`pgvector`) **`--calls-->`** `pgvector.vector.Vector.to_list` (`tests`) [`AMBIGUOUS`]

## Extracted Rationale & Design Notes (`1` found)

- **`[NOTE]`** `pgvector.psycopg2.register.register_vector` (L8): register_adapter is always global

## Incremental File Manifest Delta
- Added: `0` | Modified: `0` | Unchanged: `74` | Deleted: `0`
