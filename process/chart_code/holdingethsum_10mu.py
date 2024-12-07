import glob


holding10mueth_daily_files = glob.glob("intermediate_data/holding10mueth_daily/*")
holding10mueth_daily_files.sort()


f = open("chart_data/hodingethsum_10mu.txt", "w")

value = 10000000

for file in holding10mueth_daily_files:
    print("read", file)
    lines = open(file).read().split("\n")[:-1]
    sum = 0
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        u_balance = float(arr[1])
        if u_balance >= value:
            sum += u_balance

    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(sum)+"\n")

f.close()
