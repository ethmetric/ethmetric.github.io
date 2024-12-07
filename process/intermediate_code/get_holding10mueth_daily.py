import glob
import os

output_dir = "intermediate_data/holding10mueth_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")

holding100eth_daily_files.sort()

holding10mueth = {}
value = 10000000

# load price
price_of = {}
lines = open("chart_data/ethprice.txt").readlines()
for line in lines[:-1]:
    arr = line.strip().split(",")
    price_of[arr[0]] = float(arr[1])

for file in holding100eth_daily_files:
    print("read", file)
    day = file.split("/")[-1].split(".")[0]
    if day not in price_of:
        continue
    
    output_file = file.replace("holding100eth_daily", "holding10mueth_daily")
    f = open(output_file, "w")

    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[2])
        u_balance = balance * price_of[day] / (10**18)
        if u_balance >= value:
            f.write(addr+","+str(u_balance)+"\n")
            
    f.close()