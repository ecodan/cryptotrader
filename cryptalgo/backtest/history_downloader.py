import datetime
import os
import time
import cbpro
import csv

# columns=['time', 'low', 'high', 'open', 'close', 'volume']
# ticker = 'ETH-USD'
# out_dir = "/Users/dan/dev/code/projects/python/cryptotrader/data"
# with open(os.path.join(out_dir, "{0}.csv".format(ticker)), "w") as out_file:
#     writer = csv.writer(out_file, dialect="excel")
#     writer.writerow(columns)
#
#     pub = cbpro.PublicClient()
#     num_records = 0
#     record_start = datetime.datetime(2017, 1, 1, 0, 0, 0)
#     record_end = datetime.datetime(2021, 2, 15, 0, 0, 0)
#     marker = record_start
#     while marker < record_end:
#         start = marker
#         end = start + datetime.timedelta(minutes=5 * 300)
#         res = pub.get_product_historic_rates(ticker, start=start, end=end, granularity=300)
#         try:
#             res2 = [[datetime.datetime.fromtimestamp(x[0]), x[1], x[2], x[3], x[4], x[5]] for x in res]
#         except TypeError:
#             print("TypeError; res={0}".format(res))
#             break
#         num_records += len(res)
#         print("start: {0} len={1}".format(start, num_records))
#         writer.writerows(res2)
#         marker = end
#         time.sleep(1)

# wsClient = cbpro.WebsocketClient(url="wss://ws-feed.pro.coinbase.com",
#                                 products="ETH-USD",
#                                 channels=["ticker"])
#
# # Do other stuff...
# wsClient.close()

import cbpro, time



class myWebsocketClient(cbpro.WebsocketClient):
    def on_open(self):
        self.url = "wss://ws-feed.pro.coinbase.com/"
        self.products = ["LTC-USD"]
        self.channels = ["ticker"]
        self.message_count = 0
        print("Lets count the messages!")


    def on_message(self, msg):
        self.message_count += 1
        print(msg)
        if 'price' in msg and 'type' in msg:
            print("Message type:", msg["type"],
                  "\t@ {:.3f}".format(float(msg["price"])))


    def on_close(self):
        print("-- Goodbye! --")



wsClient = myWebsocketClient()
wsClient.start()
print(wsClient.url, wsClient.products)
while (wsClient.message_count < 500):
    print("\nmessage_count =", "{} \n".format(wsClient.message_count))
    time.sleep(1)
wsClient.close()
