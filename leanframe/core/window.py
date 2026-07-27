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

"""Windowed operations on DataFrames."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    from leanframe.core.frame import DataFrame


class Rolling:
    """Windowed operations on DataFrames."""

    def __init__(
        self,
        obj: DataFrame,
        window: int,
        min_periods: int | None = None,
    ):
        """Initialize a Rolling object.

        Args:
            obj: The DataFrame to apply rolling operations to.
            window: The size of the moving window.
            min_periods: Minimum number of observations in window required to
                have a value. Defaults to window size.
        """
        self._obj = obj
        self._window = window
        self._min_periods = min_periods if min_periods is not None else window

    def _apply_aggregation(self, op: str, **kwargs: Any) -> DataFrame:
        from leanframe.core.frame import DataFrame

        t = self._obj._data

        w = ibis.window(preceding=self._window - 1, following=0)

        exprs = []
        for c in t.columns:
            col = t[c]

            if op == "count":
                agg = col.count()
            elif op == "sum":
                agg = col.sum()
            elif op == "mean":
                agg = col.mean()
            elif op == "std":
                agg = col.std(how="sample")
            else:
                raise NotImplementedError(f"Unsupported operation: {op}")

            agg_over = agg.over(w)

            if op == "count":
                # For count, min_periods applies to the TOTAL number of rows in the window (including nulls)
                # We can trick Ibis into counting all rows by coalescing the column.
                valid_count = ibis.coalesce(col, 0).count().over(w)
            else:
                # For others, min_periods applies to the number of non-null observations
                valid_count = col.count().over(w)

            final_expr = ibis.ifelse(
                valid_count >= self._min_periods, agg_over, ibis.null()
            ).name(c)
            exprs.append(final_expr)

        return DataFrame(t.select(exprs))

    def count(self) -> DataFrame:
        """Calculate the rolling count."""
        return self._apply_aggregation("count")

    def sum(self) -> DataFrame:
        """Calculate the rolling sum."""
        return self._apply_aggregation("sum")

    def mean(self) -> DataFrame:
        """Calculate the rolling mean."""
        return self._apply_aggregation("mean")

    def std(self) -> DataFrame:
        """Calculate the rolling standard deviation."""
        return self._apply_aggregation("std")
