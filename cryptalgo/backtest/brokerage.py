import abc
from decimal import Decimal

from cryptalgo.coredata.holdings import FeeModel
from cryptalgo.coredata.trades import TradeSide



class CBPTradingFees(FeeModel):

    def calculate_fee(self, symbol: str, amount: float, price: float, side: TradeSide) -> Decimal:
        return Decimal((amount * price) * .005)
