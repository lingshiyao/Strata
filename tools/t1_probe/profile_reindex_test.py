"""T1-1 前置取证（二）：coder profile 是否 = 出厂通用排名经专家重编号 σ 得到？

README 声称 coder profile 是「the shipped 48x512 ranking 重新索引」而来。
若成立，则存在一个全模型统一的双射 σ: {0..255} -> S (S ⊂ {0..511})，使
    coder[L] == [σ(e) for e in base[L] if e in S]        (对全部 48 层成立)

零成本、纯离线。
"""
import struct
import sys
from pathlib import Path

MAGIC = b"STRP"


def read_ranked(path):
    blob = Path(path).read_bytes()
    assert blob[:4] == MAGIC
    ver, nl, ne, slots, n = struct.unpack_from("<5I", blob, 4)
    ranked = [struct.unpack_from("<HH", blob, 24 + 4 * i) for i in range(n)]
    by_layer = [[] for _ in range(nl)]
    for L, e in ranked:
        by_layer[L].append(e)
    return nl, ne, by_layer


def main():
    nl_b, ne_b, base = read_ranked(r"D:/Strata/data/expert-profile.bin")
    nl_c, ne_c, coder = read_ranked(r"D:/Strata/data/expert-profile-coder.bin")
    assert nl_b == nl_c == 48
    print(f"base  {nl_b}x{ne_b}   coder {nl_c}x{ne_c}")

    # ---- 候选假设 1: S = base 每层前 256 的集合, sigma(coder[L][j]) = base[L][j]
    print("\n=== 假设 1: coder[L] == base[L][:256] 经 sigma 重命名（sigma 由 layer0 定出）===")
    sigma = {}          # coder 编号 -> base 编号
    ok1 = True
    for j in range(ne_c):
        sigma[coder[0][j]] = base[0][j]
    if len(sigma) != ne_c:
        print("  !! layer0 的 coder 编号有重复，假设不成立")
        ok1 = False
    bad_layers = []
    for L in range(nl_b):
        for j in range(ne_c):
            if sigma.get(coder[L][j]) != base[L][j]:
                bad_layers.append(L)
                break
    if not bad_layers and ok1:
        print("  >>> 完全命中！coder profile = base 排名前 256 经统一 sigma 重命名（通用排名，不含编码信息）")
        return 0
    print(f"  不成立：{len(bad_layers)}/48 层与 sigma 不一致，前几层 {bad_layers[:8]}")

    # ---- 候选假设 2: sigma 与「保留集 S」都由 base 每层的全排名推出（coder 是 base 去掉 S 外元素）
    #    由 layer0 建立 sigma: 遍历 base[0] 的顺序, 依次把 coder[0] 的编号配给它
    print("\n=== 假设 2: coder[L] = base[L] 过滤掉 S 外元素后经 sigma（S 由 layer0 顺序对齐推出）===")
    # coder[0] 是 256 长的序列；base[0] 是 512 长的排列。
    # 若 coder[0] = base[0]|_S 经 sigma，则 base[0] 中被保留的元素恰好是 256 个，
    # 它们必须与 coder[0] 的元素一一对应且顺序一致。用「位置对齐全序列」的假设：
    #   sigma(coder[0][j]) = base[0][j] 已被假设1否掉，说明保留集不是前 256。
    # 换一种：保留集 S 未知，但 sigma 必须让 48 层的顺序全部单调。
    # 用贪心：对每层 L，sigma(coder[L][j]) 在 base[L] 中的位置必须随 j 递增。
    pos = [{e: i for i, e in enumerate(base[L])} for L in range(nl_b)]
    # 收集约束：sigma(k) 属于哪个 base 编号？未知。改用「k -> base 位置向量」一致性。
    # 简化：检查 coder 每层排名是否等于 base 每层排名去掉「某固定 256 个」后的形状。
    # 用 layer0 与 layer1 的交集推断：coder[L] 的集合大小 256。
    # 若 coder = base|_S 重命名，则对任意层 L，集合 {base[L][i] : i 是 coder 元素的原像} 恒为 S。
    # 直接测试：把 coder[L] 当作 base[L] 的子序列，求最长公共子序列长度是否 =256。
    def is_subseq(a, b):
        it = iter(b)
        return all(x in it for x in a)
    # 注意 a,b 是不同编号空间，先不管编号，只看「coder 的顺序是否为 base 顺序的子序列」需要映射。
    # 更直接：用位置单调性构造 sigma 的候选（把 coder[L][j] 与 base[L] 中第 j 个「未被占用」元素配对）
    print("  （改用单调性构造：见假设 3）")

    # ---- 候选假设 3: 存在 sigma，使 48 层的 (coder->base) 映射一致
    #    从 layer0 出发：coder[0] 有 256 个编号，base[0] 是 512 的排列。
    #    若 coder[0] 是 base[0] 的一个「保持相对顺序的 256 子序列」经 sigma 得到，
    #    那么 sigma(coder[0][j]) 在 base[0] 中位置递增。
    #    取最朴素候选：sigma(coder[0][j]) = base[0] 中第 j 个位置（前 256）已否；
    #    取「等间隔」候选：第 j 个 = base[0][2j] 或 base[0][2j+1]
    print("\n=== 假设 3: 等间隔子序列 (保留集 = base[L] 的奇/偶位) ===")
    for stride_off in (0, 1):
        sig = {}
        ok = True
        for j in range(ne_c):
            sig[coder[0][j]] = base[0][2 * j + stride_off]
        for L in range(nl_b):
            for j in range(ne_c):
                if sig.get(coder[L][j]) != base[L][2 * j + stride_off]:
                    ok = False
                    break
            if not ok:
                break
        print(f"  offset {stride_off}: {'命中' if ok else '不匹配'}")

    # ---- 假设 4: coder 是 base 每层排名中「值最小/最大」的 256 个，保序
    print("\n=== 假设 4: coder[L] = base[L] 中编号最小的 256 个（保序）或最大的 256 个（保序）===")
    for name, sel in (("最小256", lambda L: [e for e in base[L] if e < ne_c]),
                      ("最大256", lambda L: [e for e in base[L] if e >= ne_b - ne_c])):
        same = all(sel(L) == coder[L] for L in range(nl_b))
        print(f"  {name}: {'命中' if same else '不匹配'}")

    # ---- 统计：coder 与 base 的排名相关性（Spearman 近似：按 base 位置给 coder 排序）
    print("\n=== 结构对比：coder[L] 的元素在 base[L] 中的位置分布 ===")
    for L in (0, 16, 32, 47):
        idxs = sorted(pos[L][e] for e in coder[L])
        print(f"  layer {L:2d}: coder 元素在 base 中的位置 min={idxs[0]} max={idxs[-1]} "
              f"中位={idxs[len(idxs)//2]}  前10位置={idxs[:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
