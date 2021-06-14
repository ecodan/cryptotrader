import csv
from pathlib import Path

from cryptalgo.inputs.feed_agg import OHLC

max_records = 2000
data_path = Path('./data/candles/BTC-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv')
# with open(data_path, "r") as f:
#     csvreader = csv.reader(f, delimiter=',', quotechar='"')
#     header = next(csvreader)
#     num_rows: int = 0
#     for row in csvreader:
#         # start = datetime.now()
#         num_rows += 1
#         if max_records > 0 and num_rows > max_records:
#             break
#         hloc = HLOC.from_csv(row, timestamp_as_str=True)
#         print(hloc)

with open(data_path, "r") as f:
    line = "start"
    while(line):
        line = f.readline()
        print(line)
