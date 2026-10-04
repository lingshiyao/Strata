"""T1-1 阶段 1-C 决定性实验：离线模拟自适应专家缓存。

引擎的缓存有两层（源码核实）：
  1. 静态 profile 层：前 N 个排名槽位预填，容量 N。
  2. 自适应层（generate.cpp:5703-5756）：每 adapt_every 轮，把「未驻留且衰减使用率 >= 2.0」的候选
     与该层「驻留中路由最少」的受害者配对，当 cand.usage >= vict.usage + 1.5 时交换，最多 adapt_swaps 次；
     之后所有 usage *= 0.7。
usage 的累加见 expert_source.cpp:1610-1612（每个路由 id +1）。

目的：判断「换一个更好的静态 profile」在**自适应层存在**的前提下是否还有价值。
若 arm D (oracle+adapt) 约等于 arm B (v1+adapt)，则 T1 无价值。
"""
import struct
import sys
from collections import defaultdict
from pathlib import Path

PROBE = Path(r"D:/Strata/.workbuddy-ai/t1_probe")
MAGIC = b"STRP"
N_LAYER, N_EXPERT = 48, 256


def read_profile_ranked(path):
    blob = Path(path).read_bytes()
    assert blob[:4] == MAGIC
    ver, nl, ne, slots, n = struct.unpack_from("<5I", blob, 4)
    return [struct.unpack_from("<HH", blob, 24 + 4 * i) for i in range(n)]


def read_trace(path):
    blob = Path(path).read_bytes()
    off, per_layer = 0, defaultdict(list)
    while off + 8 <= len(blob):
        layer, k = struct.unpack_from("<ii", blob, off)
        off += 8
        if k < 0 or k > 64 or off + 8 * k > len(blob):
            break
        ids = struct.unpack_from("<%di" % k, blob, off)
        off += 8 * k
        per_layer[layer].append(ids)
    return per_layer


def build_oracle_ranked(per_layer, upto):
    freq = defaultdict(int)
    for L, seq in per_layer.items():
        for ids in seq[:upto]:
            for e in ids:
                freq[(L, e)] += 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    seen = set(ranked)
    for L in range(N_LAYER):
        for e in range(N_EXPERT):
            if (L, e) not in seen:
                ranked.append(((L, e), 0))
    return [p for p, _ in ranked]


def simulate(per_layer, ranked, N, adapt=True, adapt_every=13, adapt_swaps=96,
             cand_min=2.0, gain_min=1.5, decay=0.7, upto=None, start_empty=False):
    """返回 (hits, lookups, swaps)。

    start_empty=True 模拟「不给 profile」：缓存从空开始，miss 时若还有空槽则 admit（首次使用即入住）。
    **口径必须与引擎一致**：引擎报告的命中率分子只有 cache_hits，cache_admitted 只进分母
    （generate.cpp:5221-5222），即「查到时就已常驻」的严格命中率。所以 admit 在这里**不计命中**。
    槽位分配是**全局一个计数器**（默认策略：arrival order from one shared counter）。
    """
    T = max(len(s) for s in per_layer.values())
    T = min(T, upto) if upto else T

    resident = [bytearray(N_EXPERT) for _ in range(N_LAYER)]
    free = N
    if not start_empty:
        for i, (L, e) in enumerate(ranked[:N]):
            resident[L][e] = 1

    usage = [[0.0] * N_EXPERT for _ in range(N_LAYER)]
    hits = lookups = 0
    swaps_total = 0

    for t in range(T):
        for L in range(N_LAYER):
            seq = per_layer[L]
            if t >= len(seq):
                continue
            res = resident[L]
            us = usage[L]
            for e in seq[t]:
                us[e] += 1.0
                lookups += 1
                if res[e]:
                    hits += 1
                elif start_empty and free > 0:
                    free -= 1
                    res[e] = 1                    # 首次入住：进分母不进分子（与引擎口径一致）
        if adapt and (t + 1) % adapt_every == 0:
            swaps = []
            for L in range(N_LAYER):
                res = resident[L]
                us = usage[L]
                cand = [(us[e], e) for e in range(N_EXPERT) if not res[e] and us[e] >= cand_min]
                vict = sorted((us[e], e) for e in range(N_EXPERT) if res[e])
                if not cand or not vict:
                    continue
                cand.sort(key=lambda x: -x[0])
                nc = min(len(cand), len(vict))
                for i in range(nc):
                    if cand[i][0] < vict[i][0] + gain_min:
                        break
                    swaps.append((cand[i][0] - vict[i][0], L, cand[i][1], vict[i][1]))
            swaps.sort(key=lambda x: -x[0])
            if len(swaps) > adapt_swaps:
                swaps = swaps[:adapt_swaps]
            for _, L, e_in, e_out in swaps:
                resident[L][e_in] = 1
                resident[L][e_out] = 0
            swaps_total += len(swaps)
            for L in range(N_LAYER):
                us = usage[L]
                for e in range(N_EXPERT):
                    us[e] *= decay
    return hits, lookups, swaps_total


