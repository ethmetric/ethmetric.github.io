import glob


holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")
createdcontract_daily_files = glob.glob("intermediate_data/createdcontract_daily/*")

holding100eth_daily_files.sort()
createdcontract_daily_files.sort()


contracts = set()

for file in createdcontract_daily_files:
    print("read", file)
    lines = open(file).readlines()
    for line in lines:
        contracts.add(line.strip())

print(len(contracts))

f = open("chart_data/eoasum_100eth.txt", "w")

for file in holding100eth_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    eoasum = 0
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[2])
        if addr not in contracts:
            eoasum += balance

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(eoasum/(10**18))+"\n")

f.close()
