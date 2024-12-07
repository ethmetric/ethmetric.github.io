import glob
import os

f = open("chart_data/beacon_deposit.txt", "w")

holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")

holding100eth_daily_files.sort()

for file in holding100eth_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        if addr == "0x00000000219ab540356cbb839cbe05303d7705fa":
            print(line)
            day = file.split("/")[-1].split(".")[0]
            balance = int(arr[2]) / (10**18)
            f.write(day+","+str(balance)+"\n")


f.close()