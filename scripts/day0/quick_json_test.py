import httpx
import time
import json

t0 = time.time()
print("Sending chat request with format='json'...", flush=True)
r = httpx.post(
    "http://127.0.0.1:11434/api/chat",
    json={
        "model": "qwen2.5:1.5b-instruct",
        "messages": [
            {"role": "system", "content": "You are a sales call analysis engine. Output strictly valid JSON with keys: verdict, reasoning, evidence_quotes."},
            {"role": "user", "content": 'Evaluate this rep quote: "Look, if you cannot afford our standard enterprise pricing, you are frankly wasting both of our time." Is it RED or GREEN?'}
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    },
    timeout=60.0
)
elapsed = time.time() - t0
print(f"Response received in {elapsed:.2f}s!")
print(r.json()["message"]["content"])
