import abc
import collections
from datetime import datetime
from typing import Deque

import logging

import jsonpickle

logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)


class Tick:
    """
    A single trading signal or event
    """


    def __init__(self, time: datetime, symbol: str, price: float, size: float, side: str = "UNK",
                 best_bid: float = -1.0, best_ask: float = -1.0) -> None:
        self.time: datetime = time
        self.symbol: str = symbol
        self.price: float = float(price)
        self.size: float = float(size)
        self.side: str = side
        self.best_bid: float = float(best_bid)
        self.best_ask: float = float(best_ask)


    def __str__(self) -> str:
        return "{0}: {1} {2} ({3} units)".format(self.time, self.symbol, self.price, self.size)


    def to_json(self) -> str:
        return jsonpickle.encode(self, unpicklable=False)


    def to_csv_row(self) -> str:
        return '"{0}","{1}",{2},{3},"{4}",{5},{6}\n'.format(
            self.time.isoformat(),
            self.symbol,
            self.price,
            self.size,
            self.side,
            self.best_bid,
            self.best_ask,
        )


    @classmethod
    def to_csv_header(cls) -> str:
        return '"time","symbol","price","size","side","best_bid","best_ask"\n'


    @classmethod
    def from_csv_row(cls, row):
        return Tick(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
        )



class Feed(metaclass=abc.ABCMeta):

    def __init__(self, max_buffer: int = 1000) -> None:
        self.tick_buffer = collections.deque(iterable=[], maxlen=max_buffer)
        self.listeners = []
        super().__init__()


    @abc.abstractmethod
    def start(self):
        raise NotImplementedError


    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError


    def on_tick(self, msg: Tick):
        if isinstance(msg, Tick):
            logger.debug("tick received: {0}".format(msg))
            if self.accept_tick(msg):
                self.before_tick(msg)
                self.tick_buffer.appendleft(msg)
                for listener in self.listeners:
                    listener.on_tick(msg)
                self.after_tick(msg)
        else:
            logger.warning("invalid message type in on_tick: {0}".format(type(msg)))


    def accept_tick(self, tick: Tick) -> bool:
        return True


    def before_tick(self, tick: Tick):
        pass


    def after_tick(self, tick: Tick):
        pass


    def get_ticks(self) -> Deque:
        return self.tick_buffer


    def subscribe(self, listener):
        if hasattr(listener, "on_tick") and callable(listener.on_tick):
            self.listeners.append(listener)
        else:
            raise TypeError



class FileFeed(Feed):

    def __init__(self, fpath: str, max_buffer: int = 1000) -> None:
        super().__init__(max_buffer)


    def start(self):
        pass


    def stop(self):
        pass
