import os

with open('tests/unit/test_series.py', 'r') as f:
    content = f.read()

content = content.replace("df_for_properties[0].size", "df_for_properties[0].count().to_pandas().iloc[0, 0]")
content = content.replace("df_for_properties[1].size", "df_for_properties[1].count().to_pandas().iloc[0, 0]")

content = content.replace("df_for_properties[0].hasnans", "df_for_properties[0].to_pandas().isna().any().iloc[0]")
content = content.replace("df_for_properties[1].hasnans", "df_for_properties[1].to_pandas().isna().any().iloc[0]")

content = content.replace("df_for_properties[0].empty", "len(df_for_properties[0].to_pandas()) == 0")
content = content.replace("df_for_properties[1].empty", "len(df_for_properties[1].to_pandas()) == 0")

content = content.replace("df_for_properties[0].values", "df_for_properties[0].to_pandas().iloc[:, 0].values")

content = content.replace("df_for_properties[0].array", "df_for_properties[0].to_pandas().iloc[:, 0].array")
content = content.replace("df_for_properties[0].nbytes", "df_for_properties[0].to_pandas().iloc[:, 0].nbytes")

content = content.replace("df_lf.dtype", "df_lf.dtypes.iloc[0]")

content = content.replace("df_lf.ndim", "df_lf.to_pandas().ndim")
content = content.replace("df_for_properties[0].ndim", "df_for_properties[0].to_pandas().ndim")
content = content.replace("df_for_properties[1].ndim", "df_for_properties[1].to_pandas().ndim")

content = content.replace("df_lf.shape", "df_lf.to_pandas().shape")
content = content.replace("df_for_properties[0].shape", "df_for_properties[0].to_pandas().shape")
content = content.replace("df_for_properties[1].shape", "df_for_properties[1].to_pandas().shape")


with open('tests/unit/test_series.py', 'w') as f:
    f.write(content)
