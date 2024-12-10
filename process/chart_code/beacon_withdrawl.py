import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str, dao_hardfork_beneficiary, dao_hardfork_accounts, date_to_day_time, date_to_last_block, begin_end, prune_files, read_first_line_gt_block
import glob
import functools
import time


f = open("chart_data/beacon_withdrawl.txt", "w")

WithdrawalCsvs = glob.glob(datadir+"*Withdrawal.csv")
WithdrawalCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

last_write_daytime = 0
sum = 0

for rewardCSV in WithdrawalCsvs:
    file = open(rewardCSV)
    head = file.readline().strip()
    rewardLine = file.readline().strip()
    while rewardLine != "":
        rewardArr = rewardLine.split(",")
        timestamp = int(rewardArr[1])
        reward_to = rewardArr[-2]
        reward_value = int(rewardArr[-1])
        sum += reward_value

        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            print(day, sum)
            f.write(day+","+str(sum/(10**18))+"\n")

        rewardLine = file.readline().strip()



f.close()