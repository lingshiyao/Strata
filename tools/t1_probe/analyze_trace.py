"""T1-1 阶段 1-B / 1-C：离线命中率分析（纯计算，不加载模型，不碰基线）。

trace 语义（已在源码核实）：
  drive_pool / drive_pool_multi 收到的是门铃发布的**该层完整路由决策**（全部 k 个 id），
  因此 trace 记录 = 全部路由查找，不是仅未命中。
缓存策略实测为 "PROFILE, ranked by routing frequency, no eviction"（静态、无淘汰），
  故「槽位 < N 即命中」的离线代理是**精确**的，不是近似。

用法: python analyze_trace.py [trace.bin]
"""
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

PROBE = Path(r"D:/Strata/.workbuddy-ai/t1_probe")
V1 = Path(r"D:/Strata/data/expert-profile-coder.bin")
SECTIONS = PROBE / "sections.json"
MAGIC = b"STRP"
SLOT_NS = {"baseline(256k,reserve700)": 3629, "ultra(reserve380)": 3793,
           "tuned(reserve300)": 3835, "this-run(auto)": 4161}


def read_profile_ranked(path):
    blob = Path(path).read_bytes()
    assert blob[:4] == MAGIC, f"{path}: not a Strata profile"
    ver, nl, ne, slots, n = struct.unpack_from("<5I", blob, 4)
    ranked = [struct.unpack_from("<HH", blob, 24 + 4 * i) for i in range(n)]
    return dict(nl=nl, ne=ne, slots=slots, n=n, ranked=ranked,
                slot_of={p: i for i, p in enumerate(ranked)})


def read_trace(path):
    blob = Path(path).read_bytes()
    off, recs = 0, []
    while off + 8 <= len(blob):
        layer, k = struct.unpack_from("<ii", blob, off)
        off += 8
        if k < 0 or k > 64 or off + 8 * k > len(blob):
            print(f"  !! 记录异常 layer={layer} k={k} @off={off}，停止")
            break
        ids = struct.unpack_from("<%di" % k, blob, off)
        off += 8 * k
        recs.append((layer, ids))
    return recs


def by_layer(recs):
    d = defaultdict(list)
    for layer, ids in recs:
        d[layer].append(ids)
    return d


def hitrate(freq, slot_of, N):
    tot = sum(freq.values())
    if tot == 0:
        return 0.0, 0
    hit = sum(c for (L, e), c in freq.items() if slot_of.get((L, e), 10 ** 9) < N)
    return hit / tot, tot


def build_oracle(freqs):
    agg = defaultdict(int)
    for f in freqs:
        for k, v in f.items():
            agg[k] += v
    ranked = sorted(agg.items(), key=lambda kv: (-kv[1], kv[0]))
    return {p: i for i, (p, _) in enumerate(ranked)}, len(ranked)


