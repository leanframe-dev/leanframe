"""
Example: Using Indexing with Nested Data in Leanframe (No pandas ingestion)

This demo mirrors demo_indexing_with_nested.py but avoids pandas for data creation
and ingestion. Data is created as Python dicts, converted to Arrow tables, and
registered on the Ibis backend. pandas is used only at the very end for display
via DataFrame.to_pandas().
"""

from datetime import datetime
import uuid

import ibis
import pyarrow as pa
import leanframe

# Import leanframe components
from leanframe.core.frame import DataFrame, DataFrameHandler
from leanframe.core.nested_handler import NestedHandler


def register_table(
    session: leanframe.Session,
    backend: ibis.BaseBackend,
    prefix: str,
    data: dict,
    schema: pa.Schema | None = None,
) -> DataFrame:
    """Register dict data as an Arrow/Ibis temp table and return a Leanframe DataFrame."""
    table_name = f"{prefix}_{uuid.uuid4().hex[:8]}"
    pa_table = pa.Table.from_pydict(data, schema=schema)
    table = backend.create_table(table_name, pa_table, temp=True)
    return session.read_ibis(table)


def create_sample_nested_data():
    """Create sample data with nested structures for testing."""

    # Sample customer data with nested profiles
    customers_data = {
        "customer_id": [1001, 1002, 1003, 1004, 1005],
        "profile": [
            {"name": "Alice Johnson", "age": 34, "email": "alice@example.com"},
            {"name": "Bob Smith", "age": 28, "email": "bob@example.com"},
            {"name": "Carol Davis", "age": 45, "email": "carol@example.com"},
            {"name": "David Wilson", "age": 31, "email": "david@example.com"},
            {"name": "Eve Martinez", "age": 39, "email": "eve@example.com"},
        ],
        "registration_date": [
            datetime(2024, 1, 15),
            datetime(2024, 2, 20),
            datetime(2023, 11, 5),
            datetime(2024, 3, 10),
            datetime(2023, 12, 18),
        ],
    }

    # Sample order data
    orders_data = {
        "order_id": [5001, 5002, 5003, 5004, 5005, 5006],
        "customer_id": [1001, 1001, 1002, 1003, 1004, 1005],
        "amount": [299.99, 149.50, 599.00, 89.99, 450.00, 199.99],
        "order_date": [
            datetime(2024, 3, 1),
            datetime(2024, 3, 15),
            datetime(2024, 3, 5),
            datetime(2024, 3, 20),
            datetime(2024, 3, 12),
            datetime(2024, 3, 8),
        ],
        "status": [
            "completed",
            "completed",
            "pending",
            "completed",
            "shipped",
            "completed",
        ],
    }

    return customers_data, orders_data