def main():
    trace = Path(sys.argv[1]) if len(sys.argv) > 1 else PROBE / "trace_decode.bin"
    per_layer = read_trace(trace)
    T = max(len(s) for s in per_layer.values())
    print(f"trace {trace.name}: {N_LAYER} 层 × {T} 位置")

    v1 = read_profile_ranked(r"D:/Strata/data/expert-profile-coder.bin")
    half = T // 2
    orc_in = build_oracle_ranked(per_layer, T)          # in-sample oracle
    orc_out = build_oracle_ranked(per_layer, half)      # 仅用前半段训练（held-out 用）

    print(f"v1 排名 {len(v1)} 对; oracle(in-sample) {len(orc_in)} 对; oracle(前半段训练) {len(orc_out)} 对")

    for N in (3629, 4161):
        print(f"\n########## N = {N} 槽位 ##########")
        # 静态（无自适应）
        arms = [("v1  静态", v1, False), ("v1  +自适应", v1, True),
                ("oracle(in-sample) 静态", orc_in, False), ("oracle(in-sample) +自适应", orc_in, True),
                ("oracle(前半段) +自适应", orc_out, True)]
        base = None
        for name, ranked, ad in arms:
            h, lk, sw = simulate(per_layer, ranked, N, adapt=ad)
            hr = h / lk if lk else 0
            print(f"  {name:28s} hit={100*hr:6.2f}%   ({h}/{lk})  自适应交换 {sw}")
        # 随机排名对照
        import random
        random.seed(7)
        rnd = [(L, e) for L in range(N_LAYER) for e in range(N_EXPERT)]
        random.shuffle(rnd)
        h, lk, sw = simulate(per_layer, rnd, N, adapt=True)
        print(f"  {'随机排名 +自适应':28s} hit={100*h/lk:6.2f}%   ({h}/{lk})  自适应交换 {sw}")
        h, lk, sw = simulate(per_layer, rnd, N, adapt=False)
        print(f"  {'随机排名 静态':28s} hit={100*h/lk:6.2f}%   ({h}/{lk})")

    # 自适应频率敏感性（用 v1 与 oracle）
    print("\n########## 自适应频率敏感性 (N=3629) ##########")
    for ae in (4, 8, 13, 26, 52):
        h1, lk, s1 = simulate(per_layer, v1, 3629, adapt=True, adapt_every=ae)
        h2, _, s2 = simulate(per_layer, orc_in, 3629, adapt=True, adapt_every=ae)
        print(f"  adapt_every={ae:3d}  v1={100*h1/lk:6.2f}% (交换{s1:6d})   "
              f"oracle={100*h2/lk:6.2f}% (交换{s2:6d})   差={100*(h2-h1)/lk:+6.2f}pt")

    # 会话长度扫描：短请求自适应来不及收敛，profile 是否重要？
    print("\n########## 会话长度扫描 (N=3629, adapt_every=13) ##########")
    print("  「不给profile」= 缓存从空开始，首次使用即入住并算命中，再叠加自适应")
    print(f"  {'T(位置)':>8} {'v1静态':>9} {'v1+自适应':>10} {'不给profile':>12} "
          f"{'随机+自适应':>12} {'oracle+自适应':>14} {'oracle-v1':>10}")
    import random
    random.seed(7)
    rnd = [(L, e) for L in range(N_LAYER) for e in range(N_EXPERT)]
    random.shuffle(rnd)
    for Tt in (50, 100, 200, 385, 600, 1000, 1500, 2046):
        h_s, lk_s, _ = simulate(per_layer, v1, 3629, adapt=False, upto=Tt)
        h1, lk, _ = simulate(per_layer, v1, 3629, adapt=True, upto=Tt)
        h0, _, _ = simulate(per_layer, [], 3629, adapt=True, upto=Tt, start_empty=True)
        h3, _, _ = simulate(per_layer, rnd, 3629, adapt=True, upto=Tt)
        h2, _, _ = simulate(per_layer, orc_out, 3629, adapt=True, upto=Tt)
        print(f"  {Tt:8d} {100*h_s/lk_s:8.2f}% {100*h1/lk:9.2f}% {100*h0/lk:11.2f}% "
              f"{100*h3/lk:11.2f}% {100*h2/lk:13.2f}% {100*(h2-h1)/lk:+9.2f}pt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
