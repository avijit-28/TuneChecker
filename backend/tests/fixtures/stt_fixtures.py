"""
Pre-canned STT results and segment collections for fast, deterministic pipeline testing.
"""
import gzip
import json
from app.pipeline.providers.stt.base import SttResult, SttSegment, SttWord

def _make_words(text: str, start_ms: int, end_ms: int) -> list[SttWord]:
    tokens = text.split()
    if not tokens:
        return []
    duration = max(1, end_ms - start_ms)
    step = duration // len(tokens)
    words = []
    for i, token in enumerate(tokens):
        w_start = start_ms + i * step
        w_end = w_start + step if i < len(tokens) - 1 else end_ms
        words.append(SttWord(token, w_start, w_end))
    return words

def make_green_call_stt_result() -> SttResult:
    """Compliant, professional sales representative call. Expected verdict: GREEN."""
    segments = [
        SttSegment("g1", "Good morning, thank you for calling Brightwave Solutions, my name is Alex.", 0, 4200, _make_words("Good morning, thank you for calling Brightwave Solutions, my name is Alex.", 0, 4200)),
        SttSegment("g2", "Hi Alex, I was looking into your enterprise software plan.", 5500, 8500, _make_words("Hi Alex, I was looking into your enterprise software plan.", 5500, 8500)),
        SttSegment("g3", "I would be happy to explain our licensing tiers and schedule a live product demo.", 9800, 14500, _make_words("I would be happy to explain our licensing tiers and schedule a live product demo.", 9800, 14500)),
        SttSegment("g4", "That sounds great, could you send over a pricing breakdown?", 16000, 19500, _make_words("That sounds great, could you send over a pricing breakdown?", 16000, 19500)),
        SttSegment("g5", "Certainly. I will send you the detailed pricing proposal by Friday afternoon.", 21000, 26000, _make_words("Certainly. I will send you the detailed pricing proposal by Friday afternoon.", 21000, 26000)),
        SttSegment("g6", "Perfect, thank you Alex. Have a great day.", 27500, 30500, _make_words("Perfect, thank you Alex. Have a great day.", 27500, 30500)),
        SttSegment("g7", "Thank you for your time, have a wonderful day.", 32000, 35000, _make_words("Thank you for your time, have a wonderful day.", 32000, 35000)),
    ]
    raw = gzip.compress(json.dumps({"scenario": "green_call"}).encode("utf-8"))
    return SttResult(segments=segments, language="en", duration_sec=35.0, raw_payload=raw)

def make_red_call_stt_result() -> SttResult:
    """Hostile, rude sales representative call. Expected verdict: RED."""
    segments = [
        SttSegment("r1", "Yeah, what do you want?", 0, 2500, _make_words("Yeah, what do you want?", 0, 2500)),
        SttSegment("r2", "Hello, I am calling because my invoice seems higher than quoted.", 4000, 8000, _make_words("Hello, I am calling because my invoice seems higher than quoted.", 4000, 8000)),
        SttSegment("r3", "Are you kidding me? Shut up and look at the contract terms.", 9500, 14000, _make_words("Are you kidding me? Shut up and look at the contract terms.", 9500, 14000)),
        SttSegment("r4", "Excuse me? That is completely unacceptable behavior.", 15500, 18500, _make_words("Excuse me? That is completely unacceptable behavior.", 15500, 18500)),
        SttSegment("r5", "That is ridiculous, not my problem whatever you know.", 20000, 24500, _make_words("That is ridiculous, not my problem whatever you know.", 20000, 24500)),
        SttSegment("r6", "I want to speak with your manager immediately.", 26000, 29000, _make_words("I want to speak with your manager immediately.", 26000, 29000)),
        SttSegment("r7", "Bro I don't care, talk to whoever you want.", 30500, 34500, _make_words("Bro I don't care, talk to whoever you want.", 30500, 34500)),
    ]
    raw = gzip.compress(json.dumps({"scenario": "red_call"}).encode("utf-8"))
    return SttResult(segments=segments, language="en", duration_sec=35.0, raw_payload=raw)

