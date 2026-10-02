import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path("D:/Strata")
sys.path.insert(0, str(ROOT))

PORT = 8080
BASE_URL = f"http://127.0.0.1:{PORT}"

def is_server_ready():
    try:
        req = urllib.request.Request(f"{BASE_URL}/health", headers={"User-Agent": "Bench256K"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return data.get("loaded", False)
    except Exception:
        return False

def get_server_status():
    try:
        req = urllib.request.Request(f"{BASE_URL}/status", headers={"User-Agent": "Bench256K"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}

def run_test_point(target_tokens, max_output=64):
    code_block = "function evalHandScore(hand, jokers, mult) { let chips = 0; for(let c of hand){ chips += c.val; } return chips * (mult + jokers.length * 4); }\n"
    approx_chunk_tokens = len(code_block) // 3.5
    repeat = max(1, int(target_tokens / approx_chunk_tokens))
    
    prompt = f"/* Balatro Simulation Benchmark Context Scale */\n" + (code_block * repeat) + "\n/* Task: Write one line declaring done = true; */\n"
    
    payload = {
        "model": "qwen3.8-flash-next-coder-iq1_m",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": max_output,
        "temperature": 0.5,
        "reasoning_budget_tokens": 64
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )

    t0 = time.time()
    ttft = None
    token_count = 0
    start_decode = None

    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if not line_str.startswith("data:"):
                continue
            data_part = line_str[5:].strip()
            if data_part == "[DONE]":
                break
            try:
                chunk = json.loads(data_part)
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    if (delta.get("content") or delta.get("reasoning_content")) and ttft is None:
                        ttft = time.time() - t0
                        start_decode = time.time()
                    if delta.get("content") or delta.get("reasoning_content"):
                        token_count += 1
            except Exception:
                pass

    total_time = time.time() - t0
    decode_time = (time.time() - start_decode) if start_decode else 0.001
    tok_per_sec = (token_count / decode_time) if decode_time > 0 else 0

    status = get_server_status()
    cache_hit_pct = status.get("cache_hit_pct", 0)

    return {
        "target_tokens": target_tokens,
        "actual_prompt_chars": len(prompt),
        "actual_prompt_tokens_est": int(len(prompt) / 3.5),
        "ttft_sec": round(ttft if ttft is not None else total_time, 2),
        "decode_time_sec": round(decode_time, 2),
        "tokens_out": token_count,
        "tok_per_sec": round(tok_per_sec, 1),
        "total_time_sec": round(total_time, 2),
        "cache_hit_pct": round(cache_hit_pct, 1)
    }

def main():
    # Make sure port 8080 is ready
    print("[Full Spectrum] Checking if server is already running on port 8080...", flush=True)
    if not is_server_ready():
        print("[Full Spectrum] Error: Server is not running. Please start the candidate server first.", flush=True)
        sys.exit(1)

    print("[Full Spectrum] Server is UP and healthy on port 8080!", flush=True)

    test_points = [
        ("Short (1K)", 1000),
        ("Mid (18K)", 18000),
        ("32K Boundary (36K)", 36000),
        ("Heavy (72K)", 72000),
        ("Ultra (144K)", 144000),
        ("Near-Full (216K)", 216000),
    ]

    print("\n" + "=" * 90)
    print(f"{'Context Test Point':<22} | {'Est. Tokens':<12} | {'TTFT (Prefill)':<14} | {'Decode Rate':<14} | {'Cache Hit':<10} | {'Total Time'}")
    print("=" * 90, flush=True)

    results = []
    for label, target_tokens in test_points:
        print(f"[Run] Testing point: {label} (~{target_tokens} tokens)...", flush=True)
        res = run_test_point(target_tokens, max_output=64)
        results.append((label, res))
        print(f"  --> {label:<20} | {res['actual_prompt_tokens_est']:>6d} tok   | {res['ttft_sec']:>6.2f} s       | {res['tok_per_sec']:>6.1f} tok/s    | {res['cache_hit_pct']:>5.1f}%    | {res['total_time_sec']:>6.2f} s", flush=True)
        time.sleep(2)

    print("\n" + "=" * 90)
    print("  Candidate Tuned Profile Full Spectrum (1K -> 216K) Results")
    print("=" * 90)
    for label, res in results:
        print(f"{label:<22} | {res['actual_prompt_tokens_est']:>6d} tok   | {res['ttft_sec']:>6.2f} s       | {res['tok_per_sec']:>6.1f} tok/s    | {res['cache_hit_pct']:>5.1f}%    | {res['total_time_sec']:>6.2f} s")
    print("=" * 90)

if __name__ == "__main__":
    main()
