"""tools/test_ultra_empirical.py - Empirical benchmark suite for Version 3 Ultra."""
import json
import time
import urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"

def benchmark_request(name, prompt, max_tokens=1024, stream=True):
    print(f"\n============================================================")
    print(f" [TEST] {name}")
    print(f"============================================================")
    payload = {
        "model": "qwen3.8-flash-next-coder-iq1_m",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "top_p": 0.95,
        "stream": stream
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    first_token_time = None
    output_tokens = 0
    full_text = []
    
    if stream:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                chunk = json.loads(line[6:])
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                reasoning = delta.get("reasoning_content", "")
                token_text = content or reasoning
                if token_text:
                    if first_token_time is None:
                        first_token_time = time.time()
                    output_tokens += 1
                    full_text.append(token_text)
    else:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            first_token_time = time.time()
            content = body["choices"][0]["message"]["content"]
            full_text.append(content)
            output_tokens = body.get("usage", {}).get("completion_tokens", len(content.split()))

    t_end = time.time()
    ttft_s = (first_token_time - t0) if first_token_time else 0.0
    decode_s = (t_end - first_token_time) if first_token_time else 0.0
    decode_tok_s = (output_tokens / decode_s) if decode_s > 0 else 0.0
    
    result = "".join(full_text)
    preview = result[:200].replace("\n", " ") + ("..." if len(result) > 200 else "")
    
    print(f"  Total Tokens Generated : {output_tokens}")
    print(f"  TTFT (Time-to-first)   : {ttft_s:.2f} s")
    print(f"  Decode Generation Rate : {decode_tok_s:.1f} tok/s")
    print(f"  Total Roundtrip Time   : {t_end - t0:.2f} s")
    print(f"  Output Sample Preview  : {preview}")
    
    return {
        "name": name,
        "tokens": output_tokens,
        "ttft_s": ttft_s,
        "decode_tok_s": decode_tok_s,
        "total_s": t_end - t0
    }

if __name__ == "__main__":
    time.sleep(1)
    # Test 1: Python High-Performance Data Structure
    r1 = benchmark_request(
        "Algorithm Implementation (SkipList in Python)",
        "Write a complete, production-grade SkipList implementation in Python with search, insert, delete, and comprehensive comments.",
        max_tokens=600
    )
    
    # Test 2: HTML/Canvas Game Logic (Balatro-style Hand Evaluation)
    r2 = benchmark_request(
        "Complex Game Logic (Balatro Poker Hand Scoring Engine)",
        "Write a robust JavaScript module that evaluates a 5-card Balatro poker hand (High Card, Pair, Two Pair, Three of a Kind, Straight, Flush, Full House, Four of a Kind, Straight Flush, Flush Five). Include base chips and multipliers for each hand type.",
        max_tokens=800
    )
    
    # Test 3: Multi-turn prompt continuation (Test short-read verify window)
    r3 = benchmark_request(
        "Agent Short Continuation (Quick Refactor)",
        "Given the function: `function add(a, b) { return a + b; }`, refactor it to handle arbitrary numbers of arguments with type validation and write 3 assert tests.",
        max_tokens=400
    )
    
    print("\n============================================================")
    print("  ALL EMPIRICAL TESTS COMPLETED SUCCESSFULLY!")
    print("============================================================")
