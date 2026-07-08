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

"""Comparison operations for DataFrame."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import ibis.expr.types as ibis_types

    from leanframe.core.frame import DataFrame



class ComparisonsMixin:
    _data: "ibis_types.Table"

    """Mixin for DataFrame comparison methods."""

    def _compare(self, op: str, other) -> "DataFrame":
        from leanframe.core.frame import DataFrame

        exprs = {}
        for name in self._data.columns:
            col = self._data[name]
            other_val = getattr(other, "_data", other)

            if op == "lt":
                exprs[name] = col < other_val
            elif op == "gt":
                exprs[name] = col > other_val
            elif op == "le":
                exprs[name] = col <= other_val
            elif op == "ge":
                exprs[name] = col >= other_val
            elif op == "ne":
                exprs[name] = col != other_val
            elif op == "eq":
                exprs[name] = col == other_val
            elif op == "isin":
                exprs[name] = col.isin(other_val)
            else:
                raise ValueError(f"Unknown comparison operation '{op}'")

        return DataFrame(self._data.select(**exprs))

    def __lt__(self, other) -> "DataFrame":
        return self._compare("lt", other)

    def __gt__(self, other) -> "DataFrame":
        return self._compare("gt", other)

    def __le__(self, other) -> "DataFrame":
        return self._compare("le", other)

    def __ge__(self, other) -> "DataFrame":
        return self._compare("ge", other)

    def __ne__(self, other) -> "DataFrame":  # type: ignore[override]
        return self._compare("ne", other)

    def __eq__(self, other) -> "DataFrame":  # type: ignore[override]
        return self._compare("eq", other)

    def lt(self, other) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is less than the other."""
        return self < other

    def gt(self, other) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is greater than the other."""
        return self > other

    def le(self, other) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is less than or equal to the other."""
        return self <= other

    def ge(self, other) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is greater than or equal to the other."""
        return self >= other

    def ne(self, other) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is not equal to the other."""
        return self != other

    def eq(self, other) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is equal to the other."""
        return self == other

    def isin(self, values) -> "DataFrame":
        """Return a boolean DataFrame showing whether each element is exactly contained in the passed sequence of values."""
        return self._compare("isin", values)
