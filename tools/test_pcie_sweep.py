"""tools/test_pcie_sweep.py - Sweep pcie_frac on running server using strata_tune."""
import json
import time
import urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"
PROMPT = "Write a complete, production-grade SkipList implementation in Python with search, insert, and delete."

def test_pcie(frac):
    payload = {
        "model": "qwen3.8-flash-next-coder-iq1_m",
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 500,
        "temperature": 0.5,
        "top_p": 0.95,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": True,
        "strata_tune": {"pcie_frac": frac}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    t_first = None
    chunks = 0
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[6:])
            delta = chunk["choices"][0].get("delta", {})
            tok = delta.get("content", "") or delta.get("reasoning_content", "")
            if tok:
                if t_first is None:
                    t_first = time.time()
                chunks += 1
    t_end = time.time()
    rate = chunks / (t_end - t_first) if t_first else 0.0
    print(f"  pcie_frac={frac:.2f} -> {chunks} tokens in {t_end - t_first:.2f}s = {rate:.1f} tok/s")
    return rate

for frac in [0.20, 0.25, 0.30, 0.35, 0.40]:
    test_pcie(frac)
