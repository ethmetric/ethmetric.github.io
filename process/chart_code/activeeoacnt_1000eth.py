import glob


balanceupdate_daily_files = glob.glob("intermediate_data/balanceupdate_daily/*")

balanceupdate_daily_files.sort()


addr_1000eth = set()
value = 1000 * (10**18)

f = open("chart_data/activeeoacnt_1000eth.txt", "w")

for file in balanceupdate_daily_files:
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if balance >= value:
            addr_1000eth.add(addr)
        else:
            if addr in addr_1000eth:
                addr_1000eth.remove(addr)


    activeeoacnt_1000eth = 0
    activeuser_file = file.replace("balanceupdate_daily", "activeuser_daily")

    lines = open(activeuser_file).read().split("\n")[:-1]
    for line in lines:
        eoa = line.strip()
        if eoa in addr_1000eth:
            activeeoacnt_1000eth += 1

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(activeeoacnt_1000eth)+"\n")
    print(day, activeeoacnt_1000eth)

f.close()

with open("intermediate_data/addr_1000eth.txt", "w") as f:
    for i in addr_1000eth:
        f.write(i+"\n")