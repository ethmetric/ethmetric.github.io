"""时点定义 (point-in-time) 的 EOA 统计对比工具。

现版 eoacnt_100eth / eoasum_100eth / eoasum_top100_100eth 用的是"终局定义":
只要一个地址在任何时刻被确认是合约, 就从所有历史天除名, 所以要每天全量重算。

本脚本用"时点定义"重算同一组指标: 地址只在它被创建为合约的那天起才被排除,
部署之前 (例如 CREATE2 反事实地址预先收到 ETH 的阶段) 仍算 EOA。
历史天一旦写下就不变, 因此这个口径天然支持增量更新。

输出写到新文件, 与现有图表数据对比, 不覆盖:
  chart_data/eoacnt_100eth_pit.txt
  chart_data/eoasum_100eth_pit.txt
  chart_data/eoasum_top100_100eth_pit.txt
结尾打印两个口径的逐日差异汇总。

在 process/ 目录下运行:  python3 chart_code/eoa_100eth_pit.py
"""
import glob

holding100eth_daily_files = glob.glob("intermediate_data/holding100eth_daily/*")
createdcontract_daily_files = glob.glob("intermediate_data/createdcontract_daily/*")

holding100eth_daily_files.sort()
createdcontract_daily_files.sort()

# 按天整理合约创建表: day -> [addr, ...]
created_by_day = {}
for file in createdcontract_daily_files:
    day = file.split("/")[-1].split(".")[0]
    created_by_day[day] = [line.strip() for line in open(file).readlines()]
created_days = sorted(created_by_day.keys())

contracts = set()       # 截至当前天已创建的合约 (时点口径)
created_idx = 0

f_cnt = open("chart_data/eoacnt_100eth_pit.txt", "w")
f_sum = open("chart_data/eoasum_100eth_pit.txt", "w")
f_top = open("chart_data/eoasum_top100_100eth_pit.txt", "w")

for file in holding100eth_daily_files:
    day = file.split("/")[-1].split(".")[0]

    # 只把当前天及之前创建的合约纳入排除集
    while created_idx < len(created_days) and created_days[created_idx] <= day:
        contracts.update(created_by_day[created_days[created_idx]])
        created_idx += 1

    print("read", file, "contracts so far", len(contracts))
    lines = open(file).read().split("\n")[:-1]
    cnt = 0
    eoasum = 0
    balances = []
    for line in lines:
        arr = line.strip().split(",")
        addr = arr[0]
        if addr in contracts:
            continue
        balance = int(arr[2])
        cnt += 1
        eoasum += balance
        balances.append(balance)
    balances.sort(reverse=True)
    topsum = sum(balances[:100])

    f_cnt.write(day + "," + str(cnt) + "\n")
    f_sum.write(day + "," + str(eoasum / (10**18)) + "\n")
    f_top.write(day + "," + str(topsum / (10**18)) + "\n")

f_cnt.close()
f_sum.close()
f_top.close()

# ==================== 与现有 (终局定义) 数据对比 ====================

def load(path):
    ret = {}
    for line in open(path).read().split("\n")[:-1]:
        arr = line.split(",")
        ret[arr[0]] = float(arr[1])
    return ret

for old_path, new_path in (
    ("chart_data/eoacnt_100eth.txt", "chart_data/eoacnt_100eth_pit.txt"),
    ("chart_data/eoasum_100eth.txt", "chart_data/eoasum_100eth_pit.txt"),
    ("chart_data/eoasum_top100_100eth.txt", "chart_data/eoasum_top100_100eth_pit.txt"),
):
    old = load(old_path)
    new = load(new_path)
    days = sorted(set(old) & set(new))
    diffs = [(d, new[d] - old[d], old[d]) for d in days if abs(new[d] - old[d]) > 1e-9]
    print("====", old_path)
    print("days compared:", len(days), " days differ:", len(diffs))
    if diffs:
        worst = max(diffs, key=lambda x: abs(x[1] / x[2]) if x[2] else abs(x[1]))
        print("worst day:", worst[0], "old:", worst[2], "new:", worst[2] + worst[1],
              " rel diff:", round(abs(worst[1] / worst[2]) * 100, 6) if worst[2] else "n/a", "%")
        latest = diffs[-1]
        print("latest differ day:", latest[0], "old:", latest[2], "new:", latest[2] + latest[1])
