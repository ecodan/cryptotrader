import json
from datetime import datetime
from pathlib import Path

import cbpro
from cryptalgo.inputs.feed import Tick, Feed
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)



class CbproWebsocketClient(cbpro.WebsocketClient):

    def __init__(self,
                 products: [],
                 url: str = "wss://ws-feed.pro.coinbase.com",
                 message_type: str = "subscribe",
                 channels: [] = ["ticker"]) -> None:
        self.listeners = []
        super().__init__(url, products, message_type, None, False, False, "", "", "", channels)


    def on_open(self) -> None:
        logger.info("CbproWebsocketClient is open")


    def on_message(self, msg):
        if 'type' in msg:
            if msg['type'] == 'ticker':
                tick = Tick(
                    time=datetime.strptime(msg['time'], '%Y-%m-%dT%H:%M:%S.%f%z'),
                    symbol=msg['product_id'],
                    price=msg['price'],
                    size=msg['last_size'],
                    side=msg['side'],
                    best_ask=msg['best_ask'],
                    best_bid=msg['best_bid']
                )
                logger.debug("tick: {0}".format(tick))
                for listener in self.listeners:
                    listener.on_tick(tick)


    def on_close(self):
        logger.info("CbproWebsocketClient is closed")


    def subscribe(self, listener):
        if hasattr(listener, "on_tick") and callable(listener.on_tick):
            self.listeners.append(listener)
            logger.info('added new listener')
        else:
            raise TypeError



class CoinbaseFeed(Feed):

    def __init__(self, products: [], max_buffer: int = 1000, file_cache_path: str = None):
        super().__init__(max_buffer)
        self.source = CbproWebsocketClient(products)
        self.source.subscribe(self)
        if file_cache_path is not None:
            self.fcache: Path = Path(file_cache_path)
            if not self.fcache.is_dir():
                logger.warning("{0} must be a writeable directory".format(file_cache_path))
                raise IsADirectoryError
            self.fcache_files = {}
        else:
            self.fcache: Path = None


    def start(self):
        self.source.start()


    def stop(self):
        self.source.stop()


    def after_tick(self, tick: Tick):
        super().after_tick(tick)
        if self.fcache is not None:
            if tick.symbol not in self.fcache_files:
                self.fcache_files[tick.symbol] = Path(self.fcache, "{0}-{1}.csv".format(tick.symbol, datetime.now()))
                with open(self.fcache_files[tick.symbol], "w") as f:
                    f.write(tick.to_csv_header())
            with open(self.fcache_files[tick.symbol], "a") as f:
                f.write(tick.to_csv_row())

