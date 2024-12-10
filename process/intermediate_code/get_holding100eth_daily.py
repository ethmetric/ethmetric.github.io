import glob
import os

output_dir = "intermediate_data/holding100eth_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

balanceupdate_daily_files = glob.glob("intermediate_data/balanceupdate_daily/*")

balanceupdate_daily_files.sort()

holding100eth = {}
balance_of = {}
value = 100 * (10**18)

only_update = False
files = os.listdir(output_dir)
files.sort()
only_update = len(files) > 0

if only_update:
    print("only_update from", files[-1])
    lines = open(output_dir+files[-1]).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        holding100eth[addr] = int(arr[1])
        balance_of[addr] = int(arr[2])
    balanceupdate_daily_files = balanceupdate_daily_files[len(files):]

for file in balanceupdate_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if balance >= value:
            if addr not in holding100eth:
                holding100eth[addr] = 0
            balance_of[addr] = balance
        else:
            if addr in holding100eth:
                del holding100eth[addr]
                del balance_of[addr]

    for addr in holding100eth:
        holding100eth[addr] += 1

    output_file = file.replace("balanceupdate_daily", "holding100eth_daily")
    with open(output_file, "w") as f:
        for addr in holding100eth:
            f.write(addr+","+str(holding100eth[addr])+","+str(balance_of[addr])+"\n")