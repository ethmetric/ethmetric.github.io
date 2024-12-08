import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str, dao_hardfork_beneficiary, dao_hardfork_accounts, date_to_day_time, date_to_last_block, begin_end, prune_files, read_first_line_gt_block
import glob
import functools
import time


f = open("chart_data/total_burnt_fees.txt", "w")

BlockInfoCsvs = glob.glob(datadir+"*Block_Info.csv")
BlockInfoCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))
BlockInfoCsvs = prune_files(BlockInfoCsvs, 12965000)

last_write_daytime = 0
total_fees = 0

for file in BlockInfoCsvs:
    print("read", file)
    blockInfoCSV = open(file)

    head = blockInfoCSV.readline().strip()
    line = read_first_line_gt_block(blockInfoCSV, 12965000)

    while line != "":
        arr = line.split(",")
        # blockNumber,timestamp,size,difficulty,transactionCount,internalTxCntSimple,internalTxCntAdvanced,erc20TxCnt,erc721TxCnt,minerAddress,minerExtra,gasLimit,gasUsed,minGasPrice,maxGasPrice,avgGasPrice,txFees,baseFeePerGas,burntFees,tipsFees,blobGasUsed,excessBlobGas,blobBaseFeePerGas,blobTxCnt,blobCnt
        timestamp = int(arr[1])
        burntFees = to_int(arr[18])
        total_fees += burntFees

        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            eth = total_fees/(10**18)
            eth = round(eth, 3)
            print(day, eth)
            f.write(day+","+str(eth)+"\n")
            total_fees = 0

        line = blockInfoCSV.readline().strip()

f.close()