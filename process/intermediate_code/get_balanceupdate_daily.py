import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import datadir,sort_by_blocknum,to_int,to_str, dao_hardfork_beneficiary, dao_hardfork_accounts, date_to_day_time, date_to_last_block, begin_end, prune_files, read_first_line_gt_block
import glob
import functools
import time
import mmap
import subprocess

# ==================== 余额快照 ====================
# 全量地址余额不驻内存, 拆成两层:
#   - 快照: 按地址排序的定长二进制文件 (20 字节地址 + 16 字节大端余额),
#     只读不可变, mmap + 二分查找, 不占堆内存;
#   - overlay: 当天的变更放内存 dict, 查询先 overlay 后快照。
# 收盘时 overlay 排序后与旧快照两路归并写出新快照 (.tmp + rename 原子替换),
# 未变更区间整块字节拷贝。挂在中途旧快照完好, 删掉重跑即可。
# 快照只是缓存, 删掉了随时可以由 balanceupdate_daily/ 日更文件重建 (见下方自动构建)。

RECORD_SIZE = 36  # 20 bytes address + 16 bytes big-endian balance
ADDR_SIZE = 20
BAL_SIZE = 16
COPY_CHUNK = 8 * 1024 * 1024

DAILY_DIR = "intermediate_data/balanceupdate_daily/"
SNAPSHOT_DIR = "intermediate_data/balance_snapshot/"

# 距上一份快照满这么多天, 在日界写一份新快照 (默认每天一份, 约 11GB 顺序写, 一分钟级)
SNAPSHOT_INTERVAL_DAYS = 1
# overlay 记录数上限, 超过就在日界强制落一份快照, 保护内存 (全量重跑时靠它限峰)
OVERLAY_MAX_RECORDS = 20_000_000


def addr_to_key(addr):
    key = bytes.fromhex(addr[2:])
    assert len(key) == ADDR_SIZE, "bad address: " + addr
    return key


def key_to_addr(key):
    return "0x" + key.hex()


class SnapshotReader:
    """只读快照: mmap + 二分查找。"""

    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        self.nrec = len(self.mm) // RECORD_SIZE

    def lower_bound(self, key):
        """返回第一个地址 >= key 的记录下标 (== nrec 表示全部小于 key)。"""
        lo, hi = 0, self.nrec
        mm = self.mm
        while lo < hi:
            mid = (lo + hi) // 2
            rec = mm[mid * RECORD_SIZE: mid * RECORD_SIZE + ADDR_SIZE]
            if rec < key:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def balance_at(self, idx):
        off = idx * RECORD_SIZE + ADDR_SIZE
        return int.from_bytes(self.mm[off: off + BAL_SIZE], "big")

    def addr_at(self, idx):
        off = idx * RECORD_SIZE
        return self.mm[off: off + ADDR_SIZE]

    def get(self, key):
        idx = self.lower_bound(key)
        if idx < self.nrec and self.addr_at(idx) == key:
            return self.balance_at(idx)
        return None

    def close(self):
        self.mm.close()
        self.f.close()


def _copy_records(fin, out, begin, end):
    """把快照中 [begin, end) 的记录原样大块拷贝到 out。"""
    fin.seek(begin * RECORD_SIZE)
    remaining = (end - begin) * RECORD_SIZE
    while remaining > 0:
        chunk = fin.read(min(COPY_CHUNK, remaining))
        if not chunk:
            break
        out.write(chunk)
        remaining -= len(chunk)


def write_snapshot(base, overlay, final_path):
    """base(SnapshotReader 或 None) 与 overlay(dict: key->balance) 归并,
    原子写出新快照到 final_path。调用方负责之后关闭旧 base。"""
    items = sorted(overlay.items())
    tmp_path = final_path + ".tmp"
    with open(tmp_path, "wb") as out:
        if base is None or base.nrec == 0:
            for key, bal in items:
                out.write(key + bal.to_bytes(BAL_SIZE, "big"))
        else:
            fin = open(base.path, "rb")
            prev = 0
            for key, bal in items:
                idx = base.lower_bound(key)
                _copy_records(fin, out, prev, idx)
                out.write(key + bal.to_bytes(BAL_SIZE, "big"))
                if idx < base.nrec and base.addr_at(idx) == key:
                    prev = idx + 1  # 覆盖旧值
                else:
                    prev = idx  # 新地址, 插入
            _copy_records(fin, out, prev, base.nrec)
            fin.close()
    os.replace(tmp_path, final_path)


