import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
import os

PORT = 8080
BASE_URL = f"http://127.0.0.1:{PORT}"
SERVER_BAT = r"D:\Strata\run-coder-iq1_m-256k.bat"

def is_server_ready():
    try:
        req = urllib.request.Request(f"{BASE_URL}/health", headers={"User-Agent": "Bench256K"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return data.get("loaded", False)
    except Exception:
        return False

def start_server_if_needed():
    if is_server_ready():
        print(f"[Engine] Strata 256K is already running on port {PORT}!", flush=True)
        return None
    print(f"[Engine] Starting Strata 256K Engine via {SERVER_BAT}...", flush=True)
    proc = subprocess.Popen(
        [r"D:\Strata\.venv\Scripts\python.exe", r"D:\Strata\serve\server.py", "--engine", "strata", "--config", r"D:\Strata\strata-coder-iq1_m-256k.json", "--port", str(PORT)],
        cwd=r"D:\Strata",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("[Engine] Loading 23.42 GB weights & filling 3629 GPU expert slots (takes ~12-15s)...", flush=True)
    for i in range(60):
        time.sleep(1)
        if is_server_ready():
            print(f"[Engine] Server is READY in {i+1} seconds!\n", flush=True)
            return proc
    print("[Engine] Warning: Server launch timed out.", flush=True)
    return proc

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
    start_decode = None
    token_count = 0

    try:
        with urllib.request.urlopen(req, timeout=400) as resp:
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
                        content = delta.get("content") or delta.get("reasoning_content")
                        if content:
                            if ttft is None:
                                ttft = time.time() - t0
                                start_decode = time.time()
                            token_count += 1
                except Exception:
                    pass
    except Exception as e:
        return {"error": str(e), "target_tokens": target_tokens}

    total_time = time.time() - t0
    decode_time = (time.time() - start_decode) if start_decode else 0.001
    tok_s = (token_count / decode_time) if decode_time > 0 else 0
    prefill_rate = round(target_tokens / ttft, 1) if (ttft and ttft > 0) else 0

    return {
        "target_tokens": target_tokens,
        "ttft_sec": round(ttft if ttft else total_time, 2),
        "prefill_rate": prefill_rate,
        "decode_tok_s": round(tok_s, 1),
        "output_tokens": token_count,
        "decode_time_sec": round(decode_time, 2),
        "total_sec": round(total_time, 2)
    }

def main():
    print("=" * 85)
    print("  STRATA 256K (Qwen3.8-Coder-IQ1_M) FULL-SPECTRUM SCALING BENCHMARK")
    print("  Hardware: RTX 5070 Ti (16GB GDDR7) + 48GB DDR5 RAM + Intel Core Ultra 7 270K")
    print("  Testing Target: Context 0 -> 256K (Full Gradient: 1K, 16K, 32K, 64K, 128K, 192K, 240K)")
    print("=" * 85, flush=True)

    start_server_if_needed()

    points = [
        ("1K   (Baseline)", 1000),
        ("16K  (Mid-Context)", 16000),
        ("32K  (GPU VRAM Border)", 32768),
        ("64K  (RAM Stream 25%)", 64000),
        ("128K (RAM Stream 50%)", 128000),
        ("192K (RAM Stream 75%)", 192000),
        ("240K (Near Full Limit)", 240000),
    ]

    results = []
    print(f"{'Context Level':<24} | {'Prefill TTFT':<15} | {'Prefill Rate':<15} | {'Decode Speed':<14} | {'Total Time'}")
    print("-" * 85, flush=True)

    for label, target in points:
        print(f"-> Testing {label} ({target:,} tokens)...", end="\r", flush=True)
        res = run_test_point(target, max_output=64)
        if "error" in res:
            print(f"{label:<24} | ERROR: {res['error']}")
        else:
            print(f"{label:<24} | {res['ttft_sec']:>6.2f} s        | {res['prefill_rate']:>7.1f} tok/s   | {res['decode_tok_s']:>6.1f} tok/s   | {res['total_sec']:>6.2f} s", flush=True)
            results.append(res)
        time.sleep(2)

    print("=" * 85)
    print("  BENCHMARK COMPLETED! Summary Analysis Ready.")
    print("=" * 85, flush=True)

if __name__ == "__main__":
    main()