def make_customer_anger_immunity_stt_result() -> SttResult:
    """
    CRITICAL REQUIREMENT: Customer is aggressive, profane, and hostile.
    Sales representative remains calm, polite, and de-escalates.
    Expected Rep Verdict: GREEN / NOT RED.
    """
    segments = [
        # Rep (Speaker A)
        SttSegment("ca1", "Thank you for calling customer support, my name is David. How can I help you?", 0, 4500, _make_words("Thank you for calling customer support, my name is David. How can I help you?", 0, 4500)),
        # Customer (Speaker B) - extremely hostile
        SttSegment("ca2", "Your software is complete garbage and you people are total idiots!", 6000, 11000, _make_words("Your software is complete garbage and you people are total idiots!", 6000, 11000)),
        # Rep (Speaker A) - calm and empathetic
        SttSegment("ca3", "I sincerely apologize for the frustration this caused. I understand how critical this downtime is.", 12500, 18500, _make_words("I sincerely apologize for the frustration this caused. I understand how critical this downtime is.", 12500, 18500)),
        # Customer (Speaker B) - screaming & angry
        SttSegment("ca4", "Shut up with your corporate excuses! Fix it right now or I am suing your company!", 20000, 25500, _make_words("Shut up with your corporate excuses! Fix it right now or I am suing your company!", 20000, 25500)),
        # Rep (Speaker A) - professional commitment
        SttSegment("ca5", "I understand sir. I will personally escalate your ticket to our senior engineering lead and email you an update by 2 PM today.", 27000, 35000, _make_words("I understand sir. I will personally escalate your ticket to our senior engineering lead and email you an update by 2 PM today.", 27000, 35000)),
        # Customer (Speaker B)
        SttSegment("ca6", "Fine. You better do it.", 36500, 39000, _make_words("Fine. You better do it.", 36500, 39000)),
        # Rep (Speaker A)
        SttSegment("ca7", "Thank you for your patience, we are on it immediately.", 40500, 44000, _make_words("Thank you for your patience, we are on it immediately.", 40500, 44000)),
    ]
    raw = gzip.compress(json.dumps({"scenario": "customer_anger_immunity"}).encode("utf-8"))
    return SttResult(segments=segments, language="en", duration_sec=44.0, raw_payload=raw)

def make_short_duration_stt_result() -> SttResult:
    """Representative speaks for under 15 seconds. Expected confidence: low / NEEDS_REVIEW."""
    segments = [
        SttSegment("s1", "Hello, who is this?", 0, 2500, _make_words("Hello, who is this?", 0, 2500)),
        SttSegment("s2", "Wrong number, sorry.", 4000, 6000, _make_words("Wrong number, sorry.", 4000, 6000)),
    ]
    raw = gzip.compress(json.dumps({"scenario": "short_call"}).encode("utf-8"))
    return SttResult(segments=segments, language="en", duration_sec=6.0, raw_payload=raw)

def make_multi_commitment_stt_result() -> SttResult:
    """Call containing explicit commitments, follow-ups, and deliverables with distinct deadlines."""
    segments = [
        SttSegment("mc1", "Hi Sarah, thank you for your time on our product demo.", 0, 3500, _make_words("Hi Sarah, thank you for your time on our product demo.", 0, 3500)),
        SttSegment("mc2", "Thanks Alex. I will talk to Frederick next week about the approval.", 5000, 9500, _make_words("Thanks Alex. I will talk to Frederick next week about the approval.", 5000, 9500)),
        SttSegment("mc3", "Sounds great. I will send you the API technical documentation by tomorrow at 5 PM.", 11000, 16500, _make_words("Sounds great. I will send you the API technical documentation by tomorrow at 5 PM.", 11000, 16500)),
        SttSegment("mc4", "Could you also check on the volume discount structure?", 18000, 21500, _make_words("Could you also check on the volume discount structure?", 18000, 21500)),
        SttSegment("mc5", "Yes, I will follow up with our finance team by Friday to see if we can offer ten percent.", 23000, 29000, _make_words("Yes, I will follow up with our finance team by Friday to see if we can offer ten percent.", 23000, 29000)),
    ]
    raw = gzip.compress(json.dumps({"scenario": "multi_commitment"}).encode("utf-8"))
    return SttResult(segments=segments, language="en", duration_sec=30.0, raw_payload=raw)
