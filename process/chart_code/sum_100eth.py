import glob


holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")
createdcontract_daily_files = glob.glob("intermediate_data/createdcontract_daily/*")

holding100eth_daily_files.sort()
createdcontract_daily_files.sort()

f = open("chart_data/sum_100eth.txt", "w")

for file in holding100eth_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    sum = 0
    for line in lines:
        arr = line.strip().split(",")
        balance = int(arr[2])
        sum += balance

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(sum/(10**18))+"\n")

f.close()
