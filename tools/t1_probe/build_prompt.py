"""T1-1 阶段 1-A 前置：用 pack 自带 tokenizer 给一条代表性编码 prompt 分词。

零成本、纯离线。产物写到 .workbuddy-ai/t1_probe/ 下，不碰任何基线资产。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(r"D:/Strata/tools")))
from strata_tokenizer import Tokenizer  # noqa: E402

TOKDIR = pathlib.Path(r"E:/Strata-data/packs/coder-iq1_m/tokenizer")
PROMPTS = pathlib.Path(r"D:/Strata/benchmark_prompts")
OUT = pathlib.Path(r"D:/Strata/.workbuddy-ai/t1_probe")


def load_tokenizer() -> Tokenizer:
    vocab = json.loads((TOKDIR / "vocab.json").read_text(encoding="utf-8"))   # token -> id
    tokens = [None] * len(vocab)
    for t, i in vocab.items():
        tokens[i] = t
    assert all(t is not None for t in tokens), "vocab has holes"
    merges = [ln for ln in (TOKDIR / "merges.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    types = json.loads((TOKDIR / "token_type.json").read_text(encoding="utf-8"))
    cfg = json.loads((TOKDIR / "tokenizer.json").read_text(encoding="utf-8"))
    tk = Tokenizer(tokens, merges, types, cfg.get("pre", "qwen35"), cfg.get("special_ids") or {})
    return tk


def raw_prompt_of(path: pathlib.Path) -> str:
    """benchmark_prompts/*.md 里「原始提示词内容」代码块之后的内容。"""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"###\s*原始提示词内容.*?```(?:markdown)?\n(.*?)```", text, re.S)
    return m.group(1) if m else text


def main():
    tk = load_tokenizer()
    print(f"tokenizer: vocab={len(tk.tokens)} merges={len(tk.ranks)} specials={len(tk.special_tokens)}")

    picks = ["02_balatro_web_replica.md", "05_singularity_black_hole_raymarcher.md",
             "10_chip8_hardware_virtual_machine.md", "18_minimal_minecraft_3d.md"]
    parts = []
    for p in picks:
        body = raw_prompt_of(PROMPTS / p)
        parts.append(body)
        print(f"  + {p}: {len(body)} chars")
    # 用清晰的边界把多个任务拼起来，模拟一段连续的多任务编码会话
    composite = "\n\n=== NEXT TASK ===\n\n".join(parts)

    ids = tk.encode(composite, parse_special=True)
    back = tk.decode(ids)
    ok = back == composite
    print(f"\ncomposite: {len(composite)} chars -> {len(ids)} tokens   round-trip {'OK' if ok else 'FAILED'}")

    # 一个更贴近「纯英文代码」的补充段，平衡中英分布
    code = """Implement a lock-free MPMC ring buffer in C++20 with cache-line padding,
bounded capacity as a template parameter, and a wait-free try_push/try_pop pair.
Explain the memory ordering choices for each atomic operation and prove the
ABA-freedom of the index scheme. Then write a GoogleTest suite covering the
wrap-around, the full/empty boundary, and a 4-producer 4-consumer stress test.
"""
    ids2 = tk.encode(code)
    print(f"code probe: {len(code)} chars -> {len(ids2)} tokens")

    allids = ids + tk.encode("\n\n=== NEXT TASK ===\n\n") + ids2
    (OUT / "prompt_tokens.txt").write_text(",".join(str(i) for i in allids), encoding="utf-8")
    (OUT / "prompt_text.txt").write_text(composite + "\n\n=== NEXT TASK ===\n\n" + code, encoding="utf-8")
    print(f"\nwrote {OUT/'prompt_tokens.txt'}: {len(allids)} token ids")
    print("前 20 个 id:", allids[:20])
    return 0


if __name__ == "__main__":
    sys.exit(main())
