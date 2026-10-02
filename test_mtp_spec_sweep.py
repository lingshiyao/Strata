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

CODING_PROMPTS = [
    "Write a TypeScript class Matrix4x4 with methods for identity, multiply, transpose, and invert.",
    "Write a complete Python FastAPI endpoint that validates and processes a payment webhook with HMAC signature verification.",
    "Write a responsive HTML5 CSS3 navigation bar with mobile hamburger menu and smooth animations in vanilla JavaScript."
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
    ids_list = [get_chat_ids(tok, p) for p in CODING_PROMPTS]

    candidates = [
        {"name": "Baseline (Spec 4, MinP 0.50, Res 700)", "spec": 4, "min_p": "0.50", "res": 700},
        {"name": "Exp 1 (Spec 5, MinP 0.50, Res 700)",    "spec": 5, "min_p": "0.50", "res": 700},
        {"name": "Exp 2 (Spec 5, MinP 0.40, Res 700)",    "spec": 5, "min_p": "0.40", "res": 700},
        {"name": "Exp 3 (Spec 6, MinP 0.40, Res 700)",    "spec": 6, "min_p": "0.40", "res": 700},
        {"name": "Exp 4 (Spec 5, MinP 0.35, Res 700)",    "spec": 5, "min_p": "0.35", "res": 700},
        {"name": "Exp 5 (Spec 5, MinP 0.40, Res 350)",    "spec": 5, "min_p": "0.40", "res": 350},
    ]

    results = {}

    print("=" * 70)
    print("  MTP Speculative Decoding & VRAM Cache Sweep on Real Coding Tasks")
    print("=" * 70)

    for cand in candidates:
        args = list(cfg["args"])
        args = with_arg(args, "--spec", cand["spec"])
        args = with_arg(args, "--spec-min-p", cand["min_p"])
        args = with_arg(args, "--vram-reserve-mib", cand["res"])
        args = with_arg(args, "--pool-workers", 15)

        print(f"\n[Test] Launching {cand['name']} ...", flush=True)
        t0 = time.time()
        eng = StrataEngine(cfg["exe"], args, cwd=cfg.get("cwd"), log=cfg.get("log"), env=child_env(cfg))
        try:
            # Warm up
            sampling = {"temperature": 0}
            list(eng.generate(ids_list[0], 64, sampling, threading.Event()))

            rates = []
            for idx, ids in enumerate(ids_list):
                sampling = {"temperature": 0}
                n = sum(1 for t in eng.generate(ids, 160, sampling, threading.Event()) if t is not None)
                ms = (eng.last or {}).get("decode_ms") or 0.0
                if n > 8 and ms > 0:
                    spd = n / (ms / 1000.0)
                    rates.append(spd)
                    print(f"    Prompt {idx+1}: {spd:.1f} tok/s ({n} tokens)", flush=True)

            med_spd = round(statistics.median(rates), 2)
            results[cand["name"]] = med_spd
            print(f"--> {cand['name']} Median: {med_spd} tok/s (Elapsed: {round(time.time() - t0, 1)}s)", flush=True)
        finally:
            close(eng)
            time.sleep(2)

    print("\n" + "=" * 70)
    print("  MTP Speculative Decoding & VRAM Cache Sweep Summary")
    print("=" * 70)
    base_spd = results["Baseline (Spec 4, MinP 0.50, Res 700)"]
    for name, spd in results.items():
        diff = spd - base_spd
        diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
        pct = (diff / base_spd) * 100
        pct_str = f"+{pct:.1f}%" if pct > 0 else f"{pct:.1f}%"
        print(f"  {name:<42} : {spd:5.1f} tok/s  ({diff_str} tok/s, {pct_str})")
    print("=" * 70)

if __name__ == "__main__":
    main()
