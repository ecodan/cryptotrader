import unittest
from unittest import TestCase
import pandas as pd

from cryptalgo.brain.models import SMACModel
from cryptalgo.inputs.feed_agg import OHLC
from test.test_utils import generate_hloc_dataframe



class HLOCListener:

    def __init__(self) -> None:
        self.hlocs = []


    def on_signal(self, hloc):
        self.hlocs.append(hloc)



class TestSMACModel(TestCase):
    df = None


    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        TestSMACModel.df = generate_hloc_dataframe()


    def test_load_dataframe(self):
        df = TestSMACModel.df.copy()
        model = SMACModel("LTC-USD", short_lb=30, long_lb=90)
        model.load_data(df)
        self.assertEqual(len(df), len(model.hloc_data))

        with self.assertRaises(ValueError):
            model.load_data(df.reset_index())


    def test_get_signal_df(self):
        df = TestSMACModel.df.copy()
        model = SMACModel("LTC-USD", short_lb=30, long_lb=90)
        model.load_data(df)

        sdf = model.get_signal_df()
        sdf.to_csv("./data/test_signal_ref.csv")
        self.assertEqual(len(df), len(sdf))
        self.assertListEqual(
            ['signal', 'short_mav', 'long_mav', 'positions', 'price'],
            sdf.columns.values.tolist()
        )
        self.assertEqual(10, len(sdf[sdf['positions'] == 1]))
        self.assertEqual(10, len(sdf[sdf['positions'] == -1]))

        sdf = model.get_signal_df(data_limit=200, data_limit_on_tail=False)
        self.assertEqual(200, len(sdf))
        self.assertEqual(3, len(sdf[sdf['positions'] == 1]))


    def test_get_historical_signal_events(self):
        df = TestSMACModel.df.copy()
        model = SMACModel("LTC-USD", short_lb=30, long_lb=90)
        model.load_data(df)
        hse = model.get_historical_signal_events()
        self.assertEqual(20, len(hse))
        self.assertEqual(10, len(hse[hse['positions'] == 1]))
        self.assertEqual(10, len(hse[hse['positions'] == -1]))
        self.assertListEqual(
            ['positions', 'price'],
            hse.columns.values.tolist()
        )


    def test_on_hloc(self):
        df = TestSMACModel.df.copy()
        model = SMACModel("LTC-USD", short_lb=30, long_lb=90)
        hloc_sink = HLOCListener()
        model.subscribe(hloc_sink)
        for i in range(95):
            print("hloc {0}".format(i))
            row = df.iloc[i]
            rowd = row.to_dict()
            rowd['time'] = row.name
            hloc = OHLC.from_dict(rowd)
            model.on_hloc(hloc)
            self.assertEqual(i + 1, len(model.hloc_data))
            self.assertEqual(0, len(hloc_sink.hlocs))

        row = df.iloc[95]
        rowd = row.to_dict()
        rowd['time'] = row.name
        hloc = OHLC.from_dict(rowd)
        model.on_hloc(hloc)
        self.assertEqual(96, len(model.hloc_data))
        self.assertEqual(1, len(hloc_sink.hlocs))
