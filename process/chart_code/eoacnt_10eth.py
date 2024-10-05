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


eoacnt_10eth = set()
value = 10 * (10**18)

f = open("chart_data/eoacnt_10eth.txt", "w")

for file in balanceupdate_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if addr not in contracts:
            if balance >= value:
                eoacnt_10eth.add(addr)
            else:
                if addr in eoacnt_10eth:
                    eoacnt_10eth.remove(addr)

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(len(eoacnt_10eth))+"\n")

f.close()

with open("intermediate_data/eoacnt_10eth.txt", "w") as f:
    for i in eoacnt_10eth:
        f.write(i+"\n")