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

"""Aggregation operations for DataFrame."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import ibis.expr.types as ibis_types

    from leanframe.core.frame import DataFrame


import pandas as pd


class AggregationsMixin:
    _data: "ibis_types.Table"

    """Mixin for DataFrame aggregation methods."""

    def _aggregate(self, op: str, numeric_only: bool = False, **kwargs) -> "DataFrame":
        from leanframe.core.frame import DataFrame

        exprs = {}
        for name in self._data.columns:
            col = self._data[name]
            is_numeric = col.type().is_numeric()
            if numeric_only and not is_numeric:
                continue
            if op == "sum":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot sum non-numeric column '{name}'.")
                exprs[name] = col.sum()
            elif op == "mean":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute mean of non-numeric column '{name}'.")
                exprs[name] = col.mean()
            elif op == "min":
                exprs[name] = col.min()
            elif op == "max":
                exprs[name] = col.max()
            elif op == "std":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute std of non-numeric column '{name}'.")
                exprs[name] = col.std()
            elif op == "var":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute var of non-numeric column '{name}'.")
                exprs[name] = col.var()
            elif op == "count":
                exprs[name] = col.count()
            elif op == "any":
                exprs[name] = col.any()
            elif op == "all":
                exprs[name] = col.all()
            else:
                raise ValueError(f"Unknown aggregation operation '{op}'")

        if not exprs:
            # If all columns were skipped, return an empty DataFrame (or handle as appropriate)
            raise ValueError("No columns to aggregate.")

        return DataFrame(self._data.aggregate(exprs))

    def sum(self, numeric_only: bool = False) -> "DataFrame":
        """Return the sum of the DataFrame over the columns."""
        return self._aggregate("sum", numeric_only=numeric_only)

    def mean(self, numeric_only: bool = False) -> "DataFrame":
        """Return the mean of the DataFrame over the columns."""
        return self._aggregate("mean", numeric_only=numeric_only)

    def min(self, numeric_only: bool = False) -> "DataFrame":
        """Return the min of the DataFrame over the columns."""
        return self._aggregate("min", numeric_only=numeric_only)

    def max(self, numeric_only: bool = False) -> "DataFrame":
        """Return the max of the DataFrame over the columns."""
        return self._aggregate("max", numeric_only=numeric_only)

    def std(self, numeric_only: bool = False) -> "DataFrame":
        """Return the std of the DataFrame over the columns."""
        return self._aggregate("std", numeric_only=numeric_only)

    def var(self, numeric_only: bool = False) -> "DataFrame":
        """Return the var of the DataFrame over the columns."""
        return self._aggregate("var", numeric_only=numeric_only)

    def count(self) -> "DataFrame":
        """Return the number of non-null observations in the DataFrame over the columns."""
        return self._aggregate("count")

    def any(self) -> "DataFrame":
        """Return whether any element is True."""
        return self._aggregate("any")

    def all(self) -> "DataFrame":
        """Return whether all elements are True."""
        return self._aggregate("all")

    def describe(self) -> pd.DataFrame:
        """Return a pandas DataFrame with descriptive statistics."""
        # For now, we will evaluate each stat and combine them into a single pd.DataFrame
        # In a fully lazy implementation, this would involve a complex union/unpivot,
        # but returning pd.DataFrame implies immediate evaluation (as it did for Series).
        count = self.count().to_pandas().iloc[0]
        mean = self.mean(numeric_only=True).to_pandas().iloc[0]
        std = self.std(numeric_only=True).to_pandas().iloc[0]
        min_val = self.min(numeric_only=True).to_pandas().iloc[0]
        max_val = self.max(numeric_only=True).to_pandas().iloc[0]

        # Calculate percentiles
        percentiles = [0.25, 0.50, 0.75]
        q_exprs = {
            f"{int(p * 100)}%": [
                self._data[col].quantile(p) for col in mean.index
            ]
            for p in percentiles
        }

        # Execute quantiles (requires some aggregation magic or multiple queries)
        # To avoid multiple queries we can put them in a single projection,
        # but for simplicity let's evaluate them:
        q_results = {}
        for name, p_list in q_exprs.items():
            aggs = {col: expr for col, expr in zip(mean.index, p_list)}
            q_results[name] = self._data.aggregate(aggs).to_pyarrow().to_pandas().iloc[0]

        stats = {
            "count": count,
            "mean": mean,
            "std": std,
            "min": min_val,
            "25%": q_results["25%"],
            "50%": q_results["50%"],
            "75%": q_results["75%"],
            "max": max_val,
        }

        return pd.DataFrame(stats)
