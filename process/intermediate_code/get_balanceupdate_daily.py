import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str, dao_hardfork_beneficiary, dao_hardfork_accounts
import glob
import functools

output_dir = "intermediate_data/balanceupdate_daily/"
try:
    os.mkdir(output_dir)
except:
    pass

BlockTransactionCsvs = glob.glob(datadir+"*BlockTransaction.csv")
BlockTransactionCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

IneternalTransactionCsvs = glob.glob(datadir+"*InternalTransaction.csv")
IneternalTransactionCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))


MinerRewardCsvs = glob.glob(datadir+"*MinerReward.csv")
MinerRewardCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

WithdrawalCsvs = glob.glob(datadir+"*Withdrawal.csv")
WithdrawalCsvs.sort(key=functools.cmp_to_key(sort_by_blocknum))

print(datadir, BlockTransactionCsvs, IneternalTransactionCsvs)

last_write_daytime = 0
balance_of = {}
balanceupdate_of = {}
genesis_lines = open("source_data/genesis.csv").read().split("\n")
for line in genesis_lines[:-1]:
    t = line.split(",")
    addr = t[0]
    balance = int(t[1])
    balance_of[addr] = balance
    balanceupdate_of[addr] = balance

import time
start = time.time()

def block_number(line):
    number = int(line.split(",")[0])
    return number

def internal_tx_hash(line):
    txhash = line.split(",")[2]
    return txhash

def add(to, value):
    if to not in balance_of:
        balance_of[to] = 0
    balance_of[to] += value
    balanceupdate_of[to] = balance_of[to]


def sub(sender, value):
    if sender not in balance_of or balance_of[sender] < value:
        print(sender, "err!")
        exit()
    balance_of[sender] -= value
    balanceupdate_of[sender] = balance_of[sender]


def transfer(sender, to, value):
    sub(sender, value)
    add(to, value)


for file in BlockTransactionCsvs:
    blockTxCSV = open(file)
    interTxCSV = open(file.replace("Block", "Internal"))
    blockInfoCsv = open(file.replace("BlockTransaction", "Block_Info"))

    rewardCSV = None
    if int(file.split("/")[-1].split("to")[0]) < 17000000:
        rewardCSV = open(file.replace("BlockTransaction", "Block_MinerReward"))
    else:
        rewardCSV = open(file.replace("BlockTransaction", "Block_Withdrawal"))


    head1 = blockTxCSV.readline()
    head2 = interTxCSV.readline()
    head3 = blockInfoCsv.readline()
    head4 = rewardCSV.readline()

    blockTxLine = blockTxCSV.readline().strip()    
    interTxLine = interTxCSV.readline().strip()
    blockInfoLine = blockInfoCsv.readline().strip()
    rewardLine = rewardCSV.readline().strip()

    current_blocknum = 0
    current_miner = ""

    while (blockTxLine!=""):
        # First step: read the block TX, 
        # because block TX is executed before the internal TX (the same tx hash).
        blockTxArray = blockTxLine.split(",")
        blockNumber = int(blockTxArray[0])
        timestamp = int(blockTxArray[1])
        transactionHash = blockTxArray[2]
        tx_sender = blockTxArray[3]
        tx_to = blockTxArray[4]
        tx_toCreate = blockTxArray[5]
        tx_value = int(blockTxArray[8])
        isError = blockTxArray[13]

        while current_blocknum != blockNumber:
            blockInfoArr = blockInfoLine.split(",")
            current_blocknum = int(blockInfoArr[0])
            current_miner = blockInfoArr[9]
            blockInfoLine = blockInfoCsv.readline().strip()

            if current_blocknum == 1920000:
                for addr in dao_hardfork_accounts:
                    if addr in balance_of:
                        transfer(addr, dao_hardfork_beneficiary, balance_of[addr])

        while rewardLine != "" and block_number(rewardLine) < blockNumber:
            rewardArr = rewardLine.split(",")
            reward_to = rewardArr[-2]
            reward_value = int(rewardArr[-1])
            add(reward_to, reward_value)
            rewardLine = rewardCSV.readline().strip()



        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            
            print(day, last_write_daytime, len(balanceupdate_of))
            with open(output_dir + str(day) + ".txt", "w") as f:
                for addr in balanceupdate_of:
                    f.write(addr+","+str(balanceupdate_of[addr])+"\n")
            balanceupdate_of = {}
        
        if isError == "None" and tx_value>0:
            if tx_to != "None":
                transfer(tx_sender, tx_to, tx_value)
            else:
                transfer(tx_sender, tx_toCreate, tx_value)

        suicided_contracts = set()

        # Seond step: read the internal TX
        while interTxLine != "" and internal_tx_hash(interTxLine) == transactionHash:
            interTxArray = interTxLine.split(",")
            call_type = interTxArray[3].split("_")[0]
            msg_sender = interTxArray[4]
            msg_to = interTxArray[5]
            msg_value = int(interTxArray[8])
            isError = interTxArray[10]
            if isError == "None" and msg_value>0 and (call_type=="call" or call_type=="suicide" or call_type=="create"):
                transfer(msg_sender, msg_to, msg_value)
            if isError == "None" and call_type=="suicide" and blockNumber < 19426587: # before dencun
                suicided_contracts.add(msg_sender)
            interTxLine = interTxCSV.readline().strip()    

        for addr in suicided_contracts:
            if addr in balance_of:
                sub(addr, balance_of[addr])

        # Third step: calc the TX fee
        gasPrice              = int(blockTxArray[10])
        gasUsed               = int(blockTxArray[11])
        eip2718type           = to_int(blockTxArray[14])
        baseFeePerGas         = to_int(blockTxArray[15])
        maxFeePerGas          = to_int(blockTxArray[16])
        maxPriorityFeePerGas  = to_int(blockTxArray[17])

        if eip2718type == 3:
            blobHashes        = blockTxArray[18].split(":")
            blobBaseFeePerGas = int(blockTxArray[19])
            blobGasUsed       = int(blockTxArray[20])
            sub(tx_sender, blobBaseFeePerGas*blobGasUsed)

        # transfer then burn if EIP1559
        if gasPrice>0:
            transfer(tx_sender, current_miner, gasPrice*gasUsed)
        if baseFeePerGas != None:
            sub(current_miner, baseFeePerGas*gasUsed)

        blockTxLine = blockTxCSV.readline().strip()    


    blockTxCSV.close()    
    interTxCSV.close()
    blockInfoCsv.close()


    while rewardLine != "":
        rewardArr = rewardLine.split(",")
        to = rewardArr[-2]
        value = int(rewardArr[-1])
        add(to, value)
        rewardLine = rewardCSV.readline().strip()
    
    rewardCSV.close()
