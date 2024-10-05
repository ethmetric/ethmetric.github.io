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
value = 100 * (10**18)


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
        else:
            if addr in holding100eth:
                del holding100eth[addr]

    for addr in holding100eth:
        holding100eth[addr] += 1

    output_file = file.replace("balanceupdate_daily", "holding100eth_daily")
    with open(output_file, "w") as f:
        for addr in holding100eth:
            f.write(addr+","+str(holding100eth[addr])+"\n")