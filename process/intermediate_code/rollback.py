import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir, sort_by_blocknum, date_to_day_time, date_to_last_block, prune_files, read_first_line_gt_block
import glob
import functools
import time

lastday = open("chart_data/beacon_deposit.txt").read().split("\n")[-2][:10]

files = glob.glob("intermediate_data/*/*")

for file in files:
    if file.split("/")[-1].split(".")[0] > lastday:
        print(file)
        os.remove(file)
