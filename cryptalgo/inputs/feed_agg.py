import abc
import collections
import csv
import time
from threading import Thread
from enum import Enum
from datetime import datetime, timedelta, timezone
import threading as th
from typing import List, Union, Dict
import pandas as pd

import cbpro
import jsonpickle

from cryptalgo.inputs.feed import Feed

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)


class AggPeriod(Enum):
    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15
    ONE_HOUR = 60
    ONE_DAY = 1440



class OHLC:
    """
    Represents the high, low, open and close for a given period.
    """

    fields: List[str] = ['symbol', 'time', 'high', 'low', 'open', 'close', 'volume', 'duration_secs']
    csv_header: str = None


    def __init__(self, symbol: str, time: datetime, high: float, low: float, open: float, close: float, volume: float,
                 duration_sec: float) -> None:
        self.symbol = symbol
        self.time = time
        self.high = high
        self.low = low
        self.open = open
        self.close = close
        self.volume = volume
        self.duration_sec = duration_sec


    def __str__(self) -> str:
        return jsonpickle.encode(self, unpicklable=False)


    def to_dict(self) -> Dict:
        l = self.to_list()
        return {OHLC.fields[i] : l[i] for i in range(len(OHLC.fields))}


    def to_list(self) -> List[Union[str, float]]:
        return [
            self.symbol,
            self.time.isoformat(),
            self.high,
            self.low,
            self.open,
            self.close,
            self.volume,
            self.duration_sec,
        ]


    def to_csv_row(self) -> str:
        return '"{0}","{1}",{2},{3},{4},{5},{6},{7}\n'.format(
            self.symbol,
            self.time.isoformat(),
            self.high,
            self.low,
            self.open,
            self.close,
            self.volume,
            self.duration_sec,
        )


    def to_pandas_series(self, dt_index=True):
        d = self.to_dict()
        if dt_index:
            d.pop('time')
            return pd.Series(name=self.time, data=d, )
        else:
            return pd.Series(data=d, )


    @classmethod
    def get_fields(cls) -> [str]:
        return OHLC.fields


    @classmethod
    def get_csv_header(cls) -> str:
        if OHLC.csv_header is None:
            OHLC.csv_header = ",".join(['"{0}"'.format(x) for x in OHLC.get_fields()])
        return OHLC.csv_header


    @classmethod
    def from_dict(cls, data: {}):
        time = None
        if type(data['time']) == str:
            time = datetime.fromisoformat(data["time"])
        elif type(data['time']) == datetime:
            time = data["time"]
        elif type(data['time']) == pd.Timestamp:
            time = data["time"].to_pydatetime()
        return OHLC(
            data["symbol"],
            time,
            float(data["high"]),
            float(data["low"]),
            float(data["open"]),
            float(data["close"]),
            float(data["volume"]),
            int(data["duration_secs"]),
        )


    @classmethod
    def from_csv(cls, row: [], timestamp_as_str: bool = False):
        return OHLC(
            row[0],
            datetime.fromisoformat(row[1]) if timestamp_as_str else datetime.fromtimestamp(row[1], tz=timezone.utc),
            float(row[2]),
            float(row[3]),
            float(row[4]),
            float(row[5]),
            float(row[6]),
            int(row[7]),
        )



class OHLCSource(metaclass=abc.ABCMeta):

    def __init__(self, symbol: str, max_queue_len: int = 1000) -> None:
        self.symbol = symbol
        self.hlocs = collections.deque(maxlen=max_queue_len)
        self.listeners = []
        super().__init__()


    @abc.abstractmethod
    def start(self):
        raise NotImplementedError


    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError


    def subscribe(self, listener):
        if hasattr(listener, "on_hloc") and callable(listener.on_hloc):
            self.listeners.append(listener)
        else:
            raise TypeError