def latest_snapshot():
    """返回 (date_str, path), 没有快照返回 (None, None)。"""
    files = glob.glob(SNAPSHOT_DIR + "*.bin")
    if not files:
        return None, None
    files.sort()
    return files[-1].split("/")[-1].split(".")[0], files[-1]


def prune_old_snapshots(keep=2):
    """只保留最近几份快照 (最新一份在用, 前一份留给回滚), 其余删除。"""
    files = glob.glob(SNAPSHOT_DIR + "*.bin")
    files.sort()
    for f in files[:-keep]:
        print("prune snapshot", f)
        os.remove(f)


class BalanceState:
    """余额状态: 只读快照 base + 内存 overlay。

    get 先查 overlay 再二分查快照; add/sub 只写 overlay。
    touched 是当天被动过的地址 (保持插入序), 用于写日更文件。"""

    def __init__(self, snapshot_path=None):
        self.base = SnapshotReader(snapshot_path) if snapshot_path else None
        self.overlay = {}
        self.touched = {}

    def get(self, addr):
        key = addr_to_key(addr)
        if key in self.overlay:
            return self.overlay[key]
        if self.base is not None:
            return self.base.get(key)
        return None

    def _set(self, addr, value):
        key = addr_to_key(addr)
        self.overlay[key] = value
        self.touched[key] = None

    def add(self, addr, value):
        cur = self.get(addr)
        self._set(addr, (cur or 0) + value)

    def sub(self, addr, value):
        cur = self.get(addr)
        if cur is None or cur < value:
            print(addr, "err!")
            if cur is not None:
                print(cur, value)
            exit()
        self._set(addr, cur - value)

    def flush_day(self, day):
        """写日更 diff 文件 (tmp+rename), 之后清 touched。"""
        final_path = DAILY_DIR + day + ".txt"
        with open(final_path + ".tmp", "w") as f:
            for key in self.touched:
                f.write(key_to_addr(key) + "," + str(self.overlay[key]) + "\n")
        os.replace(final_path + ".tmp", final_path)
        self.touched = {}

    def maybe_write_snapshot(self, day, day_time, last_snapshot_daytime):
        """满足条件时在日界落一份新快照并切换 base, 返回是否写了。"""
        recent = day_time >= time.time() - 3 * 86400
        due = last_snapshot_daytime is None or \
            day_time - last_snapshot_daytime >= SNAPSHOT_INTERVAL_DAYS * 86400
        if len(self.overlay) > OVERLAY_MAX_RECORDS or (recent and due):
            path = SNAPSHOT_DIR + day + ".bin"
            print("write snapshot", path, "overlay", len(self.overlay))
            write_snapshot(self.base, self.overlay, path)
            if self.base is not None:
                self.base.close()
            self.base = SnapshotReader(path)
            self.overlay = {}
            prune_old_snapshots(keep=2)
            return True
        return False


def build_snapshot_from_history(last_date):
    """没有快照时自动从历史日更文件构建一份 (一次性迁移/快照被删后的重建)。

    日更文件按日期从新到旧拼接 (同一地址最新的余额在最前),
    用 GNU sort 稳定模式按地址去重保留第一次出现 (= 最新值),
    再转定长二进制。全程流式 + 外部排序, 内存 O(1)。"""
    files = glob.glob(DAILY_DIR + "*.txt")
    files.sort()
    final_path = SNAPSHOT_DIR + last_date + ".bin"
    tmp_concat = SNAPSHOT_DIR + "build_concat.tmp"
    tmp_sorted = SNAPSHOT_DIR + "build_sorted.tmp"

    print("build snapshot from", len(files), "daily files (one-off, slow) ...")
    with open(tmp_concat, "wb") as out:
        for path in reversed(files):
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(COPY_CHUNK)
                    if not chunk:
                        break
                    out.write(chunk)
        if os.path.exists("source_data/genesis.csv"):
            with open("source_data/genesis.csv", "rb") as f:
                while True:
                    chunk = f.read(COPY_CHUNK)
                    if not chunk:
                        break
                    out.write(chunk)

    subprocess.run(
        ["sort", "-s", "-u", "-t,", "-k1,1", "-S", "1G", "-T", SNAPSHOT_DIR,
         "-o", tmp_sorted, tmp_concat],
        check=True, env={**os.environ, "LC_ALL": "C"})

    n = 0
    prev_key = None
    with open(tmp_sorted) as fin, open(final_path + ".tmp", "wb") as out:
        for line in fin:
            arr = line.split(",")
            key = addr_to_key(arr[0])
            if prev_key is not None:
                assert key > prev_key, "snapshot not sorted at " + arr[0]
            prev_key = key
            out.write(key + int(arr[1]).to_bytes(BAL_SIZE, "big"))
            n += 1
    os.replace(final_path + ".tmp", final_path)

    os.remove(tmp_concat)
    os.remove(tmp_sorted)
    print("snapshot built:", final_path, n, "records")
    return final_path


