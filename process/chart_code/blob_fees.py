import glob

f = open("chart_data/blob_fees.txt", "w")

blobtx_daily_files = glob.glob("intermediate_data/blobtx_daily/*")

blobtx_daily_files.sort()

for file in blobtx_daily_files:
    print("read", file)
    total_fees = 0

    lines = open(file).read().split("\n")[:-1]
    first_block = int(lines[0].split(",")[0])
    last_block = int(lines[-1].split(",")[0])

    for line in lines:
        arr = line.split(",")
        # blockNumber,timestamp,transactionHash,from,to,toCreate,fromIsContract,toIsContract,value,gasLimit,gasPrice,gasUsed,callingFunction,isError,eip2718type,baseFeePerGas,maxFeePerGas,maxPriorityFeePerGas,blobHashes,blobBaseFeePerGas,blobGasUsed
        blobBaseFeePerGas = int(arr[19])
        blobGasUsed       = int(arr[20])
        total_fees  += blobBaseFeePerGas*blobGasUsed

    eth = total_fees/(10**18)
    if eth > 0.01:
        eth = round(eth, 3)
    day = file.split("/")[-1].split(".")[0]
    f.write(day+","+str(eth)+"\n")


f.close()