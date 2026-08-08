# Copyright 2025 Google LLC, LeanFrame Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import pandas as pd
import pandas.testing as tm
import pyarrow as pa
import pytest

import leanframe


def test_dataframe_dtypes(session: leanframe.Session):
    df_pd = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
            "col3": [1.1, 2.2, 3.3],
        }
    ).astype(
        {
            "col1": pd.ArrowDtype(pa.int64()),
            "col2": pd.ArrowDtype(pa.string()),
            "col3": pd.ArrowDtype(pa.float64()),
        }
    )
    df_lf = session.DataFrame(df_pd)
    result = df_lf.dtypes
    expected = pd.Series(
        [
            pd.ArrowDtype(pa.int64()),
            pd.ArrowDtype(pa.string()),
            pd.ArrowDtype(pa.float64()),
        ],
        index=["col1", "col2", "col3"],
        name="dtypes",
    )
    tm.assert_series_equal(result, expected)


def test_dataframe_dtypes_complex(session: leanframe.Session):
    pa_table = pa.Table.from_pydict(
        {
            "array_col": [[1, 2], [3, 4]],
            "struct_col": [{"a": 1, "b": "c"}, {"a": 2, "b": "d"}],
        },
        schema=pa.schema(
            [
                pa.field("array_col", pa.list_(pa.int64())),
                pa.field(
                    "struct_col",
                    pa.struct([("a", pa.int64()), ("b", pa.string())]),
                ),
            ]
        ),
    )
    df_pd = pa_table.to_pandas(types_mapper=pd.ArrowDtype)
    df_lf = session.DataFrame(df_pd)
    result = df_lf.dtypes
    expected = pd.Series(
        [
            pd.ArrowDtype(pa.list_(pa.int64())),
            pd.ArrowDtype(pa.struct([("a", pa.int64()), ("b", pa.string())])),
        ],
        index=["array_col", "struct_col"],
        name="dtypes",
    )
    tm.assert_series_equal(result, expected)


def test_dataframe_getitem_with_column(session: leanframe.Session):
    """Read a table with simple scalar values."""

    df_lf = session.DataFrame(
        pd.DataFrame(
            {
                "col1": [1, 2, 3],
                "col2": ["a", "b", "c"],
            }
        )
    )
    series_1 = df_lf["col1"]
    assert isinstance(series_1, leanframe.core.frame.DataFrame)
    assert series_1.columns.tolist() == ["col1"]
    # TODO(tswast): check dtype

    series_2 = df_lf["col2"]
    assert isinstance(series_2, leanframe.core.frame.DataFrame)
    assert series_2.columns.tolist() == ["col2"]
    # TODO(tswast): check dtype


def test_dataframe_assign_scalar(session: leanframe.Session):
    df_pd = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        }
    ).astype(
        {
            "col1": pd.ArrowDtype(pa.int64()),
            "col2": pd.ArrowDtype(pa.string()),
        }
    )
    df_lf = session.DataFrame(df_pd)
    result_lf = df_lf.assign(col3=4)
    expected_pd = df_pd.assign(col3=4).astype({"col3": pd.ArrowDtype(pa.int8())})
    tm.assert_frame_equal(result_lf.to_pandas(), expected_pd)


def test_dataframe_assign_series(session: leanframe.Session):
    df_pd = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        }
    ).astype(
        {
            "col1": pd.ArrowDtype(pa.int64()),
            "col2": pd.ArrowDtype(pa.string()),
        }
    )
    df_lf = session.DataFrame(df_pd)
    series_pd = pd.Series([4, 5, 6], name="col3").astype(pd.ArrowDtype(pa.int64()))

    # Use session.col("col1") instead of df_lf["col1"] to construct the deferred expression
    series_lf = session.col("col1") + 3

    result_lf = df_lf.assign(col3=series_lf)
    expected_pd = df_pd.assign(col3=series_pd)
    tm.assert_frame_equal(result_lf.to_pandas(), expected_pd)


