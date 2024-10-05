import glob


balanceupdate_daily_files = glob.glob("intermediate_data/balanceupdate_daily/*")
createdcontract_daily_files = glob.glob("intermediate_data/createdcontract_daily/*")

balanceupdate_daily_files.sort()
createdcontract_daily_files.sort()


contracts = set()

for file in createdcontract_daily_files:
    print("read", file)
    lines = open(file).readlines()
    for line in lines:
        contracts.add(line.strip())

print(len(contracts))


gt_100eth = {}
lt_100eth = {}
gt_sum = 0
lt_sum = 0
value = 100 * (10**18)

f = open("chart_data/eoasum_100eth.txt", "w")

for file in balanceupdate_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if addr not in contracts:
            if balance >= value:
                if addr in gt_100eth:
                    gt_sum -= gt_100eth[addr]
                gt_sum += balance
                gt_100eth[addr] = balance
                if addr in lt_100eth:
                    lt_sum -= lt_100eth[addr]
                    del lt_100eth[addr]

            else:
                if addr in lt_100eth:
                    lt_sum -= lt_100eth[addr]
                lt_sum += balance
                lt_100eth[addr] = balance
                if addr in gt_100eth:
                    gt_sum -= gt_100eth[addr]
                    del gt_100eth[addr]

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(len(gt_100eth))+","+str(len(lt_100eth))+","+str(len(gt_100eth)/len(lt_100eth))+","+str(gt_sum)+","+str(lt_sum)+","+str(gt_sum/lt_sum)+"\n")

f.close()

with open("intermediate_data/gt_100eth.txt", "w") as f:
    for addr in gt_100eth:
        f.write(addr+","+str(gt_100eth[addr])+"\n")
with open("intermediate_data/lt_100eth.txt", "w") as f:
    for addr in lt_100eth:
        f.write(addr+","+str(lt_100eth[addr])+"\n")