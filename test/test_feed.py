from unittest import TestCase

import cryptalgo.inputs
import time

from cryptalgo.inputs.feed_agg import OHLC



class HLOCSink:
    def __init__(self):
        self.event_ct=0

    def on_hloc(self, evt: OHLC):
        if type(evt) == OHLC:
            self.event_ct += 1


class TestFileHLOC(TestCase):

    def test_start(self):
        hloc = FileHLOC("../data/ETH-TEST-100.csv", "ETH", 0)
        sink = HLOCSink()
        hloc.subscribe(sink)
        hloc.start()
        while hloc.event_ct < 100:
            time.sleep(1)
        hloc.stop()
        self.assertEqual(100, sink.event_ct)


    def test_stop(self):
        hloc = FileHLOC("../data/ETH-TEST-100.csv", "ETH", .1)
        sink = HLOCSink()
        hloc.subscribe(sink)
        hloc.start()
        while hloc.event_ct < 5:
            time.sleep(1)
        hloc.stop()
        self.assertLess(sink.event_ct, 100)



    def test_subscribe(self):
        hloc = FileHLOC("../data/ETH-TEST-100.csv", .1)
        self.assertEqual(0, len(hloc.listeners))
        sink = HLOCSink()
        hloc.subscribe(sink)
        self.assertEqual(1, len(hloc.listeners))