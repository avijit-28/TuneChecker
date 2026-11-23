# Sample Audio Test Calls

This directory contains representative test calls in `.m4a` format for evaluating the TuneChecker pipeline:

1. `red_call_01.m4a` (`samples/red_call_01.script.md`)
   - **Scenario:** Sales call with aggressive, dismissive representative behavior.
   - **Expected Tone:** RED
   - **Key Features:** Interruptions, condescending remarks, explicit action item with owner and deadline.

2. `green_call_01.m4a` (`samples/green_call_01.script.md`)
   - **Scenario:** Sales call with polite, consultative, empathetic representative behavior.
   - **Expected Tone:** GREEN
   - **Key Features:** Active listening, reassurance, commitment with unstated owner and vague deadline.

All sample files are generated locally via synthetic text-to-speech using standard Windows system voices (Microsoft David Desktop & Microsoft Zira Desktop) and encoded with FFmpeg AAC. Zero proprietary or cloud APIs were used.