def demo_basic_indexing(session: leanframe.Session, backend: ibis.BaseBackend):
    """Demo 1: Basic indexing without nested data."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Indexing")
    print("=" * 70)

    data = {
        "id": [1, 2, 3, 4, 5],
        "value": [10, 20, 30, 40, 50],
        "timestamp": [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            datetime(2024, 1, 4),
            datetime(2024, 1, 5),
        ],
    }

    df = register_table(session, backend, "idx_basic", data)

    print(f"\nOriginal DataFrame shape: {len(df.columns)} columns")
    print(f"Columns: {df.columns.tolist()}")

    # Set index on timestamp
    print("\nSetting index on 'timestamp' (ascending)...")
    df_indexed = df.set_index("timestamp", ascending=True)
    print(f"Index: {df_indexed.index}")

    # Use iloc
    print("\nUsing .iloc for position-based access:")
    print("\n  First 2 rows (df.iloc[0:2]):")
    first_2 = df_indexed.iloc[0:2]
    print(first_2.to_pandas())

    # Use head/tail
    print("\nUsing .head() and .tail():")
    print("\n  First 3 rows (df.head(3)):")
    print(df_indexed.head(3).to_pandas())

    print("\n  Last 2 rows (df.tail(2)):")
    print(df_indexed.tail(2).to_pandas())

    # Use loc
    print("\nSetting index on 'id' for .loc access:")
    df_by_id = df.set_index("id")
    print("\n  Get row where id=3 (df.loc[3]):")
    print(df_by_id.loc[3].to_pandas())

    print("\n  Get range id=2:4 (df.loc[2:4]):")
    print(df_by_id.loc[2:4].to_pandas())


def demo_nested_data_with_indexing(
    session: leanframe.Session, backend: ibis.BaseBackend
):
    """Demo 2: Indexing with nested data extraction."""
    print("\n" + "=" * 70)
    print("DEMO 2: Nested Data + Indexing")
    print("=" * 70)

    customers_data, _ = create_sample_nested_data()

    profile_schema = pa.struct(
        [
            pa.field("name", pa.string()),
            pa.field("age", pa.int64()),
            pa.field("email", pa.string()),
        ]
    )
    customers_schema = pa.schema(
        [
            pa.field("customer_id", pa.int64()),
            pa.field("profile", profile_schema),
            pa.field("registration_date", pa.timestamp("us")),
        ]
    )

    customers_df = register_table(
        session, backend, "idx_customers", customers_data, customers_schema
    )

    print("\nOriginal nested DataFrame:")
    print(f"Columns: {customers_df.columns.tolist()}")

    # Create handler to analyze nested structure
    print("\nCreating DataFrameHandler to analyze nested structure...")
    handler = DataFrameHandler(customers_df)
    handler.show_structure()

    # Extract nested fields
    print("\nExtracting nested fields...")
    flat_df = handler.extract_nested_fields(verbose=False)
    print(f"Flattened columns: {flat_df.columns.tolist()}")

    # Now apply indexing to the flattened DataFrame
    print("\nSetting index on 'profile_age' (descending - oldest first)...")
    by_age = flat_df.set_index("profile_age", ascending=False)

    print("\nOldest 3 customers (by_age.head(3)):")
    print(
        by_age.head(3).to_pandas()[
            ["customer_id", "profile_name", "profile_age", "profile_email"]
        ]
    )

    print("\nYoungest 2 customers (by_age.tail(2)):")
    print(
        by_age.tail(2).to_pandas()[
            ["customer_id", "profile_name", "profile_age", "profile_email"]
        ]
    )

    # Index by registration date
    print("\nSetting index on 'registration_date' (newest first)...")
    by_date = flat_df.set_index("registration_date", ascending=False)

    print("\nMost recent 3 registrations (by_date.iloc[0:3]):")
    print(
        by_date.iloc[0:3].to_pandas()[
            ["customer_id", "profile_name", "registration_date"]
        ]
    )

    # Use .loc on customer_id
    print("\nSetting index on 'customer_id' for .loc access...")
    by_id = flat_df.set_index("customer_id")

    print("\nGet specific customers (by_id.loc[[1001, 1003]]):")
    print(
        by_id.loc[[1001, 1003]].to_pandas()[
            ["customer_id", "profile_name", "profile_email"]
        ]
    )


def demo_joins_with_indexing(session: leanframe.Session, backend: ibis.BaseBackend):
    """Demo 3: Combining NestedHandler joins with indexing."""
    print("\n" + "=" * 70)
    print("DEMO 3: Joins + Indexing")
    print("=" * 70)

    customers_data, orders_data = create_sample_nested_data()

    profile_schema = pa.struct(
        [
            pa.field("name", pa.string()),
            pa.field("age", pa.int64()),
            pa.field("email", pa.string()),
        ]
    )
    customers_schema = pa.schema(
        [
            pa.field("customer_id", pa.int64()),
            pa.field("profile", profile_schema),
            pa.field("registration_date", pa.timestamp("us")),
        ]
    )

    orders_schema = pa.schema(
        [
            pa.field("order_id", pa.int64()),
            pa.field("customer_id", pa.int64()),
            pa.field("amount", pa.float64()),
            pa.field("order_date", pa.timestamp("us")),
            pa.field("status", pa.string()),
        ]
    )

    customers_df = register_table(
        session, backend, "idx_join_customers", customers_data, customers_schema
    )
    orders_df = register_table(session, backend, "idx_join_orders", orders_data, orders_schema)

    # Setup NestedHandler
    print("\nSetting up NestedHandler...")
    handler = NestedHandler()
    handler.add("customers", customers_df)
    handler.add("orders", orders_df)

    # Prepare customers (extract nested fields)
    print("\nPreparing customers DataFrame (extracting nested fields)...")
    customers_prep = handler.prepare("customers", verbose=False)

    # Add prepared version back
    handler.add("customers_flat", customers_prep)

    # Perform join
    print("\nJoining customers with orders...")
    joined = handler.join(
        tables={"c": "customers_flat", "o": "orders"},
        on=[("c", "customer_id", "o", "customer_id")],
        how="inner",
    )

    print(f"Joined DataFrame columns: {len(joined.columns)}")

    # Apply indexing to joined result
    print("\nSetting index on 'order_date' (most recent first)...")
    by_date = joined.set_index("order_date", ascending=False)

    print("\nMost recent 3 orders (by_date.head(3)):")
    result = by_date.head(3).to_pandas()
    print(result[["order_id", "profile_name", "amount", "order_date", "status"]])

    # Index by amount
    print("\nSetting index on 'amount' (highest first)...")
    by_amount = joined.set_index("amount", ascending=False)

    print("\nTop 3 highest value orders (by_amount.iloc[0:3]):")
    result = by_amount.iloc[0:3].to_pandas()
    print(result[["order_id", "profile_name", "profile_email", "amount", "order_date"]])

    # Use .loc to filter by customer_id
    print("\nSetting index on 'customer_id' for .loc filtering...")
    by_customer = joined.set_index("customer_id")

    print("\nAll orders for customer 1001 (by_customer.loc[1001]):")
    result = by_customer.loc[1001].to_pandas()
    print(result[["order_id", "profile_name", "amount", "order_date"]])


def demo_chaining_operations(session: leanframe.Session, backend: ibis.BaseBackend):
    """Demo 4: Chaining indexing with other operations."""
    print("\n" + "=" * 70)
    print("DEMO 4: Chaining Operations")
    print("=" * 70)

    _, orders_data = create_sample_nested_data()

    orders_schema = pa.schema(
        [
            pa.field("order_id", pa.int64()),
            pa.field("customer_id", pa.int64()),
            pa.field("amount", pa.float64()),
            pa.field("order_date", pa.timestamp("us")),
            pa.field("status", pa.string()),
        ]
    )
    orders_df = register_table(session, backend, "idx_chain_orders", orders_data, orders_schema)

    print("\nOriginal orders:")
    print(orders_df.to_pandas())

    # Chain: filter -> set index -> slice
    print("\nChaining: filter completed orders, order by date, get top 2...")

    # Filter completed orders (using Ibis directly)
    completed = orders_df._data.filter(orders_df._data.status == "completed")
    completed_df = DataFrame(completed)

    # Set index and slice
    by_date = completed_df.set_index("order_date", ascending=False)
    recent_completed = by_date.iloc[0:2]

    print("\nMost recent 2 completed orders:")
    print(recent_completed.to_pandas())

    # Chain: order by amount, get top 3, then filter by customer
    print("\nChaining: order by amount (desc), get top 3...")
    by_amount = orders_df.set_index("amount", ascending=False)
    top_3_value = by_amount.iloc[0:3]

    print("\nTop 3 highest value orders:")
    print(top_3_value.to_pandas())


def demo_error_cases(session: leanframe.Session, backend: ibis.BaseBackend):
    """Demo 5: Common error cases and how to handle them."""
    print("\n" + "=" * 70)
    print("DEMO 5: Error Handling")
    print("=" * 70)

    data = {"id": [1, 2, 3], "value": [10, 20, 30]}
    df = register_table(session, backend, "idx_errors", data)

    # Error 1: Using .iloc without setting index
    print("\nError 1: Using .iloc without index...")
    try:
        df.iloc[0]
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # Error 2: Using .loc without setting index
    print("\nError 2: Using .loc without index...")
    try:
        df.loc[1]
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # Error 3: Setting index on non-existent column
    print("\nError 3: Setting index on non-existent column...")
    try:
        df.set_index("nonexistent")
    except KeyError as e:
        print(f"Caught expected error: {e}")

    # Success: Proper usage
    print("\nProper usage: set index first...")
    df_indexed = df.set_index("id")
    print(f"Index set: {df_indexed.index}")
    print("Now .iloc and .loc work correctly!")
    result = df_indexed.loc[2]
    print(result.to_pandas())


def demo_multi_column_ordering(
    session: leanframe.Session, backend: ibis.BaseBackend
):
    """Demo 6: Multi-column composite ordering (like SQL ORDER BY col1, col2)."""
    print("\n" + "=" * 70)
    print("DEMO 6: Multi-Column Ordering")
    print("=" * 70)

    # Create sample data with priority and timestamp
    task_data = {
        "task_id": [101, 102, 103, 104, 105, 106, 107, 108],
        "priority": [1, 1, 2, 2, 3, 3, 1, 2],
        "timestamp": [
            datetime(2024, 3, 1, 10, 0),
            datetime(2024, 3, 1, 9, 0),
            datetime(2024, 3, 1, 11, 0),
            datetime(2024, 3, 1, 8, 0),
            datetime(2024, 3, 1, 12, 0),
            datetime(2024, 3, 1, 7, 0),
            datetime(2024, 3, 1, 13, 0),
            datetime(2024, 3, 1, 14, 0),
        ],
        "description": [
            "Task A",
            "Task B",
            "Task C",
            "Task D",
            "Task E",
            "Task F",
            "Task G",
            "Task H",
        ],
    }

    task_df = register_table(session, backend, "idx_tasks", task_data)

    print("\nOriginal data (unordered):")
    print(task_df.to_pandas()[["task_id", "priority", "timestamp", "description"]])

    # Single-column ordering
    print("\nSingle-column index on 'priority' (ascending):")
    by_priority = task_df.set_index("priority")
    print(by_priority.to_pandas()[["task_id", "priority", "timestamp", "description"]])
    print("Note: Within each priority level, order is not deterministic")

    # Multi-column ordering - priority ASC, timestamp ASC
    print("\nMulti-column index: ['priority', 'timestamp'] (both ascending):")
    by_priority_time = task_df.set_index(["priority", "timestamp"], ascending=True)
    print(
        by_priority_time.to_pandas()[
            ["task_id", "priority", "timestamp", "description"]
        ]
    )
    print("Result: Ordered by priority, then by earliest timestamp within each priority")

    # Multi-column with different directions
    print("\nMulti-column index: ['priority', 'timestamp'] with [DESC, ASC]:")
    by_priority_desc = task_df.set_index(["priority", "timestamp"], ascending=[False, True])
    print(
        by_priority_desc.to_pandas()[
            ["task_id", "priority", "timestamp", "description"]
        ]
    )
    print("Result: Highest priority first, then earliest timestamp (priority queue)")

    # Use with iloc
    print("\nGetting top 3 tasks with multi-column ordering:")
    print("   (Highest priority first, earliest timestamp breaks ties)")
    top_3 = by_priority_desc.iloc[0:3]
    print(top_3.to_pandas()[["task_id", "priority", "timestamp", "description"]])

    # Example with nested data
    print("\nMulti-column ordering with nested fields:")
    customers_data, _ = create_sample_nested_data()

    profile_schema = pa.struct(
        [
            pa.field("name", pa.string()),
            pa.field("age", pa.int64()),
            pa.field("email", pa.string()),
        ]
    )
    customers_schema = pa.schema(
        [
            pa.field("customer_id", pa.int64()),
            pa.field("profile", profile_schema),
            pa.field("registration_date", pa.timestamp("us")),
        ]
    )

    customers_df = register_table(
        session, backend, "idx_multi_customers", customers_data, customers_schema
    )
    handler = DataFrameHandler(customers_df)
    flat_df = handler.extract_nested_fields(verbose=False)

    # Order by age DESC, then registration_date ASC
    by_age_date = flat_df.set_index(
        ["profile_age", "registration_date"], ascending=[False, True]
    )
    print("\nOrdered by age DESC (nested field), registration_date ASC (regular field):")
    print(
        by_age_date.to_pandas()[
            ["customer_id", "profile_name", "profile_age", "registration_date"]
        ]
    )
    print("\nSQL equivalent: ORDER BY profile_age DESC, registration_date ASC")
    print("\nThis demonstrates ordering across different nesting levels:")
    print("- 'profile_age' comes from nested 'profile' struct")
    print("- 'registration_date' is a regular top-level column")

    # More complex example: order by regular column, then multiple nested fields
    print("\nComplex multi-level ordering:")
    print(
        "Order by registration_date DESC (regular), then profile_age ASC (nested), then profile_name ASC (nested):"
    )
    complex_order = flat_df.set_index(
        ["registration_date", "profile_age", "profile_name"],
        ascending=[False, True, True],
    )
    result = complex_order.to_pandas()[
        ["customer_id", "profile_name", "profile_age", "registration_date"]
    ]
    print(result)
    print("\nThis shows:")
    print("- Primary sort: newest registrations first (regular column)")
    print("- Secondary sort: youngest first within same date (nested field)")
    print("- Tertiary sort: alphabetical by name for same age (nested field)")


if __name__ == "__main__":
    print("\n" + "LEANFRAME INDEXING EXAMPLES (NO PANDAS INGESTION)" + "\n")
    print("This demo uses Arrow/Ibis for data creation and pandas only for output")

    backend = ibis.duckdb.connect()
    session = leanframe.Session(backend=backend)

    try:
        # Run all demos
        demo_basic_indexing(session, backend)
        demo_nested_data_with_indexing(session, backend)
        demo_joins_with_indexing(session, backend)
        demo_chaining_operations(session, backend)
        demo_error_cases(session, backend)
        demo_multi_column_ordering(session, backend)

        print("\n" + "=" * 70)
        print("All demos completed!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("1. Always set index explicitly for deterministic ordering")
        print("2. Use .iloc for position-based access (with ordering)")
        print("3. Use .loc for value-based filtering (on index column)")
        print("4. Indexing works seamlessly with nested data extraction")
        print("5. Chain operations: extract -> flatten -> index -> slice")
        print("6. Multi-column ordering: like SQL ORDER BY col1 DESC, col2 ASC")
        print("\nSee docs/indexing_guide.md for more details!")
    finally:
        backend.disconnect()
