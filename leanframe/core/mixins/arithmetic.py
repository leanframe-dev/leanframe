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

"""Arithmetic operations for DataFrame."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import ibis.expr.types as ibis_types

    from leanframe.core.frame import DataFrame



class ArithmeticMixin:
    _data: "ibis_types.Table"

    """Mixin for DataFrame arithmetic methods."""

    def _arithmetic(self, op: str, other) -> "DataFrame":
        from leanframe.core.frame import DataFrame

        exprs = {}
        for name in self._data.columns:
            col = self._data[name]


            # If other is an Expression or Ibis scalar/column
            other_val = getattr(other, "_data", other)
            if hasattr(other, "_data") and hasattr(other_val, "columns") and len(other_val.columns) == 1:
                import ibis.expr.operations as ops
                op = other_val.op()
                col_name = other_val.columns[0]
                if isinstance(op, ops.Project):
                    other_val = op.values[col_name].to_expr()
                else:
                    other_val = other_val[col_name]


            # Or if it's another DataFrame, this would need joining logic which we don't have yet.
            # Assuming scalar or Expression for now, matching the previous Series behavior.
            if op == "add":
                exprs[name] = col + other_val
            elif op == "radd":
                exprs[name] = other_val + col
            elif op == "mul":
                exprs[name] = col * other_val
            elif op == "rmul":
                exprs[name] = other_val * col
            elif op == "sub":
                exprs[name] = col - other_val
            elif op == "rsub":
                exprs[name] = other_val - col
            elif op == "truediv":
                exprs[name] = col / other_val
            elif op == "rtruediv":
                exprs[name] = other_val / col
            elif op == "floordiv":
                exprs[name] = col // other_val
            elif op == "rfloordiv":
                exprs[name] = other_val // col
            elif op == "pow":
                exprs[name] = col ** other_val
            elif op == "rpow":
                exprs[name] = other_val ** col
            else:
                raise ValueError(f"Unknown arithmetic operation '{op}'")

        return DataFrame(self._data.select(**exprs))

    def __add__(self, other) -> "DataFrame":
        return self._arithmetic("add", other)

    def __radd__(self, other) -> "DataFrame":
        return self._arithmetic("radd", other)

    def __mul__(self, other) -> "DataFrame":
        return self._arithmetic("mul", other)

    def __rmul__(self, other) -> "DataFrame":
        return self._arithmetic("rmul", other)

    def __sub__(self, other) -> "DataFrame":
        return self._arithmetic("sub", other)

    def __rsub__(self, other) -> "DataFrame":
        return self._arithmetic("rsub", other)

    def __truediv__(self, other) -> "DataFrame":
        return self._arithmetic("truediv", other)

    def __rtruediv__(self, other) -> "DataFrame":
        return self._arithmetic("rtruediv", other)

    def __floordiv__(self, other) -> "DataFrame":
        return self._arithmetic("floordiv", other)

    def __rfloordiv__(self, other) -> "DataFrame":
        return self._arithmetic("rfloordiv", other)

    def __pow__(self, other) -> "DataFrame":
        return self._arithmetic("pow", other)

    def __rpow__(self, other) -> "DataFrame":
        return self._arithmetic("rpow", other)
