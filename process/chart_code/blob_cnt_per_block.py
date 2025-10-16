import glob

f = open("chart_data/blob_cnt_per_block.txt", "w")

blobtx_daily_files = glob.glob("intermediate_data/blobtx_daily/*")

blobtx_daily_files.sort()

for file in blobtx_daily_files:
    print("read", file)
    total_blobs = 0

    lines = open(file).read().split("\n")[:-1]
    if len(lines) == 0:
        continue
    first_block = int(lines[0].split(",")[0])
    last_block = int(lines[-1].split(",")[0])

    for line in lines:
        blobHashes = line.split(",")[18].split(":")
        # blockNumber,timestamp,transactionHash,from,to,toCreate,fromIsContract,toIsContract,value,gasLimit,gasPrice,gasUsed,callingFunction,isError,eip2718type,baseFeePerGas,maxFeePerGas,maxPriorityFeePerGas,blobHashes,blobBaseFeePerGas,blobGasUsed
        total_blobs += len(blobHashes)

    day = file.split("/")[-1].split(".")[0]
    cnt_per_block = total_blobs / (last_block - first_block + 1)
    cnt_per_block = round(cnt_per_block, 2)
    f.write(day+","+str(cnt_per_block)+"\n")


f.close()