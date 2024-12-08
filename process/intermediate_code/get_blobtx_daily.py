import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str, dao_hardfork_beneficiary, dao_hardfork_accounts, date_to_day_time, date_to_last_block, begin_end, prune_files, read_first_line_gt_block
import glob
import functools
import time

output_dir = "intermediate_data/blobtx_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

BlockTransactionCsvs = glob.glob(datadir+"*BlockTransaction.csv")
BlockTransactionCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

last_write_daytime = 0
blobtxs = []

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
else:
    BlockTransactionCsvs = prune_files(BlockTransactionCsvs, 19426587)


for file in BlockTransactionCsvs:
    print("read", file)
    blockTxCSV = open(file)

    head = blockTxCSV.readline()

    if only_update:
        blockTxLine = read_first_line_gt_block(blockTxCSV, last_block)
    else:
        blockTxLine = read_first_line_gt_block(blockTxCSV, 19426587)

    while (blockTxLine!=""):
        blockTxArray = blockTxLine.split(",")
        blockNumber = int(blockTxArray[0])
        timestamp = int(blockTxArray[1])
        eip2718type = to_int(blockTxArray[14])

        if eip2718type == 3:
            blobtxs.append(blockTxLine)

        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            
            print(day, last_write_daytime, len(blobtxs))

            with open(output_dir + str(day) + ".txt", "w") as f:
                for blobtx in blobtxs:
                    f.write(blobtx+"\n")

            blobtxs = []
        
        blockTxLine = blockTxCSV.readline().strip()    

    blockTxCSV.close()