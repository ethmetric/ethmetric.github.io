import glob

activeuser_daily_files = glob.glob("intermediate_data/activeuser_daily/*")

activeuser_daily_files.sort()


f = open("chart_data/activeuser.txt", "w")


for file in activeuser_daily_files:
    lines = open(file).read().split("\n")[:-1]
    
    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(len(lines))+"\n")
    print(day, len(lines))

f.close()