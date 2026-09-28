# Step 1 verification

Checked on Windows with Python 3.14.6, local Ollama, and installed `llama3.1:latest`.

- Eight automated tests pass: evidence rejection, assistant/user provenance separation, missing evidence handling, grounded corrections, SQLite persistence, invalid-response atomicity, model restrictions, and project isolation.
- JavaScript syntax and Python compilation checks pass.
- Live Ollama discovery accepted six grounded fields from the dog-matching example. An unsupported monetization guess was excluded and reported in the UI.
- The browser displayed the real assistant response and six populated profile areas. Reload restored the conversation and profile.
- HTTP root responds successfully with a content security policy. API requests without the local session token, with an external Origin, or with an unexpected Host receive 403.
- Forty source entries are registered: all entries from Text.txt, splitting Infisical and Doppler, plus Civitai, Paddle, and DuckDuckGo from the original product brief. All connectors remain planned.

Issues found and fixed: SQLite connections were not closing promptly on Windows; one unsupported model field caused the entire response to fail; stale development servers could share a port. Connections now close explicitly, unsupported fields are skipped, and the server claims its port exclusively.

This verifies the discovery foundation, not production security, model accuracy across languages, source research, or final recommendation quality. Those have separate gates in the roadmap. Exact quote matching supports provenance but still requires user review of the interpretation.

The distributed ZIP excludes local conversations, databases, caches, and model weights. The working checkout retains a synthetic example project so the local preview demonstrates the flow.