def main():
    trace_path = Path(sys.argv[1]) if len(sys.argv) > 1 else PROBE / "trace_decode.bin"
    if not trace_path.exists():
        print(f"!! 没有 trace: {trace_path}")
        return 1
    v1 = read_profile_ranked(V1)
    recs = read_trace(trace_path)
    bl = by_layer(recs)
    lens = sorted(len(v) for v in bl.values())
    k0 = len(recs[0][1]) if recs else 0
    lookups = sum(len(v) * len(v[0]) for v in bl.values())

    print(f"trace  : {trace_path.name}  {len(recs)} 条记录, {len(bl)} 层, "
          f"每层位置 {lens[0]}..{lens[-1]}, k={k0}, 总查找 {lookups}")
    print(f"v1     : {v1['nl']}x{v1['ne']}  n={v1['n']}")

    freq_all = defaultdict(int)
    for layer, ids in recs:
        for e in ids:
            freq_all[(layer, e)] += 1
    print(f"不同 (layer,expert) 对: {len(freq_all)} / {v1['n']}  "
          f"({100*len(freq_all)/v1['n']:.1f}% 的 pair 在 trace 中出现过)")

    # ---- 指标 1
    print("\n=== 指标 1: v1 profile 在本 trace 上的命中率 ===")
    for name, N in SLOT_NS.items():
        hr, tot = hitrate(freq_all, v1["slot_of"], N)
        print(f"  N={N:5d} ({name:26s})  hit={100*hr:6.2f}%")

    # ---- 指标 2
    print("\n=== 指标 2: hit(N) 曲线：v1 vs trace-oracle（in-sample，上界）===")
    oracle_all, n_or = build_oracle([freq_all])
    print(f"  oracle 覆盖对数 {n_or} / {v1['n']}")
    print(f"  {'N':>6} {'v1':>9} {'oracle':>9} {'差值':>9}")
    for N in (500, 1000, 2000, 3194, 3629, 3793, 3835, 4161, 6000, 8000, 12288):
        h1, _ = hitrate(freq_all, v1["slot_of"], N)
        h2, _ = hitrate(freq_all, oracle_all, N)
        print(f"  {N:6d} {100*h1:8.2f}% {100*h2:8.2f}% {100*(h2-h1):+8.2f}pt")

    # ---- 指标 3: 前后半段泛化
    print("\n=== 指标 3: 前后半段泛化（train=位置前半, test=位置后半, N=3629）===")
    T = max(len(v) for v in bl.values())
    half = T // 2
    ftr, fte = defaultdict(int), defaultdict(int)
    for layer, seq in bl.items():
        for t, ids in enumerate(seq):
            tgt = ftr if t < half else fte
            for e in ids:
                tgt[(layer, e)] += 1
    orc_tr, _ = build_oracle([ftr])
    h1, tot_te = hitrate(fte, v1["slot_of"], 3629)
    h2, _ = hitrate(fte, orc_tr, 3629)
    print(f"  test lookups = {tot_te}")
    print(f"  v1           = {100*h1:6.2f}%")
    print(f"  oracle(train)= {100*h2:6.2f}%")
    print(f"  >>> 净增益    = {100*(h2-h1):+6.2f} pt")

    # ---- 指标 4: K 折 leave-one-chunk-out（连续位置分块）
    K = 5
    print(f"\n=== 指标 4: {K} 折 leave-one-chunk-out（按连续位置分块, N=3629）===")
    chunk_freq = [defaultdict(int) for _ in range(K)]
    bounds = [(T * i) // K for i in range(K + 1)]
    for layer, seq in bl.items():
        for t, ids in enumerate(seq):
            ci = min(K - 1, t * K // T)
            for e in ids:
                chunk_freq[ci][(layer, e)] += 1
    print(f"  块边界 {bounds}")
    print(f"  {'held-out 块':<16} {'lookups':>8} {'v1':>9} {'oracle':>9} {'增益':>9}")
    gains = []
    for i in range(K):
        te = chunk_freq[i]
        tot = sum(te.values())
        if tot == 0:
            continue
        tr = [chunk_freq[j] for j in range(K) if j != i]
        orc, _ = build_oracle(tr)
        h1, _ = hitrate(te, v1["slot_of"], 3629)
        h2, _ = hitrate(te, orc, 3629)
        gains.append(h2 - h1)
        print(f"  块{i} [{bounds[i]:5d},{bounds[i+1]:5d}) {tot:8d} {100*h1:8.2f}% {100*h2:8.2f}% "
              f"{100*(h2-h1):+8.2f}pt")
    if gains:
        print(f"\n  平均净增益 {100*sum(gains)/len(gains):+.2f} pt   最小 {100*min(gains):+.2f}pt  "
              f"最大 {100*max(gains):+.2f}pt")

    # ---- 指标 5: 集中度
    print("\n=== 指标 5: 查找集中度（按 v1 排名累计覆盖）===")
    tot = sum(freq_all.values())
    ordered = sorted(freq_all.items(), key=lambda kv: v1["slot_of"].get(kv[0], 10 ** 9))
    cum, mi, marks = 0, 0, [0.25, 0.5, 0.6, 0.7, 0.8, 0.9]
    for i, (pair, c) in enumerate(ordered, 1):
        cum += c
        while mi < len(marks) and cum / tot >= marks[mi]:
            print(f"  {100*marks[mi]:.0f}% 查找覆盖 <- 前 {i:5d} 槽位 ({100*i/v1['n']:5.1f}% of pairs)")
            mi += 1
    for N in (3629, 4161):
        c = sum(x for p, x in ordered[:N])
        print(f"  v1 前 {N} 槽位覆盖 {100*c/tot:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
