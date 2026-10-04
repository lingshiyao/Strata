"""T1-1 前置取证：coder profile 到底是「编码专用」还是「通用排名重新索引」？

零成本、纯离线、不加载模型、不写任何基线资产。

判定：把 base profile(48x512) 每层排名里 expert<256 的项按原序取出，
      与 coder profile(48x256) 的每层排名逐项比较。
      完全一致 -> coder profile 不含任何编码信息（假设 H1 成立）。
"""
import struct
import sys
from pathlib import Path

MAGIC = b"STRP"
BASE = Path(r"D:/Strata/data/expert-profile.bin")
CODER = Path(r"D:/Strata/data/expert-profile-coder.bin")


def read_profile(path):
    blob = path.read_bytes()
    assert blob[:4] == MAGIC, f"{path}: not a Strata profile"
    ver, nl, ne, slots, n = struct.unpack_from("<5I", blob, 4)
    ranked = [struct.unpack_from("<HH", blob, 24 + 4 * i) for i in range(n)]
    rev = [struct.unpack_from("<%di" % ne, blob, 24 + 4 * n + 4 * ne * L)
           for L in range(nl)]
    return dict(path=path, ver=ver, nl=nl, ne=ne, slots=slots, n=n, ranked=ranked, rev=rev)


def main():
    b = read_profile(BASE)
    c = read_profile(CODER)
    for tag, p in (("base ", b), ("coder", c)):
        print(f"{tag}: ver={p['ver']} {p['nl']}x{p['ne']} slots={p['slots']} n={p['n']} "
              f"bytes={p['path'].stat().st_size}")

    if b["ne"] % c["ne"] != 0:
        print("!! expert counts not divisible; cannot test the reindex hypothesis")
        return 2
    ratio = b["ne"] // c["ne"]
    print(f"\nbase experts per layer {b['ne']}, coder {c['ne']}  ->  ratio {ratio}")

    # coder 排名按层分组
    coder_by_layer = [[] for _ in range(c["nl"])]
    for L, e in c["ranked"]:
        coder_by_layer[L].append(e)

    # base 排名按层分组
    base_by_layer = [[] for _ in range(b["nl"])]
    for L, e in b["ranked"]:
        base_by_layer[L].append(e)

    # 反查表自洽性
    print("\n--- 反查表自洽性 (slot_of(layer,expert) 应等于其在排名中的位置) ---")
    for tag, p in (("base ", b), ("coder", c)):
        bad = 0
        for L in range(p["nl"]):
            for e in range(p["ne"]):
                if p["rev"][L][e] < 0:
                    continue
                if p["rev"][L][e] >= p["n"]:
                    bad += 1
                    continue
                if p["ranked"][p["rev"][L][e]] != (L, e):
                    bad += 1
        print(f"  {tag}: 反查表不一致项 = {bad}")

    print("\n--- 假设检验 A: coder = base 每层保留 e<256、保序 ---")
    total_mismatch = 0
    for L in range(c["nl"]):
        filtered = [e for e in base_by_layer[L] if e < c["ne"]]
        got = coder_by_layer[L]
        if filtered != got:
            n_diff = sum(1 for x, y in zip(filtered, got) if x != y) + abs(len(filtered) - len(got))
            total_mismatch += n_diff
            if L < 5 or n_diff > 0 and L < 50:
                print(f"  layer {L:2d}: base(e<{c['ne']}) n={len(filtered)}, coder n={len(got)}, "
                      f"first diffs = {[(i, filtered[i] if i < len(filtered) else None, got[i] if i < len(got) else None) for i in range(min(len(filtered), len(got), 40)) if filtered[i] != got[i]][:5]}")
    print(f"  >>> 假设 A 不一致总数 = {total_mismatch}")

    # 假设检验 B: coder 是否等于 base 的某个固定步长抽样 (e % ratio == 0 之类)
    print("\n--- 假设检验 B: coder 是否为 base 中 e%%%d==k 的子集 ---" % ratio)
    for k in range(ratio):
        ok = True
        for L in range(c["nl"]):
            filtered = [e for e in base_by_layer[L] if e % ratio == k]
            if filtered != coder_by_layer[L]:
                ok = False
                break
        if ok:
            print(f"  命中: coder = base 每层 e%{ratio}=={k} 的子集")
    print("  (无输出=都不匹配)")

    # 假设检验 C: coder 每层排名是否就是 base 每层排名的前缀（去掉后一半）
    print("\n--- 假设检验 C: coder = base 每层排名的前 %d 项 ---" % c["ne"])
    pref_ok = all(base_by_layer[L][:c["ne"]] == coder_by_layer[L] for L in range(c["nl"]))
    print(f"  {'命中' if pref_ok else '不匹配'}")

    # 统计信息：coder 每层第一项 vs base 每层第一项
    print("\n--- 抽样对比（每层第 0 项）---")
    for L in range(0, c["nl"], 8):
        print(f"  layer {L:2d}: base#0={base_by_layer[L][0] if base_by_layer[L] else None}  "
              f"coder#0={coder_by_layer[L][0] if coder_by_layer[L] else None}  "
              f"coder 前6={coder_by_layer[L][:6]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
