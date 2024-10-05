import glob
import json
import time

files = glob.glob("source_data/price/*")
files.sort()


f = open("chart_data/ethprice.txt", "w")

"""
[
  [
    1499040000000,      // k线开盘时间
    "0.01634790",       // 开盘价
    "0.80000000",       // 最高价
    "0.01575800",       // 最低价
    "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
    "148976.11427815",  // 成交量
    1499644799999,      // k线收盘时间
    "2434.19055334",    // 成交额
    308,                // 成交笔数
    "1756.87402397",    // 主动买入成交量
    "28.46694368",      // 主动买入成交额
    "17928899.62484339" // 请忽略该参数
  ]
]
"""
for file in files:
    print("read", file)
    arr = json.loads(open(file).read())
    for i in arr:
        timestamp = int(i[0])/1000
        price = i[4]
        day = time.strftime('%Y-%m-%d', time.gmtime(timestamp))
        f.write(day+","+price+"\n")

f.close()
