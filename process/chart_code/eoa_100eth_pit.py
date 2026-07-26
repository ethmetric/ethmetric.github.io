"""Point-in-time EOA statistics: comparison tool.

The current eoacnt_100eth / eoasum_100eth / eoasum_top100_100eth scripts use
"final" semantics: once an address is known to be a contract it is excluded
from ALL history, which forces a full recompute every day.

This script recomputes the same metrics with point-in-time semantics: an
address is excluded only from the day it was created as a contract; before
its deployment (e.g. a CREATE2 counterfactual address that received ETH
early) it still counts as an EOA. History never changes once written, so
this semantics naturally supports incremental updates.

Output goes to NEW files, nothing is overwritten:
  chart_data/eoacnt_100eth_pit.txt
  chart_data/eoasum_100eth_pit.txt
  chart_data/eoasum_top100_100eth_pit.txt
At the end a per-day diff summary against the current data is printed.

run from process/:  python3 chart_code/eoa_100eth_pit.py
"""
import glob

holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")
createdcontract_daily_files = glob.glob("intermediate_data/createdcontract_daily/*")

holding100eth_daily_files.sort()
createdcontract_daily_files.sort()

# contract creation table by day: day -> [addr, ...]
created_by_day = {}
for file in createdcontract_daily_files:
    day = file.split("/")[-1].split(".")[0]
    created_by_day[day] = [line.strip() for line in open(file).readlines()]
created_days = sorted(created_by_day.keys())

contracts = set()       # contracts created up to the current day (pit)
created_idx = 0

f_cnt = open("chart_data/eoacnt_100eth_pit.txt", "w")
f_sum = open("chart_data/eoasum_100eth_pit.txt", "w")
f_top = open("chart_data/eoasum_top100_100eth_pit.txt", "w")

for file in holding100eth_daily_files:
    day = file.split("/")[-1].split(".")[0]

    # only contracts created on or before the current day are excluded
    while created_idx < len(created_days) and created_days[created_idx] <= day:
        contracts.update(created_by_day[created_days[created_idx]])
        created_idx += 1

    print("read", file, "contracts so far", len(contracts))
    lines = open(file).read().split("\n")[:-1]
    cnt = 0
    eoasum = 0
    balances = []
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        if addr in contracts:
            continue
        balance = int(arr[2])
        cnt += 1
        eoasum += balance
        balances.append(balance)
    balances.sort(reverse=True)
    topsum = sum(balances[:100])

    f_cnt.write(day + "," + str(cnt) + "\n")
    f_sum.write(day + "," + str(eoasum / (10**18)) + "\n")
    f_top.write(day + "," + str(topsum / (10**18)) + "\n")

f_cnt.close()
f_sum.close()
f_top.close()

# ==================== diff against current (final-semantics) data ====================

def load(path):
    ret = {}
    for line in open(path).read().split("\n")[:-1]:
        arr = line.split(",")
        ret[arr[0]] = float(arr[1])
    return ret

for old_path, new_path in (
    ("chart_data/eoacnt_100eth.txt", "chart_data/eoacnt_100eth_pit.txt"),
    ("chart_data/eoasum_100eth.txt", "chart_data/eoasum_100eth_pit.txt"),
    ("chart_data/eoasum_top100_100eth.txt", "chart_data/eoasum_top100_100eth_pit.txt"),
):
    old = load(old_path)
    new = load(new_path)
    days = sorted(set(old) & set(new))
    diffs = [(d, new[d] - old[d], old[d]) for d in days if abs(new[d] - old[d]) > 1e-9]
    print("====", old_path)
    print("days compared:", len(days), " days differ:", len(diffs))
    if diffs:
        worst = max(diffs, key=lambda x: abs(x[1] / x[2]) if x[2] else abs(x[1]))
        print("worst day:", worst[0], "old:", worst[2], "new:", worst[2] + worst[1],
              " rel diff:", round(abs(worst[1] / worst[2]) * 100, 6) if worst[2] else "n/a", "%")
        latest = diffs[-1]
        print("latest differ day:", latest[0], "old:", latest[2], "new:", latest[2] + latest[1])
