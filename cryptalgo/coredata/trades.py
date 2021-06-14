from enum import Enum

from cryptalgo.utils.decorators.simplifiers import initializer



class TradeSide(Enum):
    BUY = 1
    SELL = -1



class Trade:

    def __init__(self, symbol: str, amount: float, price: float, side: TradeSide, fee: float) -> None:
        if symbol is None or amount is None or price is None or side is None or fee is None:
            raise ValueError("must pass all parameters")
        self.symbol = symbol
        self.amount = amount
        self.price = price
        self.side = side
        self.fee = fee



class TradeHistory:

    def __init__(self) -> None:
        self.trades = []


    def add_trade(self, trade: Trade):
        if trade is None:
            raise ValueError('Trade must be passed')
        self.trades.append(trade)
