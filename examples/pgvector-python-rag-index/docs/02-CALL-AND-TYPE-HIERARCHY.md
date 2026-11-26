# 02 — Call Hierarchy, Type Hierarchy & Super-Implementations (`pgvector-python`)

[← 00-INDEX.md](./00-INDEX.md)

| Type | Kind | Super Types | Sub Types / Implementations | Location |
| :--- | :--- | :--- | :--- | :--- |
| `examples.implicit.example.Base` | class | `DeclarativeBase` | `examples.implicit.example.User`, `examples.implicit.example.Item`, `examples.lightfm.example.User`, `examples.lightfm.example.Item`, `examples.surprise.example.User`, `examples.surprise.example.Item`, `tests.test_sqlalchemy.Item` | `examples/implicit/example.py:13` |
| `examples.implicit.example.User` | class | `examples.implicit.example.Base`, `examples.lightfm.example.Base` | — | `examples/implicit/example.py:17` |
| `examples.implicit.example.Item` | class | `examples.implicit.example.Base`, `examples.lightfm.example.Base` | — | `examples/implicit/example.py:24` |
| `examples.lightfm.example.Base` | class | `DeclarativeBase` | `examples.implicit.example.User`, `examples.implicit.example.Item`, `examples.lightfm.example.User`, `examples.lightfm.example.Item`, `examples.surprise.example.User`, `examples.surprise.example.Item`, `tests.test_sqlalchemy.Item` | `examples/lightfm/example.py:13` |
| `examples.lightfm.example.User` | class | `examples.implicit.example.Base`, `examples.lightfm.example.Base` | — | `examples/lightfm/example.py:17` |
| `examples.lightfm.example.Item` | class | `examples.implicit.example.Base`, `examples.lightfm.example.Base` | — | `examples/lightfm/example.py:24` |
| `examples.surprise.example.Base` | class | `DeclarativeBase` | — | `examples/surprise/example.py:12` |
| `examples.surprise.example.User` | class | `examples.implicit.example.Base`, `examples.lightfm.example.Base` | — | `examples/surprise/example.py:16` |
| `examples.surprise.example.Item` | class | `examples.implicit.example.Base`, `examples.lightfm.example.Base` | — | `examples/surprise/example.py:23` |
| `pgvector.bit.Bit` | class | — | — | `pgvector/bit.py:10` |
| `pgvector.halfvec.HalfVector` | class | — | — | `pgvector/halfvec.py:12` |
| `pgvector.sparsevec.Sentinel` | class | — | — | `pgvector/sparsevec.py:11` |
| `pgvector.sparsevec.SparseVector` | class | — | — | `pgvector/sparsevec.py:18` |
| `pgvector.vector.Vector` | class | — | — | `pgvector/vector.py:12` |
| `pgvector.django.bit.BitField` | class | `Field` | — | `pgvector/django/bit.py:7` |
| `pgvector.django.bit.BitFormField` | class | `forms.CharField` | — | `pgvector/django/bit.py:33` |
| `pgvector.django.extensions.VectorExtension` | class | `CreateExtension` | — | `pgvector/django/extensions.py:6` |
| `pgvector.django.functions.DistanceBase` | class | `Func` | `pgvector.django.functions.L2Distance`, `pgvector.django.functions.MaxInnerProduct`, `pgvector.django.functions.CosineDistance`, `pgvector.django.functions.L1Distance` | `pgvector/django/functions.py:6` |
| `pgvector.django.functions.BitDistanceBase` | class | `Func` | `pgvector.django.functions.HammingDistance`, `pgvector.django.functions.JaccardDistance` | `pgvector/django/functions.py:22` |
| `pgvector.django.functions.L2Distance` | class | `pgvector.django.functions.DistanceBase` | — | `pgvector/django/functions.py:31` |
| `pgvector.django.functions.MaxInnerProduct` | class | `pgvector.django.functions.DistanceBase` | — | `pgvector/django/functions.py:36` |
| `pgvector.django.functions.CosineDistance` | class | `pgvector.django.functions.DistanceBase` | — | `pgvector/django/functions.py:41` |
| `pgvector.django.functions.L1Distance` | class | `pgvector.django.functions.DistanceBase` | — | `pgvector/django/functions.py:46` |
| `pgvector.django.functions.HammingDistance` | class | `pgvector.django.functions.BitDistanceBase` | — | `pgvector/django/functions.py:51` |
| `pgvector.django.functions.JaccardDistance` | class | `pgvector.django.functions.BitDistanceBase` | — | `pgvector/django/functions.py:56` |
| `pgvector.django.halfvec.HalfVectorField` | class | `Field` | — | `pgvector/django/halfvec.py:8` |
| `pgvector.django.halfvec.HalfVectorFormField` | class | `forms.CharField` | — | `pgvector/django/halfvec.py:50` |
| `pgvector.django.indexes.IvfflatIndex` | class | `PostgresIndex` | — | `pgvector/django/indexes.py:5` |
| `pgvector.django.indexes.HnswIndex` | class | `PostgresIndex` | — | `pgvector/django/indexes.py:25` |
| `pgvector.django.sparsevec.SparseVectorField` | class | `Field` | — | `pgvector/django/sparsevec.py:8` |
| `pgvector.django.sparsevec.SparseVectorWidget` | class | `forms.TextInput` | — | `pgvector/django/sparsevec.py:48` |
| `pgvector.django.sparsevec.SparseVectorFormField` | class | `forms.CharField` | — | `pgvector/django/sparsevec.py:55` |
| `pgvector.django.vector.VectorField` | class | `Field` | — | `pgvector/django/vector.py:8` |
| `pgvector.django.vector.VectorFormField` | class | `forms.CharField` | — | `pgvector/django/vector.py:50` |
| `pgvector.peewee.bit.FixedBitField` | class | `Field` | — | `pgvector/peewee/bit.py:5` |
| `pgvector.peewee.halfvec.HalfVectorField` | class | `Field` | — | `pgvector/peewee/halfvec.py:6` |
| `pgvector.peewee.sparsevec.SparseVectorField` | class | `Field` | — | `pgvector/peewee/sparsevec.py:6` |
| `pgvector.peewee.vector.VectorField` | class | `Field` | — | `pgvector/peewee/vector.py:6` |
| `pgvector.psycopg.bit.BitDumper` | class | `Dumper` | `pgvector.psycopg.bit.BitBinaryDumper` | `pgvector/psycopg/bit.py:11` |
| `pgvector.psycopg.bit.BitBinaryDumper` | class | `pgvector.psycopg.bit.BitDumper` | — | `pgvector/psycopg/bit.py:18` |

## Super-Implementations (Method Overrides)

- `pgvector.psycopg.bit.BitBinaryDumper.dump` **overrides** → `pgvector.psycopg.bit.BitDumper.dump`
- `pgvector.psycopg.halfvec.HalfVectorBinaryDumper.dump` **overrides** → `pgvector.psycopg.halfvec.HalfVectorDumper.dump`
- `pgvector.psycopg.halfvec.HalfVectorBinaryLoader.load` **overrides** → `pgvector.psycopg.halfvec.HalfVectorLoader.load`
- `pgvector.psycopg.sparsevec.SparseVectorBinaryDumper.dump` **overrides** → `pgvector.psycopg.sparsevec.SparseVectorDumper.dump`
- `pgvector.psycopg.sparsevec.SparseVectorBinaryLoader.load` **overrides** → `pgvector.psycopg.sparsevec.SparseVectorLoader.load`
- `pgvector.psycopg.vector.VectorBinaryDumper.dump` **overrides** → `pgvector.psycopg.vector.VectorDumper.dump`
- `pgvector.psycopg.vector.VectorBinaryLoader.load` **overrides** → `pgvector.psycopg.vector.VectorLoader.load`