class FileOHLC(OHLCSource):

    def __init__(self, fpath: str, symbol: str, msg_delay_sec: float = 0.0) -> None:
        super().__init__(symbol)
        self.fpath = fpath
        self.msg_delay_sec = msg_delay_sec
        self.end = True
        self.thread = None
        self.event_ct = 0


    def start(self):
        def _go():
            with open(self.fpath, "r") as file:
                csv_reader = csv.DictReader(file, dialect="excel")
                for row in csv_reader:
                    row['duration_sec'] = 300
                    row['symbol'] = self.symbol
                    hloc = OHLC.from_dict(row)
                    for listener in self.listeners:
                        listener.on_hloc(hloc)
                    self.event_ct += 1
                    time.sleep(self.msg_delay_sec)
                    if self.end:
                        break


        self.end = False
        self.thread = Thread(target=_go)
        self.thread.start()


    def stop(self):
        self.end = True
        self.thread.join()


    def subscribe(self, listener):
        return super().subscribe(listener)



class TickerOHLCSource(OHLCSource):

    def __init__(self, symbol: str, ticker_feed: Feed, max_queue_len: int = 1000) -> None:
        super().__init__(symbol, max_queue_len)
        if ticker_feed:
            ticker_feed.subscribe(self)
        self.listeners = []


    @abc.abstractmethod
    def on_tick(self, tick):
        raise NotImplementedError



class PeriodicOHLCSource(OHLCSource):

    def __init__(self, symbol: str, agg_period: AggPeriod, num_periods: int = 100) -> None:
        super().__init__(symbol, num_periods)
        self.agg_period: AggPeriod = agg_period
        self.timer: th.Timer = None
        self.period_start: datetime = None
        self.period_end: datetime = None


    def start(self):
        """
        Sets a timer to call on_period_end within 1s of the time in period_end (calculated using the agg_period)
        :return: None
        """
        logger.debug("starting timer")
        t = datetime.utcnow()
        period_mins = self.agg_period.value
        self.period_start = t - timedelta(minutes=t.minute % period_mins, seconds=t.second, microseconds=t.microsecond)
        self.period_end = t + timedelta(minutes=period_mins) - timedelta(minutes=t.minute % period_mins,
                                                                         seconds=t.second, microseconds=t.microsecond)
        logger.debug("period start: {0} | end={1}".format(self.period_start, self.period_end))
        self.timer = th.Timer((self.period_end - datetime.utcnow()).seconds + 1, self.on_period_end)
        self.timer.start()


    def stop(self):
        logger.debug("stopping timer")
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
            self.period_start = None
            self.period_end = None


    def on_period_end(self):
        logger.debug("starting...")
        hloc = self.generate_hloc()
        logger.debug("hloc={0}".format(hloc))
        for l in self.listeners:
            l.on_hloc(hloc)
        self.period_start = self.period_end
        self.period_end = self.period_start + timedelta(minutes=self.agg_period.value)
        self.timer = th.Timer((self.period_end - datetime.utcnow()).seconds + 1, self.on_period_end)
        logger.debug("setting new timer period_end={0}".format(self.period_end))
        self.timer.start()


    @abc.abstractmethod
    def generate_hloc(self):
        raise NotImplementedError



class CBProPeriodicHLOCSource(PeriodicOHLCSource):

    def __init__(self, symbol: str, agg_period: AggPeriod, num_periods: int = 100) -> None:
        super().__init__(symbol, agg_period, num_periods)
        self.cbpro_client = cbpro.PublicClient()


    def generate_hloc(self):
        res = self.cbpro_client.get_product_historic_rates(
            self.symbol,
            self.period_start,
            self.period_start,  # for a single period, start = end
            self.agg_period.value * 60,  # s
        )
        frame_start = datetime.fromtimestamp(res[0][0], tz=timezone.utc)

        if (frame_start - self.period_start).seconds != 0:
            logger.warning("Coinbase return data start time {0} different from requested {1}".format(frame_start,
                                                                                                      self.period_start))
        row = res[0]
        rowx = [self.symbol, row[0], row[2], row[1], row[3], row[4], row[5], self.agg_period.value * 60]
        return OHLC.from_csv(rowx)
