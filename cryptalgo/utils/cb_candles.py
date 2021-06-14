import logging
from datetime import datetime, timedelta
from pathlib import Path
import time
import cbpro

from cryptalgo.inputs.feed_agg import OHLC

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s: [%(filename)s:%(funcName)s:%(lineno)d] %(message)s'
)

if __name__ == '__main__':
    public_client = cbpro.PublicClient()
    period: int = 300  # s
    start: datetime = datetime(2021, 1, 1, 0, 0, 0)
    end: datetime = datetime(2021, 6, 1, 0, 0, 0)
    periods = (end - start) / period

    data_dir = Path("./data/candles/")
    assert data_dir.is_dir()

    # for product in ['BTC-USD', 'ETH-USD', 'LTC-USD', 'MATIC-USD', 'LINK-USD', 'DASH-USD', 'BCH-USD']:
    for product in ['ATOM-USD', 'ALGO-USD', 'ZRX-USD', ]:
        next_start = start
        out_file = Path(data_dir, "{0}-{1}-{2}-{3}-candles.csv".format(product, start, end, period))
        with open(out_file, "w") as f:
            f.write(",".join(['"{0}"'.format(x) for x in OHLC.get_fields()]))
            f.write("\n")
            while (next_start < end):
                last_end = next_start + timedelta(seconds=(300 * period))
                print("{0}-{1}-{2}-{3}".format(product, next_start, last_end, period))
                res = public_client.get_product_historic_rates(product, next_start, last_end, period)
                num_records = len(res) - 1
                for i in range(num_records, 0, -1):
                    row = res[i]
                    rowx = [product, row[0], row[2], row[1], row[3], row[4], row[5], period]
                    hloc = OHLC.from_csv(rowx)
                    f.write(hloc.to_csv_row())
                next_start = last_end
                time.sleep(0.25)
