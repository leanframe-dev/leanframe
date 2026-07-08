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

"""Transformation operations for DataFrame."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import ibis.expr.types as ibis_types

    from leanframe.core.frame import DataFrame




class TransformationsMixin:
    _data: "ibis_types.Table"

    """Mixin for DataFrame transformation methods."""

    def _transform(self, op: str, numeric_only: bool = False, **kwargs) -> "DataFrame":
        from leanframe.core.frame import DataFrame

        exprs = {}
        for name in self._data.columns:
            col = self._data[name]
            is_numeric = col.type().is_numeric()
            if numeric_only and not is_numeric:
                continue
            if op == "cummax":
                exprs[name] = col.cummax()
            elif op == "cummin":
                exprs[name] = col.cummin()
            elif op == "cumprod":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute cumprod of non-numeric column '{name}'.")
                exprs[name] = col.log().cumsum().exp().cast(col.type())
            elif op == "cumsum":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute cumsum of non-numeric column '{name}'.")
                exprs[name] = col.cumsum()
            elif op == "diff":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute diff of non-numeric column '{name}'.")
                exprs[name] = col - col.lag()
            elif op == "abs":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute abs of non-numeric column '{name}'.")
                exprs[name] = col.abs()
            elif op == "round":
                if not numeric_only and not is_numeric:
                    raise TypeError(f"Cannot compute round of non-numeric column '{name}'.")
                n = kwargs.get("n", 0)
                exprs[name] = col.round(n)
            else:
                raise ValueError(f"Unknown transformation operation '{op}'")

        if not exprs:
            raise ValueError("No columns to transform.")

        return DataFrame(self._data.select(**exprs))

    def cummax(self) -> "DataFrame":
        """Return a DataFrame with the cumulative maximum of each element."""
        return self._transform("cummax")

    def cummin(self) -> "DataFrame":
        """Return a DataFrame with the cumulative minimum of each element."""
        return self._transform("cummin")

    def cumprod(self) -> "DataFrame":
        """Return a DataFrame with the cumulative product of each element."""
        return self._transform("cumprod")

    def cumsum(self) -> "DataFrame":
        """Return a DataFrame with the cumulative sum of each element."""
        return self._transform("cumsum")

    def diff(self) -> "DataFrame":
        """Return a DataFrame with the difference between each element and the previous element."""
        return self._transform("diff")

    def abs(self, numeric_only: bool = False) -> "DataFrame":
        """Return a DataFrame with the absolute value of each element."""
        return self._transform("abs", numeric_only=numeric_only)

    def __round__(self, n=0) -> "DataFrame":
        return self._transform("round", n=n)
