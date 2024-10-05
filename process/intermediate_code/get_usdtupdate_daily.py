import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str, dao_hardfork_beneficiary, dao_hardfork_accounts
import glob
import functools

output_dir = "intermediate_data/usdtupdate_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

ERC20TransactionCsvs = glob.glob(datadir+"*ERC20Transaction.csv")
ERC20TransactionCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))


print(datadir, ERC20TransactionCsvs)

last_write_daytime = 0
usdt_of = {}
usdtupdate_of = {}

import time
start = time.time()

def add(to, value):
    if to not in usdt_of:
        usdt_of[to] = 0
    usdt_of[to] += value
    usdtupdate_of[to] = usdt_of[to]

def sub(sender, value):
    if sender not in usdt_of:
        usdt_of[sender] = 0
    usdt_of[sender] -= value
    usdtupdate_of[sender] = usdt_of[sender]

def transfer(sender, to, value):
    sub(sender, value)
    add(to, value)


last_write_daytime = 0

for file in ERC20TransactionCsvs:
    erc20TxCSV = open(file)

    head = erc20TxCSV.readline()


    erc20TxLine = erc20TxCSV.readline().strip()

    while (erc20TxLine!=""):

        oneArray = erc20TxLine.split(",")
        erc20TxLine = erc20TxCSV.readline().strip()

        # blockNumber,timestamp,transactionHash,tokenAddress,from,to,fromIsContract,toIsContract,amount
        tokenAddress = oneArray[3]

        if tokenAddress != "0xdac17f958d2ee523a2206206994597c13d831ec7":
            continue
            
        timestamp = int(oneArray[1])
        sender = oneArray[4]
        to = oneArray[5]
        amount = int(oneArray[8])

        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            
            print(day, last_write_daytime, len(usdtupdate_of))
            with open(output_dir + str(day) + ".txt", "w") as f:
                for addr in usdtupdate_of:
                    f.write(addr+","+str(usdtupdate_of[addr])+"\n")
            usdtupdate_of = {}
            
        transfer(sender, to, amount)
        

    erc20TxCSV.close()
