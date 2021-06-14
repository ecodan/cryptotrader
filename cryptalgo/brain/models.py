import abc
import time
from datetime import datetime
from enum import Enum
import matplotlib.pyplot as plt
import mplfinance as mpf

import pandas as pd
import numpy as np

import logging

from cryptalgo.inputs.feed_agg import OHLC

logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)



class Signal(Enum):
    SELL = -1
    BUY = 1



class SignalEvent:

    def __init__(self, time: datetime, symbol: str, signal: Signal, price: float) -> None:
        self.time = time
        self.symbol = symbol
        self.signal = signal
        self.price = price



class AlgoFishHLOCModel(metaclass=abc.ABCMeta):

    def __init__(self, symbol: str, ) -> None:
        self.hloc_data: pd.DataFrame = pd.DataFrame(columns=OHLC.get_fields()).drop(columns=['time'])
        self.listeners: [] = []
        self.symbol = symbol


    def subscribe(self, listener):
        if hasattr(listener, "on_signal") and callable(listener.on_signal):
            self.listeners.append(listener)
        else:
            raise TypeError()


    def load_data(self, data):
        if type(data.index) is not pd.DatetimeIndex:
            raise ValueError("dataframe must have datetime index")
        self.hloc_data = data


    @abc.abstractmethod
    def on_hloc(self, hloc):
        raise NotImplementedError


    @abc.abstractmethod
    def get_historical_signal_events(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_signal_df(self, data_limit: int = -1, data_limit_on_tail: bool = True) -> pd.DataFrame:
        raise NotImplementedError()


    @abc.abstractmethod
    def visualize(self, signal_df: pd.DataFrame = None):
        raise NotImplementedError()


class SMACModel(AlgoFishHLOCModel):

    def __init__(self, symbol: str, short_lb: int = 50, long_lb: int = 120, max_hlocs: int = 2000) -> None:
        super().__init__(symbol)
        self.short_lb = short_lb
        self.long_lb = long_lb
        self.max_hlocs = max_hlocs


    def get_signal_df(self, data_limit: int = -1, data_limit_on_tail: bool = True) -> pd.DataFrame:
        data_df = self.hloc_data

        if data_limit > 0:
            if data_limit_on_tail:
                data_df = data_df.iloc[-data_limit::]
            else:
                data_df = data_df.iloc[0:data_limit]

        signal_df = pd.DataFrame(index=data_df.index)
        signal_df['signal'] = 0.0

        # create a short simple moving average over the short lookback period
        signal_df['short_mav'] = data_df['close'].rolling(window=self.short_lb, min_periods=1, center=False).mean()

        # create long simple moving average over the long lookback period
        signal_df['long_mav'] = data_df['close'].rolling(window=self.long_lb, min_periods=1, center=False).mean()

        # calculate signals
        signal_df['signal'][self.short_lb:] = np.where(
            signal_df['short_mav'][self.short_lb:] > signal_df['long_mav'][self.short_lb:], 1.0, 0.0)
        signal_df['positions'] = signal_df['signal'].diff()
        signal_df['price'] = signal_df.apply(
            lambda x: data_df.loc[x.name]['close'] if x['positions'] != 0 else np.NaN, axis=1)
        return signal_df


    def get_historical_signal_events(self) -> pd.DataFrame:
        signal_df = self.get_signal_df()
        buysells_df = signal_df[signal_df['positions'].isin([-1, 1])].drop(columns=["signal", "short_mav", "long_mav"])
        return buysells_df


    # @timeme
    def on_hloc(self, hloc):
        if hloc.symbol != self.symbol:
            logger.warning("on_hloc rec'd mismatched symbol. Accepts {0}, got {1}".format(self.symbol, hloc.symbol))
            return

        # append to data
        # logger.debug("on hloc {0}".format(hloc))
        self.hloc_data = self.hloc_data.append(hloc.to_pandas_series(dt_index=True))

        if len(self.hloc_data) >= self.long_lb:
            signal_df = self.get_signal_df()

            # fire events
            if signal_df['positions'].iloc[-1] == -1:
                logger.info('generated SELL signal for {0}'.format(hloc))
                for l in self.listeners:
                    l.on_signal(Signal.SELL)
            elif signal_df['positions'].iloc[-1] == 1:
                logger.info('generated BUY signal for {0}'.format(hloc))
                for l in self.listeners:
                    l.on_signal(Signal.BUY)

        # replace data if too long
        if len(self.hloc_data) > self.max_hlocs:
            self.hloc_data = self.hloc_data.iloc[-self.max_hlocs::].copy()

        # if len(signal_df) % 250 == 0:
        #     signal_df.to_csv("./data/signal_model.csv")


class MACDModel(AlgoFishHLOCModel):

    def __init__(self, symbol: str, low_ewm: int, high_ewm: int) -> None:
        super().__init__(symbol)
        self.low_ewm = low_ewm
        self.high_ewm = high_ewm
        self.signal_df = None


    def on_hloc(self, hloc):
        raise NotImplementedError('TBD')


    def get_historical_signal_events(self) -> pd.DataFrame:
        logger.debug("get_historical_signal_events starting...")
        signal_df = self.get_signal_df()
        buysells_df = signal_df[signal_df['positions'].isin([-1, 1])].drop(columns=["signal", "short_ewm", "long_ewm"])
        return buysells_df


    def get_signal_df(self, data_limit: int = -1, data_limit_on_tail: bool = True) -> pd.DataFrame:
        logger.debug("get_signal_df starting...")

        if self.signal_df is None:
            data_df = self.hloc_data

            if data_limit > 0:
                if data_limit_on_tail:
                    data_df = data_df.iloc[-data_limit::]
                else:
                    data_df = data_df.iloc[0:data_limit]

            signal_df = pd.DataFrame(index=data_df.index)
            signal_df['signal'] = 0.0

            signal_df['short_ewm'] = data_df['close'].ewm(span=self.low_ewm, adjust=False).mean()
            signal_df['long_ewm'] = data_df['close'].ewm(span=self.high_ewm, adjust=False).mean()

            # calculate signals
            signal_df['signal'][self.low_ewm:] = np.where(
                signal_df['short_ewm'][self.low_ewm:] > signal_df['long_ewm'][self.low_ewm:], 1.0, 0.0)
            signal_df['positions'] = signal_df['signal'].diff()
            signal_df['price'] = data_df['close']
            self.signal_df = signal_df
        return self.signal_df

    def visualize(self, signal_df: pd.DataFrame = None):
        logger.debug("visualizing...")
        if signal_df is None:
            signal_df = self.get_signal_df().copy()
        signal_df['close'] = self.hloc_data['close']
        apds = [
            mpf.make_addplot(signal_df['short_ewm'], type='line', color='g'),
            mpf.make_addplot(signal_df['long_ewm'], type='line', color='b'),
            mpf.make_addplot(signal_df.apply(lambda x: x['close'] if x['positions'] == Signal.SELL.value else np.NaN, axis=1), type='scatter', markersize=200, marker='v'),
            mpf.make_addplot(signal_df.apply(lambda x: x['close'] if x['positions'] == Signal.BUY.value else np.NaN, axis=1), type='scatter', markersize=200, marker='^'),
        ]
        mpf.plot(self.hloc_data, volume=True, addplot=apds, type='line')
