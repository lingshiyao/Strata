"""tools/benchmark_speed_matrix.py - High-precision speed benchmark suite for Route A."""
import json
import time
import urllib.request
import sys

URL = "http://127.0.0.1:8080/v1/chat/completions"

TESTS = [
    ("Python SkipList", "Write a complete, production-grade SkipList implementation in Python with search, insert, and delete.", 400),
    ("Balatro Poker Engine", "Write a robust JavaScript module that evaluates a 5-card Balatro poker hand with chips and multipliers.", 400),
    ("GLSL Raymarching", "Write a GLSL fragment shader that performs sphere tracing raymarching with Phong lighting.", 400),
]

def run_test(name, prompt, max_tokens):
    payload = {
        "model": "qwen3.8-flash-next-coder-iq1_m",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "top_p": 0.95,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": True
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    t_first = None
    chunks = 0
    full_text = []
    
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[6:])
            delta = chunk["choices"][0].get("delta", {})
            token_text = delta.get("content", "") or delta.get("reasoning_content", "")
            if token_text:
                if t_first is None:
                    t_first = time.time()
                chunks += 1
                full_text.append(token_text)
                
    t_end = time.time()
    ttft = (t_first - t0) if t_first else 0.0
    decode_s = (t_end - t_first) if t_first else 0.0
    
    # In streaming SSE, each token is 1 chunk if not merged
    rate = chunks / decode_s if decode_s > 0 else 0.0
    text_len = len("".join(full_text))
    
    print(f"  [{name:22}] TTFT: {ttft:.3f}s | Decode: {decode_s:.2f}s | Tokens/Chunks: {chunks:3} | Rate: {rate:5.1f} tok/s | Chars: {text_len}")
    return {"name": name, "ttft": ttft, "decode_s": decode_s, "chunks": chunks, "rate": rate}

def main():
    print("============================================================")
    print("  STRATA HIGH-PRECISION SPEED BENCHMARK (ROUTE A)")
    print("============================================================")
    
    # Warmup
    try:
        run_test("Warmup", "Hello! Write a 1-line hello world in Python.", 30)
    except Exception as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)
        
    results = []
    for name, prompt, max_tok in TESTS:
        r = run_test(name, prompt, max_tok)
        results.append(r)
        
    avg_rate = sum(r["rate"] for r in results) / len(results)
    avg_ttft = sum(r["ttft"] for r in results) / len(results)
    print("------------------------------------------------------------")
    print(f"  SUMMARY: Average TTFT = {avg_ttft:.3f}s | Average Speed = {avg_rate:.1f} tok/s")
    print("============================================================\n")

if __name__ == "__main__":
    main()
