# LeanFrame Table-First API Proposal v2

This document proposes a clearer split between `DataFrame`, `DataFrameHandler`, and `NestedHandler` without introducing a facade. The goal is to keep the current codebase intact while defining a cleaner target architecture that stays lazy, table-first, and Ibis-centered.

## Core idea

LeanFrame should think in terms of tables and expressions, not pandas objects. Users should be able to write familiar column- and table-oriented code, while Ibis remains the execution engine and source of truth for lazy evaluation.

### Responsibilities

#### `DataFrame`
The `DataFrame` object should stay small and expression-oriented.

Keep here:
- `columns`
- `dtypes`
- `__getitem__` for column access
- `assign`
- `to_ibis`
- `to_pandas`
- `set_index`
- `iloc`, `loc`
- `head`, `tail` via `HeadTailMixin`

Do not put here:
- nested schema traversal
- flattening logic
- cross-table orchestration
- backend lineage tracking
- record iteration helpers that force materialization beyond explicit conversion

#### `DataFrameHandler`
This should be a nested-data capability object for one table.

Keep here:
- schema introspection
- nested path discovery
- nested field name mapping
- flatten / extract planning
- nested-aware filtering that returns a new `DataFrame`
- backend qualifier metadata if you want that state attached to a single table

Do not make it a second `DataFrame`.
It should not become the place for general table operations.

#### `NestedHandler`
This should remain orchestration only.

Keep here:
- named table registry
- prepare workflows
- multi-table joins
- lineage tracking
- backend reference coordination across named tables

## Suggested module layout

This keeps the current files, but adds focused v2 modules rather than growing one class.

```text
leanframe/
  core/
    frame.py
    indexing.py
    nested_handler.py
    schema_ops_v2.py
    nested_ops_v2.py
    table_ops_v2.py
```

### Module roles

#### `schema_ops_v2.py`
Shared helpers for nested introspection.

Examples:
- discover struct columns
- walk nested field paths
- map nested path -> extracted column name
- produce metadata without materializing data

#### `nested_ops_v2.py`
Functional helpers for flattening and nested-aware selection.

Examples:
- extract all nested fields
- extract selected nested fields
- filter by extracted columns
- return a new `DataFrame` only

#### `table_ops_v2.py`
Optional future home for table-oriented transformations that are not nested-specific.

Examples:
- projection helpers
- rename helpers
- lightweight column utilities
- future joins or aggregates if they should not live on `DataFrame`

## Suggested API shape

### DataFrame
Keep the public object compact and predictable.

```python
class DataFrame(HeadTailMixin):
    def __getitem__(self, key: str): ...
    def assign(self, **kwargs): ...
    def set_index(self, columns, ascending=True, name=None): ...
    def to_ibis(self): ...
    def to_pandas(self): ...
```

If you want one or two extra convenience methods, they should still stay in the “table-first” spirit:
- `select`
- `rename`
- `drop`

But only if they map cleanly to Ibis and do not introduce pandas-style complexity.

### DataFrameHandler
Keep it narrow and explicit.

```python
class DataFrameHandler:
    def show_structure(self): ...
    def extract_nested_fields(self, verbose=True) -> DataFrame: ...
    def filter_by(self, **kwargs) -> DataFrameHandler: ...
    def get_extracted_column_name(self, nested_path: str) -> str | None: ...
    def get_backend_info(self) -> dict[str, str | None]: ...
```

Potential refinement:
- `columns` should return metadata-derived fields only if that is cheap
- otherwise expose `extracted_fields` and leave `columns` to the extracted `DataFrame`

### NestedHandler
Keep this as a coordinator.

```python
class NestedHandler:
    def add(self, name: str, df: DataFrame, ...): ...
    def get(self, name: str) -> DataFrameHandler: ...
    def prepare(self, name: str, fields=None, verbose=False) -> DataFrame: ...
    def join(self, tables, on=None, predicates=None, how="inner") -> DataFrame: ...
```

## Naming rules

Use names that reflect table work, not pandas imitation.

Good:
- `prepare`
- `extract_nested_fields`
- `filter_by`
- `set_index`
- `select`
- `rename`
- `join`

Avoid:
- multi-index semantics
- hierarchical pandas-like behavior
- methods whose main purpose is to mimic pandas internals

## Growth model for new functionality

Add functionality in layers, not by adding methods everywhere.

### Layer 1: core table operations
These belong closest to `DataFrame`.
- projection
- filtering
- renaming
- ordering/indexing
- limiting
- joins when they are basic and Ibis-native

### Layer 2: nested-specific operations
These belong to `DataFrameHandler` or nested helper modules.
- introspection
- flattening
- nested field selection
- nested-aware filter helpers

### Layer 3: orchestration
These belong to `NestedHandler`.
- table registry
- joins across named tables
- prepare workflows
- lineage / backend tracking

## What this means for the current code

No facade is needed.
Instead, the implementation can remain discoverable by keeping the current classes public and moving the heavy logic into focused helper modules over time.

The current file structure can be improved gradually:
- keep `frame.py` as the user-facing anchor for `DataFrame`
- keep `nested_handler.py` as the orchestration anchor
- extract reusable logic into `_v2` helper modules
- leave the old path in place until the split feels natural

## Practical benefit

This gives LeanFrame a simple story:
- `DataFrame` is the lazy table object
- `DataFrameHandler` understands nested schema shape
- `NestedHandler` coordinates multiple tables
- Ibis performs the actual relational work

That keeps the mental model table-first, lazy, and explicit without drifting into pandas-style complexity.
