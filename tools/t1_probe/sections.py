"""计算 prompt_tokens.txt 中各任务段的 token 边界，供 leave-one-task-out 评估使用。

分词是确定性的，因此这里重算出的边界与引擎读到的 prompt_tokens.txt 完全一致。
纯离线，不触碰基线。
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
    vocab = json.loads((TOKDIR / "vocab.json").read_text(encoding="utf-8"))
    tokens = [None] * len(vocab)
    for t, i in vocab.items():
        tokens[i] = t
    merges = [ln for ln in (TOKDIR / "merges.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    types = json.loads((TOKDIR / "token_type.json").read_text(encoding="utf-8"))
    cfg = json.loads((TOKDIR / "tokenizer.json").read_text(encoding="utf-8"))
    return Tokenizer(tokens, merges, types, cfg.get("pre", "qwen35"), cfg.get("special_ids") or {})


def raw_prompt_of(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"###\s*原始提示词内容.*?```(?:markdown)?\n(.*?)```", text, re.S)
    return m.group(1) if m else text


def main():
    tk = load_tokenizer()
    picks = ["02_balatro_web_replica.md", "05_singularity_black_hole_raymarcher.md",
             "10_chip8_hardware_virtual_machine.md", "18_minimal_minecraft_3d.md"]
    code = """Implement a lock-free MPMC ring buffer in C++20 with cache-line padding,
bounded capacity as a template parameter, and a wait-free try_push/try_pop pair.
Explain the memory ordering choices for each atomic operation and prove the
ABA-freedom of the index scheme. Then write a GoogleTest suite covering the
wrap-around, the full/empty boundary, and a 4-producer 4-consumer stress test.
"""
    SEP = "\n\n=== NEXT TASK ===\n\n"
    seg_tokens = tk.encode(SEP)

    segs = []
    cursor = 0
    total = 0
    texts = []
    for p in picks:
        texts.append((p, raw_prompt_of(PROMPTS / p)))
    texts.append(("code_probe", code))

    # 复刻 build_prompt.py 的拼接：先 join 前 4 段，再 SEP + code
    # 注意 build_prompt 里 parts 只有 4 个 benchmark，code 是后加的
    n_bench = 4
    ids_running = []
    for idx, (name, body) in enumerate(texts):
        if idx > 0:
            ids_running += seg_tokens
        start = len(ids_running)
        ids_running += tk.encode(body, parse_special=True) if idx < n_bench else tk.encode(body)
        end = len(ids_running)
        segs.append(dict(name=name, start=start, end=end, n=end - start))

    total = len(ids_running)
    print(f"重建 prompt: {total} tokens")
    for s in segs:
        print(f"  {s['name']:42s} [{s['start']:5d}, {s['end']:5d})  n={s['n']}")

    # 与 prompt_tokens.txt 对照
    saved = [int(x) for x in (OUT / "prompt_tokens.txt").read_text(encoding="utf-8").split(",") if x.strip()]
    print(f"\nprompt_tokens.txt: {len(saved)} tokens  ->  {'一致' if saved == ids_running else '不一致!'}")
    if saved != ids_running:
        # 找出第一个分歧点
        for i, (a, b) in enumerate(zip(saved, ids_running)):
            if a != b:
                print(f"  首个分歧在 token {i}: saved={a} rebuilt={b}")
                break

    (OUT / "sections.json").write_text(json.dumps(
        dict(total=total, gen=128, segs=segs, sep=SEP), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT/'sections.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
