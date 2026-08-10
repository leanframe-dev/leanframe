#!/usr/bin/env python3
"""
Compare Leanframe workflows: pandas-first vs strict-Ibis-until-output.

This demo answers two practical questions in one place:

1) How to work with Leanframe when starting from pandas vs staying in Ibis.
2) A runnable side-by-side example using a tiny nested dataset.

Scope:
- Simple data model (two columns, one nested) for each table.
- Same operations in both approaches:
  - data creation
  - nesting + extraction (NestedHandler.prepare)
  - join on extracted nested fields
  - indexing (.set_index + .head)
  - materialize to pandas only for final display
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ibis
import pandas as pd
import pyarrow as pa

import leanframe
from leanframe.core.frame import DataFrame
from leanframe.core.nested_handler import NestedHandler


def print_concept_comparison() -> None:
    """Explain practical tradeoffs between pandas-first and Ibis-first workflows."""
    print("\n" + "=" * 80)
    print("Leanframe Workflow Comparison: pandas-first vs strict-Ibis")
    print("=" * 80)

    print("\n1) Data Creation")
    print("- pandas-first:")
    print("  Build pandas DataFrames first, then call session.DataFrame(pandas_df).")
    print("  Best when your source is already local/in-memory or notebook-centric.")
    print("- strict-Ibis:")
    print("  Build Arrow/Ibis tables and read them via session.read_ibis(...).")
    print("  Best for backend-native execution (BigQuery-style workflow).")

    print("\n2) Nested Columns")
    print("- Both paths use NestedHandler identically once data is in Leanframe DataFrames.")
    print("- Use handler.prepare(name) to flatten nested fields into underscore columns.")
    print("  Example: profile.email -> profile_email")

    print("\n3) Joins")
    print("- pandas-first:")
    print("  Easy startup, but you materialize data locally early.")
    print("- strict-Ibis:")
    print("  Keep execution in backend expressions as long as possible.")
    print("  Better alignment with warehouse engines and larger datasets.")

    print("\n4) Indexing")
    print("- Indexing API is the same in both approaches: set_index(), iloc, loc, head/tail.")
    print("- Indexing composes well after nested extraction and joins.")

    print("\n5) When to use to_pandas()")
    print("- pandas-first:")
    print("  You already started in pandas, so conversion happened at ingestion.")
    print("- strict-Ibis:")
    print("  Use to_pandas() only at the very end (display/export/debug sample).")

    print("\n6) What Leanframe already feels like")
    print("- DataFrame: columns, dtypes, assign, set_index, head, tail, loc, iloc")
    print("- Series: sum, mean, min, max, count, isin, dtype, to_list")
    print("- NestedHandler: join() and prepare() provide the SQL/Ibis bridge")
    print("- Current gap vs pandas: no full merge/groupby/query/drop/reset_index parity yet")
    print("- Practical takeaway: write pandas-shaped code, but keep execution deferred in Ibis")


def build_pandas_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create tiny nested inputs in pandas for the pandas-first path."""
    customers_pd = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "profile": [
                {"email": "alice@example.com", "age": 30},
                {"email": "bob@example.com", "age": 25},
                {"email": "charlie@example.com", "age": 35},
            ],
        }
    )

    orders_pd = pd.DataFrame(
        {
            "order_id": [101, 102, 103],
            "shipping": [
                {"recipient": {"email": "alice@example.com"}},
                {"recipient": {"email": "bob@example.com"}},
                {"recipient": {"email": "alice@example.com"}},
            ],
        }
    )

    return customers_pd, orders_pd


def build_ibis_inputs(backend: ibis.BaseBackend) -> tuple[DataFrame, DataFrame]:
    """Create the same logical data in Arrow/Ibis for the strict-Ibis path."""
    customers_tbl = backend.create_table(
        f"customers_cmp_{uuid.uuid4().hex[:8]}",
        pa.Table.from_pydict(
            {
                "customer_id": [1, 2, 3],
                "profile": [
                    {"email": "alice@example.com", "age": 30},
                    {"email": "bob@example.com", "age": 25},
                    {"email": "charlie@example.com", "age": 35},
                ],
            },
            schema=pa.schema(
                [
                    pa.field("customer_id", pa.int64()),
                    pa.field(
                        "profile",
                        pa.struct(
                            [pa.field("email", pa.string()), pa.field("age", pa.int64())]
                        ),
                    ),
                ]
            ),
        ),
        temp=True,
    )

    orders_tbl = backend.create_table(
        f"orders_cmp_{uuid.uuid4().hex[:8]}",
        pa.Table.from_pydict(
            {
                "order_id": [101, 102, 103],
                "shipping": [
                    {"recipient": {"email": "alice@example.com"}},
                    {"recipient": {"email": "bob@example.com"}},
                    {"recipient": {"email": "alice@example.com"}},
                ],
            },
            schema=pa.schema(
                [
                    pa.field("order_id", pa.int64()),
                    pa.field(
                        "shipping",
                        pa.struct(
                            [
                                pa.field(
                                    "recipient",
                                    pa.struct([pa.field("email", pa.string())]),
                                )
                            ]
                        ),
                    ),
                ]
            ),
        ),
        temp=True,
    )

    return DataFrame(customers_tbl), DataFrame(orders_tbl)


def run_pipeline(label: str, customers_df: DataFrame, orders_df: DataFrame) -> None:
    """Run the same nesting, join, and indexing pipeline for either input style."""
    print("\n" + "-" * 80)
    print(f"Pipeline: {label}")
    print("-" * 80)

    handler = NestedHandler()
    handler.add("customers", customers_df)
    handler.add("orders", orders_df)

    # NestedHandler already gives a pandas-like join wrapper over Ibis.
    joined_df = handler.join(
        tables={"c": "customers", "o": "orders"},
        on=[("c", "profile_email", "o", "shipping_recipient_email")],
        how="inner",
    )

    print(f"Joined rows: {joined_df['order_id'].count()}")
    print(f"Joined columns: {joined_df.columns.tolist()}")

    # Keep the workflow pandas-shaped: index first, then take head().
    by_age_desc = joined_df.set_index("profile_age", ascending=False)
    top_rows = by_age_desc.head(5)

    print(f"Oldest matched customer age: {joined_df['profile_age'].max()}")

    # Final materialization for output.
    result_pd = top_rows.to_pandas()[
        ["customer_id", "profile_email", "profile_age", "order_id"]
    ]
    print("\nFinal output (pandas, materialized at the end):")
    print(result_pd)


def main() -> None:
    print_concept_comparison()

    backend = ibis.duckdb.connect()
    session = leanframe.Session(backend=backend)

    try:
        # Approach A: pandas-first ingestion.
        customers_pd, orders_pd = build_pandas_inputs()
        customers_from_pd = session.DataFrame(customers_pd)
        orders_from_pd = session.DataFrame(orders_pd)
        run_pipeline("A) pandas-first", customers_from_pd, orders_from_pd)

        # Approach B: strict-Ibis ingestion (Arrow/Ibis until final output).
        customers_ibis, orders_ibis = build_ibis_inputs(backend)
        customers_from_ibis = session.read_ibis(customers_ibis.to_ibis())
        orders_from_ibis = session.read_ibis(orders_ibis.to_ibis())
        run_pipeline(
            "B) strict-Ibis (pandas only at the end)",
            customers_from_ibis,
            orders_from_ibis,
        )
    finally:
        backend.disconnect()


if __name__ == "__main__":
    main()
