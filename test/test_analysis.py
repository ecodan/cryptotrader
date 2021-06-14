import csv
from collections import deque
from unittest import TestCase

from cryptalgo.brain.analysis import EMAStatistic
from cryptalgo.inputs.feed_agg import OHLC



class TestEMAStatistic(TestCase):

    def test_name(self):
        stat = EMAStatistic(10)
        self.assertEqual("EMA10", stat.name)

    def test_calculate(self):
        stat = EMAStatistic(10)
        history = deque([], 100)
        with open("../data/ETH-TEST-100.csv", "r") as file:
            csv_reader = csv.DictReader(file, dialect="excel")
            last_close = 0
            last_ema = 0
            for row in csv_reader:
                row['duration_sec'] = 300
                row['symbol'] = "ETH"
                hloc = OHLC.from_dict(row)
                history.appendleft(hloc)
                ema = stat.calculate(history)
                print("last: {0} | ema: {1}".format(hloc.close, ema))
                if last_close and last_ema:
                    if last_close < hloc.close:
                        self.assertGreater(ema, last_ema)
                    elif last_close > hloc.close:
                        self.assertLess(ema, last_ema)
                last_close = hloc.close
                last_ema = ema


    def test_get_latest(self):
        self.fail()


    def test_get_history(self):
        self.fail()
