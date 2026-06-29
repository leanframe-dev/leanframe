import re

files = [
    'leanframe/core/mixins/arithmetic.py',
    'leanframe/core/mixins/comparisons.py'
]

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()

    # We need to extract the underlying column from `other` if it's a DataFrame, but ensure it's evaluated on `self._data`
    # We can extract the underlying value via op().values if it's a project
    replacement = """
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
"""

    search_str = """
            # If other is an Expression or Ibis scalar/column
            other_val = getattr(other, "_data", other)
            if hasattr(other, "_data") and hasattr(other_val, "columns") and len(other_val.columns) == 1:
                other_val = other_val[other_val.columns[0]]
"""
    content = content.replace(search_str, replacement)

    with open(filepath, 'w') as f:
        f.write(content)
print("done")
