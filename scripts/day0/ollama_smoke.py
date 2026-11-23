import time
import json
import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:1.5b-instruct"

TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["RED", "GREEN"]
        },
        "reasoning": {
            "type": "string"
        },
        "evidence_quotes": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["verdict", "reasoning", "evidence_quotes"]
}

PROMPT = """Analyze the sales representative's tone in the following statement:
"Look, if you can't afford our standard enterprise pricing, you're frankly wasting both of our time."

Evaluate strictly against the professional guidelines: Is this tone RED (unprofessional, hostile, dismissive) or GREEN (professional, constructive)?
Return valid JSON adhering to the provided schema."""

def test_ollama_structured_output():
    print(f"Testing Ollama model '{MODEL}' at {OLLAMA_URL} with format='json'...")
    latencies = []
    
    for i in range(3):
        t0 = time.time()
        print(f"Sending request {i+1}...", flush=True)
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a sales call quality analysis assistant. Output strictly in JSON format with keys 'verdict' ('RED' or 'GREEN'), 'reasoning' (string), and 'evidence_quotes' (array of strings)."},
                    {"role": "user", "content": PROMPT}
                ],
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "seed": 42
                },
                "stream": False
            },
            timeout=60.0
        )
        elapsed = time.time() - t0
        latencies.append(elapsed)
        
        assert response.status_code == 200, f"Ollama error: {response.text}"
        res_json = response.json()
        raw_content = res_json["message"]["content"]
        print(f"Run {i+1} took {elapsed:.2f}s:")
        print(f"  Content: {raw_content.strip()}")
        
        # Verify valid JSON
        parsed = json.loads(raw_content)
        assert parsed.get("verdict") in ["RED", "GREEN"], f"Invalid verdict: {parsed.get('verdict')}"
        assert isinstance(parsed.get("evidence_quotes"), list), "evidence_quotes is not a list"
        print(f"  Verdict: {parsed['verdict']}")
        
    avg_latency = sum(latencies) / len(latencies)
    print(f"\nAll 3 runs passed validation! Avg latency: {avg_latency:.2f}s")
    print("Ollama structured output test: PASS")

if __name__ == "__main__":
    test_ollama_structured_output()
