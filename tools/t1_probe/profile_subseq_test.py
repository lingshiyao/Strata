"""T1-1 前置取证（三）：决定性判据——coder 排名是否为 base 排名的保序子序列？

若 coder profile 只是出厂排名的重新索引（保留原编号），则对每层 L，
    pos_L(coder[L][j]) 随 j 严格递增（coder 是 base 的一个保序子序列）。
同时给出两者的序相关度，量化「coder 到底带了多少新信息」。

零成本、纯离线。
"""
import struct
import sys
from pathlib import Path

MAGIC = b"STRP"


def read_by_layer(path):
    blob = Path(path).read_bytes()
    assert blob[:4] == MAGIC
    ver, nl, ne, slots, n = struct.unpack_from("<5I", blob, 4)
    ranked = [struct.unpack_from("<HH", blob, 24 + 4 * i) for i in range(n)]
    by_layer = [[] for _ in range(nl)]
    for L, e in ranked:
        by_layer[L].append(e)
    return nl, ne, by_layer


def main():
    nl, ne_b, base = read_by_layer(r"D:/Strata/data/expert-profile.bin")
    _, ne_c, coder = read_by_layer(r"D:/Strata/data/expert-profile-coder.bin")
    pos = [{e: i for i, e in enumerate(base[L])} for L in range(nl)]

    print("=== 判据 1: coder[L] 是否为 base[L] 的保序子序列（同编号空间）===")
    incr_layers = 0
    for L in range(nl):
        p = [pos[L][e] for e in coder[L]]
        if all(p[j] < p[j + 1] for j in range(len(p) - 1)):
            incr_layers += 1
    print(f"  严格递增的层数: {incr_layers}/48")
    if incr_layers == 48:
        print("  >>> coder = base 的保序子序列（出厂排名的重新索引）——通用排名，不含编码信息")
    else:
        print("  >>> 不是保序子序列：coder 排名携带了 base 之外的信息")

    print("\n=== 判据 2: 序相关度（coder 相对 base 的顺序一致性）===")
    # 对每层：coder 的元素按 base 位置排序后，其 coder 顺序的逆序对数占比
    total_pairs = 0
    concordant = 0
    for L in range(nl):
        p = [pos[L][e] for e in coder[L]]        # coder 顺序下，各元素在 base 中的位置
        m = len(p)
        # 数逆序对（p 中 i<j 但 p[i]>p[j]）
        inv = 0
        # O(n log n) 用归并
        def count_inv(a):
            if len(a) < 2:
                return 0, a
            mid = len(a) // 2
            c1, l = count_inv(a[:mid])
            c2, r = count_inv(a[mid:])
            c, i, j, out = c1 + c2, 0, 0, []
            while i < len(l) and j < len(r):
                if l[i] <= r[j]:
                    out.append(l[i]); i += 1
                else:
                    out.append(r[j]); j += 1
                    c += len(l) - i
            out += l[i:]; out += r[j:]
            return c, out
        inv, _ = count_inv(p)
        total_pairs += m * (m - 1) // 2
        concordant += m * (m - 1) // 2 - inv
    tau = 2 * concordant / total_pairs - 1
    print(f"  Kendall tau(coder 顺序 vs base 顺序) = {tau:+.4f}   (1=完全相同序, 0=无关, -1=完全反序)")

    print("\n=== 判据 3: 若 coder 只是 base 的「前 N 项」，N 应是多少？===")
    # 对每层，coder 元素在 base 中的最大位置
    for L in (0, 16, 32, 47):
        p = sorted(pos[L][e] for e in coder[L])
        print(f"  layer {L:2d}: 位置范围 [{p[0]}, {p[-1]}]  跨度 {p[-1]-p[0]+1}  "
              f"（若为前缀则应为 [0,255]）")

    print("\n=== 判据 4: 两个 profile 的 top-3629 集合重合度（缓存实际驻留的那批）===")
    N = 3629
    base_flat = [e for L in range(nl) for e in base[L]]      # 按全局排名（层优先）拼接
    # 注意：排名表是逐层排列的；实际 slot i = ranked[i]，i 跨层。
    # 用 read_by_layer 已丢失全局顺序，这里重新读全局顺序
    def read_flat(path):
        blob = Path(path).read_bytes()
        ver, nl2, ne2, slots, n = struct.unpack_from("<5I", blob, 4)
        return [struct.unpack_from("<HH", blob, 24 + 4 * i) for i in range(n)]
    fb = read_flat(r"D:/Strata/data/expert-profile.bin")
    fc = read_flat(r"D:/Strata/data/expert-profile-coder.bin")
    # base 的 pair 里 expert>=256 的不会出现在 coder 模型里；映射未知，直接比较 (layer, expert) 原编号
    topb = set(fb[:N])
    topc = set(fc[:N])
    inter = len(topb & topc)
    print(f"  base top{N} ∩ coder top{N} = {inter} / {N}  ({100*inter/N:.1f}%)")
    print(f"  base top{N} 中 expert>=256 的项 = {sum(1 for (_,e) in fb[:N] if e>=256)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
