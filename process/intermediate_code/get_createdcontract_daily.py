import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str,date_to_last_block,begin_end,date_to_day_time,prune_files
import glob
import functools

output_dir = "intermediate_data/createdcontract_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

ContractInfoCsvs = glob.glob(datadir+"*ContractInfo.csv")
ContractInfoCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

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
    ContractInfoCsvs = prune_files(ContractInfoCsvs, last_block)

print(datadir, ContractInfoCsvs)

contracts = []

import time

for file in ContractInfoCsvs:
    theCSV = open(file)
    head = theCSV.readline().strip()

    oneLine = theCSV.readline().strip()
    while oneLine!="":
        oneArray = oneLine.split(",")
        oneLine = theCSV.readline().strip()

        if only_update:
            createdBlockNumber = int(oneArray[1])
            if createdBlockNumber <= last_block:
                continue

        # address,createdBlockNumber,createdTimestamp,createdTransactionHash,creator,creatorIsContract,createValue,creationCode,contractCode
        address = oneArray[0]
        timestamp = int(oneArray[2])

        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            
            print(day, last_write_daytime, len(contracts))
            with open(output_dir + str(day) + ".txt", "w") as f:
                for i in contracts:
                    f.write(i+"\n")
            contracts = []
        
        contracts.append(address)


    theCSV.close()
