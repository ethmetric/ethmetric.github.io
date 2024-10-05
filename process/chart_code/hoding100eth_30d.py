import glob


holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")
holding100eth_daily_files.sort()


f = open("chart_data/hoding100eth_30d.txt", "w")

for file in holding100eth_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    hoding100eth_30d = 0
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        holdingdays = int(arr[1])
        if holdingdays >= 30:
            hoding100eth_30d += 1

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(hoding100eth_30d)+"\n")

f.close()
