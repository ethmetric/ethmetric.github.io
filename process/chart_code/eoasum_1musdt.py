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


gt_1musdt = {}
gt_sum = 0
value = 10**12

f = open("chart_data/eoasum_1musdt.txt", "w")

for file in usdtupdate_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if addr not in contracts and balance >= 0:
            if balance >= value:
                if addr in gt_1musdt:
                    gt_sum -= gt_1musdt[addr]
                gt_sum += balance
                gt_1musdt[addr] = balance

            else:
                if addr in gt_1musdt:
                    gt_sum -= gt_1musdt[addr]
                    del gt_1musdt[addr]

    print("finish")
    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(len(gt_1musdt))+","+str(gt_sum)+"\n")

f.close()