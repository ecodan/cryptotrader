import time
from datetime import datetime
from unittest import TestCase

from cryptalgo.inputs.feed_agg import FileOHLC, AggPeriod, PeriodicOHLCSource, OHLC, CBProPeriodicHLOCSource



class PeriodicHLOCSourceStub(PeriodicOHLCSource):

    def generate_hloc(self):
        return OHLC("TEST", datetime.now(), 100.0, 50.0, 90.0, 60.0, 1000.0, -1.0)


class TestPeriodicHLOCSource(TestCase):

    def test_start_stop(self):
        s = PeriodicHLOCSourceStub("TEST", agg_period=AggPeriod.ONE_MINUTE)
        s.start()
        self.assertEqual(s.period_end.second, 0)
        self.assertEqual(s.period_end.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual((s.period_end - s.period_start).seconds, 60)
        self.assertIsNotNone(s.timer)
        s.stop()
        self.assertIsNone(s.timer)
        self.assertIsNone(s.period_end)
        self.assertIsNone(s.period_start)

        s = PeriodicHLOCSourceStub("TEST", agg_period=AggPeriod.FIVE_MINUTES)
        s.start()
        self.assertEqual(s.period_end.second, 0)
        self.assertEqual(s.period_end.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual((s.period_end - s.period_start).seconds, 300)
        self.assertIsNotNone(s.timer)
        s.stop()
        self.assertIsNone(s.timer)
        self.assertIsNone(s.period_end)
        self.assertIsNone(s.period_start)

        s = PeriodicHLOCSourceStub("TEST", agg_period=AggPeriod.FIFTEEN_MINUTES)
        s.start()
        self.assertEqual(s.period_end.second, 0)
        self.assertEqual(s.period_end.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual((s.period_end - s.period_start).seconds, 900)
        self.assertIsNotNone(s.timer)
        s.stop()
        self.assertIsNone(s.timer)
        self.assertIsNone(s.period_end)
        self.assertIsNone(s.period_start)

        s = PeriodicHLOCSourceStub("TEST", agg_period=AggPeriod.ONE_HOUR)
        s.start()
        self.assertEqual(s.period_end.second, 0)
        self.assertEqual(s.period_end.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual((s.period_end - s.period_start).seconds, 3600)
        self.assertIsNotNone(s.timer)
        s.stop()
        self.assertIsNone(s.timer)
        self.assertIsNone(s.period_end)
        self.assertIsNone(s.period_start)

        s = PeriodicHLOCSourceStub("TEST", agg_period=AggPeriod.ONE_DAY)
        s.start()
        self.assertEqual(s.period_end.second, 0)
        self.assertEqual(s.period_end.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual(s.period_start.microsecond, 0)
        self.assertEqual((s.period_end - s.period_start).days, 1)
        self.assertIsNotNone(s.timer)
        s.stop()
        self.assertIsNone(s.timer)
        self.assertIsNone(s.period_end)
        self.assertIsNone(s.period_start)



class HLOCListener:


    def __init__(self) -> None:
        self.hlocs = []


    def on_hloc(self, hloc):
        print(hloc)
        self.hlocs.append(hloc)


class TestCBProPeriodicHLOCSource(TestCase):

    def test_start_stop(self):
        s = CBProPeriodicHLOCSource("BTC-USD", agg_period=AggPeriod.ONE_MINUTE)
        l = HLOCListener()
        s.subscribe(l)
        s.start()
        start = datetime.now()
        while(len(l.hlocs) == 0):
            time.sleep(5)
            if (datetime.now() - start).seconds > 70:
                s.stop()
                self.fail()
        self.assertIsNotNone(l.hlocs[0])
        s.stop()