import sys
import json
import time
import statistics
import threading
from pathlib import Path

ROOT = Path("D:/Strata")
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from serve.server import StrataEngine, child_env
import strata_tokenizer as ST

PROMPTS = [
    "Write a Python function that merges two sorted lists into one sorted list, with a docstring and two tests.",
    "Explain in two paragraphs how a refrigerator moves heat from inside to outside.",
    "List twelve European capitals with one sentence about each."
]

def get_chat_ids(tok, text):
    return tok.encode(f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n", parse_special=True)

def with_arg(args, flag, value):
    out = list(args)
    if flag in out:
        i = out.index(flag)
        del out[i:i + 2]
    if value is not None:
        out += [flag, str(value)]
    return out

def close(eng):
    proc = getattr(eng, "proc", None)
    if proc is None:
        return
    try:
        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.stdin.close()
        proc.wait(30)
    except Exception:
        proc.kill()

def main():
    cfg_path = ROOT / "strata-coder-iq1_m-256k.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    
    tpath = Path(cfg["tokenizer"])
    vocab = json.loads((tpath / "vocab.json").read_text(encoding="utf-8"))
    toks = [None] * len(vocab)
    for t, i in vocab.items():
        toks[i] = t
    tok = ST.Tokenizer(toks, (tpath / "merges.txt").read_text(encoding="utf-8").split("\n"),
                       json.loads((tpath / "token_type.json").read_text()))
    ids_list = [get_chat_ids(tok, p) for p in PROMPTS]

    worker_list = [8, 10, 12, 14, 15]
    results = {}

    print("=" * 60)
    print("  CPU Pool Worker Sweep on Intel Core Ultra 7 270K Plus")
    print("  (8 P-Cores + 16 E-Cores, Total 24 Cores)")
    print("=" * 60)

    for w in worker_list:
        test_args = with_arg(cfg["args"], "--pool-workers", w)
        print(f"\n[Test] Launching with --pool-workers {w} ...", flush=True)
        t0 = time.time()
        eng = StrataEngine(cfg["exe"], test_args, cwd=cfg.get("cwd"), log=cfg.get("log"), env=child_env(cfg))
        try:
            # Warm up
            for ids in ids_list[:1]:
                sampling = {"temperature": 0}
                list(eng.generate(ids, 64, sampling, threading.Event()))
            
            rates = []
            for r in range(2):
                for ids in ids_list:
                    sampling = {"temperature": 0}
                    n = sum(1 for t in eng.generate(ids, 128, sampling, threading.Event()) if t is not None)
                    ms = (eng.last or {}).get("decode_ms") or 0.0
                    if n > 8 and ms > 0:
                        speed = n / (ms / 1000.0)
                        rates.append(speed)
            
            med_speed = round(statistics.median(rates), 2)
            results[w] = med_speed
            print(f"--> Workers {w}: {med_speed} tok/s (Elapsed: {round(time.time() - t0, 1)}s)", flush=True)
        finally:
            close(eng)
            time.sleep(2)

    print("\n" + "=" * 60)
    print("  CPU Worker Pool Sweep Results Summary")
    print("=" * 60)
    for w, spd in results.items():
        diff = spd - results[15]
        diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
        print(f"  Workers {w:2d}: {spd:5.1f} tok/s  ({diff_str} vs Baseline 15)")
    print("=" * 60)

if __name__ == "__main__":
    main()
