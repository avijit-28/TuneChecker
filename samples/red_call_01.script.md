# Sample Call 01: RED (Hostile / Dismissive Rep)

**Call ID:** sample-red-01  
**Audio File:** `samples/red_call_01.m4a`  
**Expected Verdict:** RED  
**Rep Speaker:** Speaker 0 (Microsoft David Desktop)  
**Customer Speaker:** Speaker 1 (Microsoft Zira Desktop)  

---

### Script & Utterances

- **[00:00 - 00:05] Rep (Speaker 0):** Hello, thanks for taking my call today. Let's get right into the contract.
- **[00:05 - 00:12] Customer (Speaker 1):** Hi David, thanks for calling. We reviewed your initial proposal, but the pricing feels quite high for our team size.
- **[00:12 - 00:23] Rep (Speaker 0):** Look, if you can't afford our standard enterprise pricing, you're frankly wasting both of our time. We don't give handouts to small shops.
- **[00:23 - 00:30] Customer (Speaker 1):** That's quite an aggressive response. We just wanted to see if there's any flexibility on implementation fees.
- **[00:30 - 00:41] Rep (Speaker 0):** Take it or leave it. I will email you the revised contract addendum by tomorrow at 5 PM, but the price is non-negotiable.
- **[00:41 - 00:48] Customer (Speaker 1):** Okay, please send that over, though we will likely need to evaluate other vendors.
- **[00:48 - 00:54] Rep (Speaker 0):** Fine. Maybe we could look into custom integrations next quarter, but don't count on it. Goodbye.

---

### Ground Truth Expectations

- **Rep Tone:** RED
- **Violations Identified:**
  - Aggressive and dismissive language ("wasting both of our time", "handouts to small shops", "Take it or leave it").
  - Lack of empathy or professional objection handling.
- **Evidence Quotes (Verbatim):**
  - "Look, if you can't afford our standard enterprise pricing, you're frankly wasting both of our time. We don't give handouts to small shops."
  - "Take it or leave it."
- **Action Items:**
  - Item 1: "email you the revised contract addendum" | Owner: Rep (David) | Deadline: "tomorrow at 5 PM" | Explicit: Yes
  - Hypothetical mention ("look into custom integrations next quarter, but don't count on it") must NOT be an action item (or flagged as non-committal).
