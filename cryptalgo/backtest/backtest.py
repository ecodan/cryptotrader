import decimal
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import csv
from typing import Tuple

from cryptalgo.brain.models import AlgoFishHLOCModel, Signal, SignalEvent
from cryptalgo.coredata.holdings import FeeModel, Account
from cryptalgo.inputs.feed_agg import OHLC, AggPeriod
import numpy as np
import pandas as pd
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)


class BacktestHarness:

    def __init__(self, alpha_model: AlgoFishHLOCModel, backtest_data: Path = None, seed_investment: float = 1000.0, brokerage_model: FeeModel = None, agg_period: AggPeriod = AggPeriod.FIVE_MINUTES) -> None:
        self.alpha_model = alpha_model
        self.alpha_model.subscribe(self)
        self.data_path = backtest_data
        if self.data_path is not None:
            assert self.data_path.is_file()

        self.account = Account(start_cash_balance=seed_investment, default_currency='USD', default_trade_fee_model=brokerage_model)
        self.seed_investment: Decimal = Decimal(seed_investment)

        self.last_buy_price = np.NaN

        self.start_price = Decimal()
        self.end_price = Decimal()

        self.agg_period = agg_period


    @classmethod
    def generate_report_header(cls) -> Tuple:
        return (
            'start', 'end', 'price_chg', 'num_trades', 'start_bal', 'end_bal', 'gain', 'growth'
        )


    def generate_report(self) -> Tuple:
        # start, end, price_chg, num_trades, start_bal, end_bal, gain, growth
        with decimal.localcontext() as ctx:
            ctx.prec = 10
            start_bal = self.account.initial_cash_balance
            end_bal = self.account.get_account_value({self.alpha_model.symbol: self.end_price})
            return (
                round(self.start_price, 2),
                round(self.end_price, 2),
                (self.end_price / self.start_price) - Decimal('1.0'),
                self.account.num_trades(),
                start_bal,
                end_bal,
                end_bal - start_bal,
                end_bal/start_bal - Decimal('1.0')
            )


    def report_as_string(self) -> str:
        headers = BacktestHarness.generate_report_header()
        data = self.generate_report()
        return "\n".join(["{0}: {1}".format(x[0], x[1]) for x in zip(headers, data)])



    def backtest_single_pass(self, data = None) -> pd.DataFrame:
        if data is None:
            # "symbol","time","high","low","open","close","volume","duration_secs"
            data = pd.read_csv(self.data_path, sep=",", quotechar='"', parse_dates=['time'])
            data.set_index('time', inplace=True)
            data.sort_index(ascending=True, inplace=True)

        if self.agg_period != AggPeriod.FIVE_MINUTES:
            if self.agg_period == AggPeriod.FIFTEEN_MINUTES:
                freq = '15T'
                duration_secs = 900
            elif self.agg_period == AggPeriod.ONE_HOUR:
                freq = '1H'
                duration_secs = 3600
            elif self.agg_period == AggPeriod.ONE_DAY:
                freq = '1D'
                duration_secs = 3600 * 24
            elif self.agg_period == AggPeriod.ONE_MINUTE:
                raise NotImplementedError("minimum backtest is 5 mins")

            data = data.resample(freq).agg({
                'symbol': 'first',
                'high': np.max,
                'low': np.min,
                'open': 'first',
                'close': 'last',
                'volume': np.sum,
                'duration_secs': 'first',
            })
            data['duration_secs'] = duration_secs

        self.alpha_model.load_data(data)
        evts: pd.DataFrame = self.alpha_model.get_historical_signal_events()

        with decimal.localcontext() as ctx:
            ctx.prec = 5
            logger.debug("processing {0} signal events".format(len(evts)))
            for idx, row in evts.iterrows():
                if row['positions'] == Signal.BUY.value:
                    price = Decimal(row['price'])
                    # TODO: make this model driven
                    shares = self.account.get_cash_balance() * Decimal(0.9) / price
                    self.account.buy_shares(symbol=self.alpha_model.symbol, amount=shares, price=price)
                    logger.debug("BUY {0} at {1} (total cash: {2}".format(
                        self.account.get_num_shares_for(self.alpha_model.symbol),
                        price,
                        self.account.get_cash_balance(),
                    ))
                    self.last_buy_price = price
                elif row['positions'] == Signal.SELL.value:
                    price = Decimal(row['price'])
                    # TODO: make this model driven
                    shares = self.account.get_num_shares_for(self.alpha_model.symbol)
                    self.account.sell_shares(symbol=self.alpha_model.symbol, amount=shares, price=price)
                    logger.debug("SELL {0} at {1} (bought at {2}) for gain of {3}".format(
                        self.account.get_num_shares_for(self.alpha_model.symbol),
                        price,
                        self.last_buy_price,
                        "TBD", # TODO: create returns model
                    ))

            self.start_price = Decimal(data.iloc[0]['open'])
            self.end_price = Decimal(data.iloc[-1]['close'])
            net_gain = self.account.get_account_value(security_prices={self.alpha_model.symbol: Decimal(self.end_price)}) - Decimal(self.seed_investment)
            logger.debug("Finished. Starting portfolio cash={5} and price={6} || Final portfolio cash={0} | holdings={1} at {2} ({3}) | net gain={4} ({7}) || baseline gain={8} | trades={9}".format(
                self.account.get_cash_balance(),
                self.account.get_num_shares_for(self.alpha_model.symbol),
                self.end_price,
                self.account.get_num_shares_for(self.alpha_model.symbol) * Decimal(self.end_price),
                net_gain,
                self.seed_investment,
                self.start_price,
                net_gain / self.seed_investment,
                (self.end_price / self.start_price) - 1,
                self.account.num_trades(),
                ))

            return evts

    def backtest_by_replay(self, max_records: int = -1):
        logger.info("starting backtest_by_replay...")
        with open(self.data_path, "r") as f:
            csvreader = csv.reader(f, delimiter=',', quotechar='"')
            header = next(csvreader)
            num_rows: int = 0
            for row in csvreader:
                # start = datetime.now()
                num_rows += 1
                if max_records > 0 and num_rows > max_records:
                    break
                hloc = OHLC.from_csv(row, timestamp_as_str=True)
                if num_rows % 100 == 0:
                    logger.debug("processing row #{1}: hloc={0}".format(hloc, num_rows))
                # logger.debug("processing hloc={0}".format(hloc))
                self.alpha_model.on_hloc(hloc)
                # print((datetime.now() - start).microseconds)

        self.start_price = self.alpha_model.hloc_data.iloc[0]['price']
        self.end_price = self.alpha_model.hloc_data.iloc[-1]['price']
        self.net_gain = (self.holdings * self.end_price) + self.cash - self.seed_inv

        logger.info("Finished. Starting portfolio cash={5} and price={6} || Final portfolio cash={0} | holdings={1} at {2} ({3}) | net gain={4} ({7}) || baseline gain={8}".format(
            self.cash,
            self.holdings,
            self.end_price,
            self.holdings * self.end_price,
            self.net_txn_gain,
            self.seed_inv,
            self.start_price,
            self.net_gain / self.seed_inv,
            self.start_price / self.end_price,
        ))

    def on_signal(self, signal: Signal):
        logger.info("on signal {0}".format(signal))
        if signal == Signal.BUY:
            if self.holdings == 0.0:
                price = self.alpha_model.hloc_data.iloc[-1]['price']
                self.holdings = self.cash / price
                logger.info("BUY {0} at {1} (total cash: {2}".format(
                    self.holdings,
                    price,
                    self.cash,
                ))
                self.cash = 0.0
                self.last_buy_price = price
                self.num_trades += 1
                if self.brokerage_model is not None:
                    self.total_fees += self.brokerage_model.get_fee(self.holdings, price)
            else:
                logger.warning("Got a BUY signal with holdings")
                # raise AssertionError()
        elif signal == Signal.SELL:
            if self.holdings > 0.0:
                price = self.alpha_model.hloc_data.iloc[-1]['price']
                self.cash = self.holdings * price
                gain = (self.holdings * price) - (self.holdings * self.last_buy_price)
                logger.info("SELL {0} at {1} (bought at {2}) for gain of {3}".format(
                    self.holdings,
                    price,
                    self.last_buy_price,
                    gain,
                ))
                self.net_txn_gain += gain
                if self.brokerage_model is not None:
                    self.total_fees += self.brokerage_model.get_fee(self.holdings, price)
                self.holdings = 0.0
                self.last_buy_price = 0.0
                self.num_trades += 1
            else:
                logger.warning("Got a SELL signal with no holdings")
                # raise AssertionError()


