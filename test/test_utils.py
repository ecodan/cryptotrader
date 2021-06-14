import csv
from pathlib import Path
import pandas as pd

from cryptalgo.inputs.feed_agg import OHLC



def generate_hloc_dataframe():
    df = pd.read_csv(Path("./test/data/test_candles_1000.csv"), sep=",", quotechar='"', parse_dates=['time'])
    df.set_index('time', inplace=True)
    df.sort_index(ascending=True, inplace=True)
    return df
