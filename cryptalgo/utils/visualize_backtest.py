import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

plt.style.use('dark_background')

tickers = [
    'ALGO',
    'ATOM',
    'BCH',
    'BTC',
    'DASH',
    'ETH',
    'LINK',
    'LTC',
    'MATIC',
    'ZRX',
]

model_name = 'MACD'

rows = int(len(tickers) / 2 if len(tickers) % 2 == 0 else len(tickers) / 2 + 1)
cols = 2
fig, axs = plt.subplots(
    nrows=rows,
    ncols=cols,
    figsize=(20, 10 * rows)
)
print(axs.shape)
for rnum in range(rows):
    for cnum in range(cols):
        ax = axs[rnum, cnum]
        idx = (rnum * cols) + cnum
        k = tickers[idx]
        # extracting Data for plotting
        data_df = pd.read_csv('./data/out/algo_{1}/{1}_backtests_{0}_all.csv'.format(k, model_name), header=0)
        data_df['rel_gain'] = data_df['growth'] - data_df['price_chg']

        df_p = pd.pivot_table(data_df[['st','lt','rel_gain']], index='st', columns='lt', values='rel_gain')
        # df_p = pd.pivot_table(data_df[['st','lt','growth']], index='st', columns='lt', values='growth')

        g = sns.heatmap(df_p, linewidth=0.5, center=0.0, vmin=-2.0, vmax=2.0, ax=ax)
        # g = sns.heatmap(df_p, linewidth=0.5, center=0.0, vmin=-1.0, vmax=5.0, ax=ax)
        g.set(title=k)

plt.subplots_adjust(hspace=0.30, wspace=0.25)
# plt.title('Abs Gain')
plt.title('Rel Gain')
plt.show()
