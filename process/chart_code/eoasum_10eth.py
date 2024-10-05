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


eoa_10eth = {}
eoasum = 0
value = 10 * (10**18)

f = open("chart_data/eoasum_10eth.txt", "w")

for file in balanceupdate_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if addr not in contracts:
            if balance >= value:
                if addr in eoa_10eth:
                    eoasum -= eoa_10eth[addr]
                eoasum += balance
                eoa_10eth[addr] = balance
            else:
                if addr in eoa_10eth:
                    eoasum -= eoa_10eth[addr]
                    del eoa_10eth[addr]

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(eoasum/(10**18))+"\n")

f.close()

with open("intermediate_data/eoasum_10eth.txt", "w") as f:
    for addr in eoa_10eth:
        f.write(addr+","+str(eoa_10eth[addr])+"\n")