# ==================== 主流程 ====================

output_dir = DAILY_DIR
for d in (output_dir, SNAPSHOT_DIR):
    try:
        os.mkdir(d)
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

last_write_daytime = 0

only_update = False
files = os.listdir(output_dir)
files.sort()
only_update = len(files) > 0

snapshot_date, snapshot_path = latest_snapshot()

if only_update:
    last_date = files[-1].split(".")[0]

    # rollback 可能删掉了尾部日更文件, 比最后日更文件新的快照一并作废
    if snapshot_date is not None and snapshot_date > last_date:
        for f in glob.glob(SNAPSHOT_DIR + "*.bin"):
            if f.split("/")[-1].split(".")[0] > last_date:
                print("discard snapshot", f)
                os.remove(f)
        snapshot_date, snapshot_path = latest_snapshot()

    # 没有快照 (首次迁移, 或快照被删) 就从历史日更文件自动重建一份
    if snapshot_path is None:
        snapshot_path = build_snapshot_from_history(last_date)
        snapshot_date = last_date

    last_write_daytime = date_to_day_time(last_date) + 86400
    last_block = date_to_last_block(last_date)
    print("only update from", last_block, "snapshot", snapshot_date)
    BlockTransactionCsvs = prune_files(BlockTransactionCsvs, last_block)
    IneternalTransactionCsvs = prune_files(IneternalTransactionCsvs, last_block)
    MinerRewardCsvs = prune_files(MinerRewardCsvs, last_block)
    WithdrawalCsvs = prune_files(WithdrawalCsvs, last_block)

    state = BalanceState(snapshot_path)
    last_snapshot_daytime = date_to_day_time(snapshot_date)

    # 只需回放比快照新的日更文件 (间隔内的几天)
    for file in files:
        date = file.split(".")[0]
        if date <= snapshot_date:
            continue
        path = output_dir + file
        n = 0
        with open(path) as f:
            for line in f:
                arr = line.strip().split(",")
                state.overlay[addr_to_key(arr[0])] = int(arr[1])
                n += 1
        print("read", path, "update", n, len(state.overlay))

else:
    state = BalanceState()
    last_snapshot_daytime = None
    genesis_lines = open("source_data/genesis.csv").read().split("\n")
    for line in genesis_lines[:-1]:
        t = line.split(",")
        addr = t[0]
        balance = int(t[1])
        state._set(addr, balance)


def block_number(line):
    number = int(line.split(",")[0])
    return number

def internal_tx_hash(line):
    txhash = line.split(",")[2]
    return txhash

def add(to, value):
    state.add(to, value)


def sub(sender, value):
    state.sub(sender, value)


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

    if only_update:
        blockInfoLine = read_first_line_gt_block(blockInfoCsv, last_block)
        blockTxLine = read_first_line_gt_block(blockTxCSV, last_block)
        interTxLine = read_first_line_gt_block(interTxCSV, last_block)
        rewardLine = read_first_line_gt_block(rewardCSV, last_block)
    else:
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
                    cur = state.get(addr)
                    if cur is not None:
                        transfer(addr, dao_hardfork_beneficiary, cur)

        while rewardLine != "" and block_number(rewardLine) < blockNumber:
            rewardArr = rewardLine.split(",")
            reward_to = rewardArr[-2]
            reward_value = int(rewardArr[-1])
            add(reward_to, reward_value)
            rewardLine = rewardCSV.readline().strip()



        if timestamp >= last_write_daytime + 86400:
            last_write_daytime = int(timestamp/86400) * 86400
            day = time.strftime('%Y-%m-%d', time.gmtime(last_write_daytime-1))
            
            print(day, last_write_daytime, len(state.touched))
            state.flush_day(day)
            if state.maybe_write_snapshot(day, last_write_daytime, last_snapshot_daytime):
                last_snapshot_daytime = last_write_daytime
        
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
            cur = state.get(addr)
            if cur is not None:
                sub(addr, cur)

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
