import csv
import decimal
from datetime import timedelta
from pathlib import Path
import pandas as pd
from cryptalgo.backtest.backtest import BacktestHarness
from cryptalgo.brain.models import SMACModel, MACDModel
import logging
import matplotlib.pyplot as plt
from cryptalgo.inputs.feed_agg import AggPeriod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s: [%(filename)s:%(funcName)s:%(lineno)d] %(message)s'
)

logger = logging.getLogger(__name__)

# from logging.config import dictConfig
#
# logging_config = dict(
#     version = 1,
#     formatters = {
#         'f': {'format':
#                   '%(asctime)s | %(levelname)s: [%(filename)s:%(funcName)s:%(lineno)d] %(message)s'}
#     },
#     handlers = {
#         'h': {'class': 'logging.StreamHandler',
#               'formatter': 'f',
#               'level': logging.DEBUG}
#     },
#     root = {
#         'handlers': ['h'],
#         'level': logging.DEBUG,
#     },
# )
# dictConfig(logging_config)


histories = {
    'LTC': Path('./data/candles/LTC-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'ETH': Path('./data/candles/ETH-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'MATIC': Path('./data/candles/MATIC-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'BTC': Path('./data/candles/BTC-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'BCH': Path('./data/candles/BCH-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'ZRX': Path('./data/candles/ZRX-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'ATOM': Path('./data/candles/ATOM-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'ALGO': Path('./data/candles/ALGO-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'DASH': Path('./data/candles/DASH-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
    'LINK': Path('./data/candles/LINK-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'),
}


def load_dataframe(path: Path):
    df = pd.read_csv(path, sep=",", quotechar='"', parse_dates=['time'])
    df.set_index('time', inplace=True)
    df.sort_index(ascending=True, inplace=True)
    return df



def smac_parameter_hunt(key: str, agg_period: AggPeriod):
    k = key
    df = load_dataframe(Path(histories[k]))

    with open("./data/out/algo_smac/smac_backtests_{0}_params.csv".format(k), "w") as f:
        writer = csv.writer(f, "excel")
        hdr = ['st', 'lt']
        hdr.extend([str(x) for x in BacktestHarness.generate_report_header()])
        writer.writerow(hdr)

        for st in range(10, 250, 10):
            for lt in range((st + 10), 250, 10):
                logger.info("modeling {2}: {0}, {1}".format(st, lt, k))
                model = SMACModel("{0}-USD".format(k), short_lb=st, long_lb=lt)
                bt = BacktestHarness(model, seed_investment=1000.00, agg_period=agg_period)
                bt.backtest_single_pass(df)
                with decimal.localcontext() as ctx:
                    ctx.prec = 5
                    rpt = [st, lt]
                    rpt.extend([str(x) for x in bt.generate_report()])
                    writer.writerow(rpt)
                    f.flush()



def macd_parameter_hunt(key: str, agg_period: AggPeriod):
    k = key
    df = load_dataframe(Path(histories[k]))

    with open("./data/out/algo_macd/macd_backtests_{0}_params.csv".format(k), "w") as f:
        writer = csv.writer(f, "excel")
        hdr = ['lewm', 'hewm']
        hdr.extend([str(x) for x in BacktestHarness.generate_report_header()])
        writer.writerow(hdr)

        for st in range(10, 16, 1):
            for lt in range(20, 30, 1):
                logger.info("modeling {2}: {0}, {1}".format(st, lt, k))
                model = MACDModel("{0}-USD".format(k), low_ewm=st, high_ewm=lt)
                bt = BacktestHarness(model, seed_investment=1000.00, agg_period=agg_period)
                bt.backtest_single_pass(df)
                with decimal.localcontext() as ctx:
                    ctx.prec = 5
                    rpt = [st, lt]
                    rpt.extend([str(x) for x in bt.generate_report()])
                    writer.writerow(rpt)
                    f.flush()



def macd_time_progression_results(key: str, lewm: int = 12, hewm: int = 26, agg_period: AggPeriod = AggPeriod.FIVE_MINUTES):
    logger.info("macd_time_progression_results starting...")
    k = key
    df = load_dataframe(Path(histories[k]))

    with open("./data/out/algo_macd/macd_backtests_{0}_time.csv".format(k), "w") as f:
        writer = csv.writer(f, "excel")
        hdr = ['date', 'lewm', 'hewm']
        hdr.extend([str(x) for x in BacktestHarness.generate_report_header()])
        writer.writerow(hdr)
        start_date = df.index[0] + timedelta(days=2)
        if agg_period == AggPeriod.ONE_DAY:
            start_date = df.index[0] + timedelta(days=26)
        for date in pd.date_range(start_date, df.index[-1], freq='D'):
            logger.info("modeling {2}: {0}, {1} through {3}".format(lewm, hewm, k, date))
            model = MACDModel("{0}-USD".format(k), low_ewm=lewm, high_ewm=hewm)
            bt = BacktestHarness(model, seed_investment=1000.00, agg_period=agg_period)
            bt.backtest_single_pass(df[df.index <= date])
            with decimal.localcontext() as ctx:
                ctx.prec = 5
                rpt = [date, lewm, hewm]
                rpt.extend([str(x) for x in bt.generate_report()])
                writer.writerow(rpt)
                f.flush()

    dfv = pd.read_csv("./data/out/algo_macd/macd_backtests_{0}_time.csv".format(k), parse_dates=['date'])
    ax = plt.gca()
    dfv[['price_chg','growth']].plot.line(ax=ax)
    plt.show()


if __name__ == '__main__':
    macd_time_progression_results('MATIC', agg_period=AggPeriod.ONE_DAY)