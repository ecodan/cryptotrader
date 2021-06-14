import abc
from collections import deque
from typing import Iterable, List

from cryptalgo.inputs.feed_agg import OHLC



class FeedStatistic(metaclass=abc.ABCMeta):
    def __init__(self, name: str):
        self.history = deque([], 1000)
        self.name = name


    def calculate(self, data: Iterable) -> None:
        raise NotImplementedError


    def get_latest(self) -> float:
        raise NotImplementedError


    def get_history(self) -> Iterable:
        raise NotImplementedError



class EMAStatistic(FeedStatistic):

    def __init__(self, num_periods: int):
        self.num_periods = num_periods
        super().__init__("EMA{0}".format(num_periods))


    def calculate(self, data: List) -> float:
        if len(data) == 1:
            entry = {"time": data[0].time, "value": data[0].close}
            self.history.appendleft(entry)
        else:
            # EMA Today = Price Today * (Smoothing / (1 + Days)) + EMA Yesterday * ( 1 – (Smoothing / (1 + Days))
            smoothing: float = 2.0
            periods = self.num_periods if len(data) >= self.num_periods else len(data)
            ema = data[0].close * (smoothing / (1.0 + periods)) + self.history[0]['value'] * (
                        1.0 - (smoothing / (1.0 + periods)))
            self.history.appendleft({"time": data[0].time, "value": ema})
            return ema


    def get_latest(self) -> float:
        if len(self.history > 0):
            return self.history[0]['value']
        else:
            return 0.0


    def get_history(self) -> Iterable:
        return self.history



class FeedAnalyzer:

    def __init__(self, history_len: int, min_history: int = 30):
        self.history_len = history_len
        self.histories = {}
        self.min_histories = min_history
        self.statistics = [
            EMAStatistic(12),
            EMAStatistic(26),
        ]
        self.signals = []
        self.signal_listeners = []


    def on_hloc(self, hloc) -> None:
        if hloc.symbol not in self.histories:
            self.histories[hloc.symbol] = deque([], maxlen=self.history_len)
        self.histories[hloc.symbol].appendleft(hloc)
        self.process(hloc)


    def process(self, hloc: OHLC) -> None:
        assert (hloc.symbol in self.histories)
        history = self.histories[hloc.symbol]
        # decide if any processing should happen
        if self.min_histories >= len(history):

            # calculate stats
            for statistic in self.statistics:
                statistic.calculate(history)

            # hunt for signals
            for signal in self.signals:
                if (signal.detect()):
                    # send signals
                    for listener in self.signal_listers:
                        listener.signal(signal)
