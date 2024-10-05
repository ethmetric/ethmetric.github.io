import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str
import glob
import functools

output_dir = "intermediate_data/activeuser_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

BlockTransactionCsvs = glob.glob(datadir+"*BlockTransaction.csv")
BlockTransactionCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

print(datadir, BlockTransactionCsvs)

last_write_daytime = 0
activeusers = set()

import time
start = time.time()

for file in BlockTransactionCsvs:
    theCSV = open(file)
    head = theCSV.readline().strip()

    oneLine = theCSV.readline().strip()
    while oneLine!="":
        oneArray = oneLine.split(",")

        timestamp = int(oneArray[1])
        sender = oneArray[3]

        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            
            print(day, last_write_daytime, len(activeusers))
            with open(output_dir + str(day) + ".txt", "w") as f:
                for i in activeusers:
                    f.write(i+"\n")
                activeusers = set()
        
        activeusers.add(sender)

        oneLine = theCSV.readline().strip()

    theCSV.close()
