import numpy as np
import pandas as pd
import pandas.testing as pdt
import ibis

from leanframe.core.frame import DataFrame


def test_dataframe_rolling_aggregations():
    pdf = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [10.0, np.nan, 30.0, 40.0, 50.0],
        }
    )
    ldf = DataFrame(ibis.memtable(pdf))

    # Test sum with default min_periods (min_periods=window)
    p_sum = pdf.rolling(window=3).sum()
    l_sum = ldf.rolling(window=3).sum().to_pandas()
    pdt.assert_frame_equal(p_sum, l_sum, check_dtype=False)

    # Test sum with min_periods=1
    p_sum_min = pdf.rolling(window=3, min_periods=1).sum()
    l_sum_min = ldf.rolling(window=3, min_periods=1).sum().to_pandas()
    pdt.assert_frame_equal(p_sum_min, l_sum_min, check_dtype=False)

    # Test count
    p_count = pdf.rolling(window=2).count()
    # Pandas count returns float if there's nan, int if not. Ibis returns int. Let pandas handle the check_dtype=False
    l_count = ldf.rolling(window=2).count().to_pandas()
    pdt.assert_frame_equal(p_count, l_count, check_dtype=False)

    # Test mean
    p_mean = pdf.rolling(window=3, min_periods=2).mean()
    l_mean = ldf.rolling(window=3, min_periods=2).mean().to_pandas()
    pdt.assert_frame_equal(p_mean, l_mean, check_dtype=False)

    # Test std
    p_std = pdf.rolling(window=3, min_periods=2).std()
    l_std = ldf.rolling(window=3, min_periods=2).std().to_pandas()
    pdt.assert_frame_equal(p_std, l_std, check_dtype=False)
