import glob


balanceupdate_daily_files = glob.glob("intermediate_data/balanceupdate_daily/*")

balanceupdate_daily_files.sort()


addr_10eth = set()
value = 10 * (10**18)

f = open("chart_data/activeeoacnt_10eth.txt", "w")

for file in balanceupdate_daily_files:
    lines = open(file).read().split("\n")[:-1]
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        balance = int(arr[1])
        if balance >= value:
            addr_10eth.add(addr)
        else:
            if addr in addr_10eth:
                addr_10eth.remove(addr)


    activeeoacnt_10eth = 0
    activeuser_file = file.replace("balanceupdate_daily", "activeuser_daily")

    lines = open(activeuser_file).read().split("\n")[:-1]
    for line in lines:
        eoa = line.strip()
        if eoa in addr_10eth:
            activeeoacnt_10eth += 1

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(activeeoacnt_10eth)+"\n")
    print(day, activeeoacnt_10eth)

f.close()

with open("intermediate_data/addr_10eth.txt", "w") as f:
    for i in addr_10eth:
        f.write(i+"\n")