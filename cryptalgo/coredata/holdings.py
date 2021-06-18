import abc
import datetime
import decimal
from decimal import Decimal
from typing import Dict, List

import pandas as pd

from cryptalgo.coredata.trades import TradeSide, TradeHistory, Trade
from cryptalgo.utils.decorators.validation import requires_amount, requires_symbol_and_amount, \
    requires_symbol_amount_and_price



class FeeModel(metaclass=abc.ABCMeta):

    def calculate_fee(self, symbol: str, amount: float, price: float, side: TradeSide) -> Decimal:
        pass



class Ledger:
    class History:

        def __init__(self, symbol: str, amount: Decimal, dir: str, bal: Decimal) -> None:
            self.date = datetime.datetime.utcnow()
            self.amount = amount
            self.direction = dir
            self.remaining_balance = bal
            self.symbol = symbol

    def __init__(self, name: str) -> None:
        self.name = name
        self.holdings: Dict = {}
        self.history: List[Ledger.History] = []


    def balance_history_as_series(self) -> pd.Series:
        return pd.Series(index=[x.date for x in self.history], data=[x.remaining_balance for x in self.history])


    @requires_symbol_and_amount
    def add(self, symbol: str, amount: float) -> None:
        if symbol not in self.holdings:
            self.holdings[symbol] = Decimal()
        with decimal.localcontext() as ctx:
            ctx.prec = 5
            self.holdings[symbol] += Decimal(amount)
            self.history.append(Ledger.History(symbol, Decimal(amount), "add", self.holdings[symbol]))


    @requires_symbol_and_amount
    def remove(self, symbol: str, amount: float) -> None:
        if symbol not in self.holdings:
            raise ValueError("can't remove {0} with no holdings".format(symbol))
        if amount > self.holdings[symbol]:
            raise ValueError(
                "can't remove {0} from {1} as holdings are {2}".format(amount, symbol, self.holdings[symbol]))
        with decimal.localcontext() as ctx:
            ctx.prec = 5
            self.holdings[symbol] -= Decimal(amount)
            self.history.append(Ledger.History(symbol, Decimal(amount), "remove", self.holdings[symbol]))



class Account:

    def __init__(self, start_cash_balance: float = 0.0, default_currency: str = 'USD',
                 default_trade_fee_model: FeeModel = None) -> None:
        self.cash_ledger: Ledger = Ledger(name='cash')
        self.default_currency: str = default_currency
        self.cash_ledger.add(self.default_currency, start_cash_balance)
        self.securities_ledger: Ledger = Ledger(name='securities')
        self.default_trade_fee_model: FeeModel = default_trade_fee_model
        self.trade_history: TradeHistory = TradeHistory()
        self.initial_cash_balance: Decimal = Decimal(start_cash_balance)


    def get_cash_balance(self, currency: str = None) -> Decimal:
        if currency is None:
            currency = self.default_currency
        return self.cash_ledger.holdings[currency]


    def get_account_value(self, security_prices: Dict, currency: str = None) -> Decimal:
        value = self.get_cash_balance()
        for k, v in self.securities_ledger.holdings.items():
            value += v * Decimal(security_prices[k])
        return value


    def get_num_shares_for(self, symbol: str) -> Decimal:
        if symbol in self.securities_ledger.holdings:
            return self.securities_ledger.holdings[symbol]
        else:
            return Decimal()


    def num_trades(self) -> int:
        return len(self.trade_history.trades)


    @requires_amount
    def deposit_cash(self, amount: float, currency: str = None):
        if currency is None:
            currency = self.default_currency
        self.cash_ledger.add(currency, amount, )


    @requires_amount
    def withdraw_cash(self, amount: float, currency: str = None):
        if currency is None:
            currency = self.default_currency
        self.cash_ledger.remove(currency, amount, )


    @requires_symbol_and_amount
    def add_shares(self, symbol: str, amount: float):
        self.securities_ledger.add(symbol, amount)


    @requires_symbol_and_amount
    def remove_shares(self, symbol: str, amount: float):
        self.securities_ledger.remove(symbol, amount)


    @requires_symbol_amount_and_price
    def buy_shares(self, symbol: str, amount: float, price: float, fee: float = None, currency: str = None):
        if currency is None:
            currency = self.default_currency
        with decimal.localcontext() as ctx:
            ctx.prec = 5
            trade_fee = Decimal()
            if fee is not None:
                trade_fee = Decimal(fee)
            elif self.default_trade_fee_model is not None:
                trade_fee = self.default_trade_fee_model.calculate_fee(symbol, amount, price, TradeSide.BUY)
            self.cash_ledger.remove(currency, (Decimal(amount) * Decimal(price)) + trade_fee)
            self.securities_ledger.add(symbol, amount)
            self.trade_history.add_trade(Trade(symbol, amount, price, TradeSide.BUY, trade_fee))


    @requires_symbol_amount_and_price
    def sell_shares(self, symbol: str, amount: float, price: float, fee: float = None, currency: str = None):
        if currency is None:
            currency = self.default_currency
        with decimal.localcontext() as ctx:
            ctx.prec = 5
            trade_fee = Decimal()
            if fee is not None:
                trade_fee = Decimal(fee)
            elif self.default_trade_fee_model is not None:
                trade_fee = self.default_trade_fee_model.calculate_fee(symbol, amount, price, TradeSide.SELL)
            self.securities_ledger.remove(symbol, amount)
            self.cash_ledger.add(currency, (Decimal(amount) * Decimal(price)) - trade_fee)
            self.trade_history.add_trade(Trade(symbol, amount, price, TradeSide.SELL, trade_fee))
