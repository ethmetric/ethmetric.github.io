import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir, sort_by_blocknum, date_to_day_time, date_to_last_block, prune_files, read_first_line_gt_block
import glob
import functools
import time

output_dir = "intermediate_data/activeuser_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

BlockTransactionCsvs = glob.glob(datadir+"*BlockTransaction.csv")
BlockTransactionCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))


last_write_daytime = 0

only_update = False
files = os.listdir(output_dir)
files.sort()
only_update = len(files) > 0

if only_update:
    last_date = files[-1].split(".")[0]
    last_write_daytime = date_to_day_time(last_date) + 86400
    last_block = date_to_last_block(last_date)
    print("only update from", last_block)
    BlockTransactionCsvs = prune_files(BlockTransactionCsvs, last_block)

print(datadir, BlockTransactionCsvs)

activeusers = set()


for file in BlockTransactionCsvs:
    theCSV = open(file)
    head = theCSV.readline().strip()

    if only_update:
        oneLine = read_first_line_gt_block(theCSV, last_block)
    else:
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
