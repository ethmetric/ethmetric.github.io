import glob


usdtupdate_daily_files = glob.glob("intermediate_data/usdtupdate_daily/*")
createdcontract_daily_files = glob.glob("intermediate_data/createdcontract_daily/*")

usdtupdate_daily_files.sort()
createdcontract_daily_files.sort()


contracts = set()

for file in createdcontract_daily_files:
    print("read", file)
    lines = open(file).readlines()
    for line in lines:
        contracts.add(line.strip())

print(len(contracts))


gt_10000usdt = {}
lt_10000usdt = {}
gt_sum = 0
lt_sum = 0
value = 10000000000

f = open("chart_data/eoarate_10000usdt.txt", "w")

for file in usdtupdate_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if addr not in contracts and balance >= 0:
            if balance >= value:
                if addr in gt_10000usdt:
                    gt_sum -= gt_10000usdt[addr]
                gt_sum += balance
                gt_10000usdt[addr] = balance
                if addr in lt_10000usdt:
                    lt_sum -= lt_10000usdt[addr]
                    del lt_10000usdt[addr]

            else:
                if addr in lt_10000usdt:
                    lt_sum -= lt_10000usdt[addr]
                lt_sum += balance
                lt_10000usdt[addr] = balance
                if addr in gt_10000usdt:
                    gt_sum -= gt_10000usdt[addr]
                    del gt_10000usdt[addr]

    print("finish")
    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(len(gt_10000usdt))+","+str(len(lt_10000usdt))+","+str(gt_sum)+","+str(lt_sum)+"\n")

f.close()

with open("intermediate_data/gt_10000usdt.txt", "w") as f:
    for addr in gt_10000usdt:
        f.write(addr+","+str(gt_10000usdt[addr])+"\n")
with open("intermediate_data/lt_10000usdt.txt", "w") as f:
    for addr in lt_10000usdt:
        f.write(addr+","+str(lt_10000usdt[addr])+"\n")