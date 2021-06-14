# import required packages
from pathlib import Path

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
import matplotlib.dates as mpdates

from cryptalgo.backtest.backtest import BacktestHarness
from cryptalgo.brain.models import MACDModel
import logging

from cryptalgo.inputs.feed_agg import AggPeriod

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s | %(levelname)s: [%(filename)s:%(funcName)s:%(lineno)d] %(message)s'
)

plt.style.use('dark_background')

symbol = 'BTC'
df = pd.read_csv(Path('./data/candles/{0}-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv'.format(symbol)), sep=",", quotechar='"', parse_dates=['time'])
df.set_index('time', inplace=True)
df.sort_index(ascending=True, inplace=True)
model = MACDModel("{0}-USD".format(symbol), low_ewm=12, high_ewm=26)
bt = BacktestHarness(model, seed_investment=1000.00, agg_period=AggPeriod.ONE_DAY)
bt.backtest_single_pass(df[0:(120*24*12)])
bt.alpha_model.visualize()
logging.getLogger(__name__).critical("\n" + bt.report_as_string())




# # extracting Data for plotting
# data_df = pd.read_csv('./data/candles/LTC-USD-2021-01-01 00:00:00-2021-06-01 00:00:00-300-candles.csv', header=0,
#                       parse_dates=['time'])
# data_df.set_index('time', inplace=True)
# data_df = data_df.sort_index(ascending=True)
#
# data_df = data_df.iloc[0:1000]
#
# short_lb = 30
# long_lb = 90
#
# # trim to lookback
# # data_df = data_df.iloc[-1 * long_lb::].copy()
#
# signal_df = pd.DataFrame(index=data_df.index)
# signal_df['signal'] = 0.0
#
# # create a short simple moving average over the short lookback period
# signal_df['short_mav'] = data_df['close'].rolling(window=short_lb, min_periods=1, center=False).mean()
#
# # step4: create long simple moving average over the long lookback period
# signal_df['long_mav'] = data_df['close'].rolling(window=long_lb, min_periods=1, center=False).mean()
#
# # calculate signals
# signal_df['signal'][short_lb:] = np.where(signal_df['short_mav'][short_lb:] > signal_df['long_mav'][short_lb:], 1.0, 0.0)
#
# # fire events
# signal_df['positions'] = signal_df['signal'].diff()
# signal_df['sell_signals'] = signal_df.apply(lambda x: data_df.loc[x.name]['close'] if x['positions'] == -1 else np.NaN, axis=1)
# signal_df['buy_signals'] = signal_df.apply(lambda x: data_df.loc[x.name]['close'] if x['positions'] == 1 else np.NaN, axis=1)
#
# signal_df.to_csv('./data/signal_ref.csv')
#
# apds = [
#     mpf.make_addplot(signal_df['short_mav'], type='line', color='g'),
#     mpf.make_addplot(signal_df['long_mav'], type='line', color='b'),
#     mpf.make_addplot(signal_df['sell_signals'], type='scatter', markersize=200, marker='v'),
#     mpf.make_addplot(signal_df['buy_signals'], type='scatter', markersize=200, marker='^'),
# ]
# # mpf.plot(data_df, volume=True, addplot=apds, style='starsandstripes')
# mpf.plot(data_df, volume=True, addplot=apds)
