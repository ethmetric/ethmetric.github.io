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


f = open("chart_data/eoahoding100eth_30d.txt", "w")

for file in holding100eth_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    hoding100eth_30d = 0
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        holdingdays = int(arr[1])
        if holdingdays >= 30 and addr not in contracts:
            hoding100eth_30d += 1

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(hoding100eth_30d)+"\n")

f.close()
