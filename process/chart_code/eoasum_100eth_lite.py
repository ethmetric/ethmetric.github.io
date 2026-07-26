# lite version of eoasum_100eth.py: total balance of EOA (>= 100 ETH) per day.
#
# Difference from the original:
# - point-in-time semantics: an address is excluded only from the day it was
#   created as a contract (e.g. a CREATE2 counterfactual address still counts
#   as EOA before its deployment). History never changes once written, so this
#   script is incremental: it reads the last day of the existing output and
#   only computes newer days, then rewrites the whole output atomically
#   (tmp + rename). Delete the output file to trigger a full rebuild.
# - the original uses final semantics (an address known as a contract is
#   excluded from ALL history), which forces a full recompute every day.
#
# run from process/:  python3 chart_code/eoasum_100eth_lite.py
import os
import glob

output_path = "chart_data/eoasum_100eth.txt"

holding_files = glob.glob("intermediate_data/holding100eth_daily/*")
holding_files.sort()
created_files = glob.glob("intermediate_data/createdcontract_daily/*")
created_files.sort()

# existing results: day -> value
results = {}
last_day = None
if os.path.exists(output_path):
    for line in open(output_path).read().split("\n")[:-1]:
        arr = line.split(",")
        results[arr[0]] = arr[1]
        last_day = arr[0] if last_day is None else max(last_day, arr[0])

todo = [f for f in holding_files
        if last_day is None or f.split("/")[-1].split(".")[0] > last_day]

if not todo:
    print("up to date, last day:", last_day)
    exit(0)

print("last day:", last_day, " todo:", len(todo), "days")

# point-in-time contract set: only contracts created up to the day being
# computed are added
created_days = [f.split("/")[-1].split(".")[0] for f in created_files]
contracts = set()
created_idx = 0

for file in todo:
    day = file.split("/")[-1].split(".")[0]

    while created_idx < len(created_days) and created_days[created_idx] <= day:
        for line in open(created_files[created_idx]).readlines():
            contracts.add(line.strip())
        created_idx += 1

    print("read", file, "contracts so far", len(contracts))
    lines = open(file).read().split("\n")[:-1]
    eoasum = 0
    for line in lines:
        arr = line.strip().split(",")
        if arr[0] not in contracts:
            eoasum += int(arr[2])
    results[day] = str(eoasum / (10**18))

with open(output_path + ".tmp", "w") as f:
    for day in sorted(results):
        f.write(day + "," + results[day] + "\n")
os.replace(output_path + ".tmp", output_path)
print("wrote", output_path, len(results), "days")
