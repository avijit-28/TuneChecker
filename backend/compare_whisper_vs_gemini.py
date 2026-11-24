import re
import difflib

# 1. Reference Ground Truth Transcript from Gemini
GEMINI_REFERENCE = """
Hello, I am the agent.
Hello, I am the caller.
Agent 5, Agent 6, Agent 7, Agent 8, Agent 9, Agent 10.
Caller 11, Caller 12, Caller 13, Caller 14, Caller 15.
Agent 16, Agent 17, Agent 18, Agent 19, Agent 20.
Caller 21, Caller 22, Caller 23, Caller 24, Caller 25.
Agent 26, Agent 27, Agent 28, Agent 29, Agent 30.
Caller, I'm the caller and 33.
And I am the agent, I am the agent 37.
I am the caller, and 40, 41, 43.
I am the agent, I am at 7, 8, 9.
I am the caller, 52, 53, 54.
I am the agent, 58.
I am the caller, 1 minute, 2.
I am the agent, 1 minute, 8.
I am the caller, 1 minute, 13 seconds.
I am the agent, 1 minute, 16 seconds.
I am the caller, 1 minute, 22 seconds.
I am the agent, 1 minute, 28 seconds.
I am the caller, 1 minute, 32 seconds.
I am the agent, 1 minute, 38 seconds.
I am the caller, 1 minute, 42 seconds.
I am the agent, 1 minute, 48 seconds.
I am the caller, 1 minute, 52 seconds.
I am the agent, 1 minute, 58 seconds.
I am the caller, 2 minutes, 2 seconds.
I am the agent, 2 minutes, 8 seconds.
I am the caller, 2 minutes, 12 seconds.
And I'm the agent, 2 minutes, 18 seconds, Aardvark.
I am the caller, 2 minutes, 22 seconds, Banana.
I'm the agent, 2 minutes, 28 seconds, Chrysanthemum.
I am the caller, 2 minutes, 33 seconds, Delta.
I am the agent, 2 minutes, 38 seconds, Echo.
I am the caller, 2 minutes, 42 seconds, Foxtrot.
I am the agent, 2 minutes, 48 seconds, Golf.
I'm the caller, 2 minutes, 52 seconds, Hotel.
I am the agent, 2 minutes, 58 seconds, India.
And I am the caller. Goodbye.
I am the agent. Goodbye.
3 minutes, 10 seconds.
""".strip()

def normalize_text(text: str) -> list[str]:
    # Lowercase and keep alphanumeric words
    text = text.lower()
    words = re.findall(r"\b[a-z0-9']+\b", text)
    return words

def compute_wer(ref_words: list[str], hyp_words: list[str]) -> tuple[float, int, int, int, int]:
    # Dynamic programming Levenshtein distance on words
    r_len = len(ref_words)
    h_len = len(hyp_words)
    d = [[0] * (h_len + 1) for _ in range(r_len + 1)]

    for i in range(r_len + 1):
        d[i][0] = i
    for j in range(h_len + 1):
        d[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    total_errors = d[r_len][h_len]
    wer = (total_errors / max(1, r_len)) * 100
    accuracy = max(0.0, 100.0 - wer)
    return wer, accuracy, total_errors, r_len, h_len

def evaluate_transcription(whisper_transcript_text: str):
    ref_words = normalize_text(GEMINI_REFERENCE)
    hyp_words = normalize_text(whisper_transcript_text)

    wer, accuracy, errors, r_len, h_len = compute_wer(ref_words, hyp_words)

    # Phonetic vocabulary evaluation
    target_vocab = [
        "aardvark", "banana", "chrysanthemum", "delta", "echo",
        "foxtrot", "golf", "hotel", "india", "goodbye"
    ]

    vocab_hits = {}
    hyp_str = " ".join(hyp_words)
    for v in target_vocab:
        vocab_hits[v] = v in hyp_str

    print("=" * 60)
    print("TRANSCRIPTION COMPARISON: TuneChecker (Whisper) vs Gemini Model")
    print("=" * 60)
    print(f"Reference (Gemini) Total Words : {r_len}")
    print(f"TuneChecker Total Words        : {h_len}")
    print(f"Word Error Rate (WER)          : {wer:.2f}%")
    print(f"Transcription Accuracy         : {accuracy:.2f}%")
    print("-" * 60)
    print("Phonetic & Challenge Vocabulary Check:")
    for word, found in vocab_hits.items():
        status = "[PASS]" if found else "[MISS]"
        print(f"  {status} {word.capitalize()}")
    print("=" * 60)

    return {
        "gemini_words": r_len,
        "whisper_words": h_len,
        "wer": round(wer, 2),
        "accuracy": round(accuracy, 2),
        "vocab_accuracy_pct": round((sum(vocab_hits.values()) / len(target_vocab)) * 100, 1),
        "vocab_details": vocab_hits
    }

if __name__ == "__main__":
    import os
    path = "D:/avi/TuneChecker/backend/data/audio/benchmark_whisper_transcript.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        evaluate_transcription(content)
    else:
        print("Transcript file not found at", path)