def test_dataframe_assign_multiple(session: leanframe.Session):
    df_pd = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        }
    ).astype(
        {
            "col1": pd.ArrowDtype(pa.int64()),
            "col2": pd.ArrowDtype(pa.string()),
        }
    )
    df_lf = session.DataFrame(df_pd)
    series_pd = pd.Series([4, 5, 6], name="col3").astype(pd.ArrowDtype(pa.int64()))

    # Use session.col("col1")
    series_lf = session.col("col1") + 3

    result_lf = df_lf.assign(col3=series_lf, col4="d")
    expected_pd = df_pd.assign(col3=series_pd, col4="d").astype(
        {"col4": pd.ArrowDtype(pa.string())}
    )
    tm.assert_frame_equal(result_lf.to_pandas(), expected_pd)


def test_dataframe_assign_overwrite(session: leanframe.Session):
    df_pd = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        }
    ).astype(
        {
            "col1": pd.ArrowDtype(pa.int64()),
            "col2": pd.ArrowDtype(pa.string()),
        }
    )
    df_lf = session.DataFrame(df_pd)

    # Use session.col("col1")
    result_lf = df_lf.assign(col1=session.col("col1") * 2)
    expected_pd = df_pd.assign(col1=df_pd["col1"] * 2)
    tm.assert_frame_equal(result_lf.to_pandas(), expected_pd)


def test_dataframe_drop_columns(session: leanframe.Session):
    df_pd = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
        "col3": [1.1, 2.2, 3.3],
    }).astype({
        "col1": pd.ArrowDtype(pa.int64()),
        "col2": pd.ArrowDtype(pa.string()),
        "col3": pd.ArrowDtype(pa.float64()),
    })
    df_lf = session.DataFrame(df_pd)

    # Drop single column
    result1 = df_lf.drop(columns="col2")
    expected1 = df_pd.drop(columns="col2")
    tm.assert_frame_equal(result1.to_pandas(), expected1)

    # Drop multiple columns
    result2 = df_lf.drop(columns=["col1", "col3"])
    expected2 = df_pd.drop(columns=["col1", "col3"])
    tm.assert_frame_equal(result2.to_pandas(), expected2)

    # Drop using labels and axis=1
    result3 = df_lf.drop(["col2"], axis=1)
    expected3 = df_pd.drop(["col2"], axis=1)
    tm.assert_frame_equal(result3.to_pandas(), expected3)

def test_dataframe_drop_errors(session: leanframe.Session):
    df_pd = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
    })
    df_lf = session.DataFrame(df_pd)

    # Test errors='raise' (default)
    with pytest.raises(KeyError, match=r"\['missing'\] not found in axis"):
        df_lf.drop(columns="missing")

    with pytest.raises(KeyError, match=r"\['missing'\] not found in axis"):
        df_lf.drop(columns=["col1", "missing"])

    # Test errors='ignore'
    result = df_lf.drop(columns=["col1", "missing"], errors="ignore")
    # Need to handle pandas type conversion for assert
    tm.assert_frame_equal(result.to_pandas(), df_lf.to_pandas().drop(columns=["col1", "missing"], errors="ignore"))

def test_dataframe_drop_unsupported(session: leanframe.Session):
    df_pd = pd.DataFrame({
        "col1": [1, 2, 3],
    })
    df_lf = session.DataFrame(df_pd)

    with pytest.raises(NotImplementedError, match="inplace=True is not supported"):
        df_lf.drop(columns="col1", inplace=True)

    with pytest.raises(NotImplementedError, match="level is not supported"):
        df_lf.drop(columns="col1", level=1)

    with pytest.raises(NotImplementedError, match="Dropping rows by index is not supported"):
        df_lf.drop(index=[0])

    with pytest.raises(NotImplementedError, match="Dropping rows by index is not supported"):
        df_lf.drop(labels=[0], axis=0)

    with pytest.raises(ValueError, match="Need to specify at least one of 'labels', 'index' or 'columns'"):
        df_lf.drop()
