# Quality improvements — 2026-09-28

107 automated tests pass. Real local Ollama replays covered a complete 13-turn, nine-product set and focused cases. Changes include a bundled trained chat-intent classifier, quote-grounded corrections, local browser and CLI stacks, bounded Ollama-directed research of explicit capabilities, and concise answer-only chat for comparisons/debugging. The latest Pulse replay preserved the dossier on questions, removed stale integrations after a correction, and redirected an off-topic recipe. Android selected Flutter + SQLite without remote database research; CSV automation selected Python CLI and recognized file processing. Research now gets source-grounded types and excerpts, checks platform/domain/source quality, and can ask Ollama for a bounded alternative public search. Ollama searched B3 stock-data sources but found no evidence-backed provider, which remains an explicit gap. See the [dated evaluation report](../../quality-evaluation-2026-09-28/REPORT.md) for traces and limits.

The release archive was rebuilt and smoke-tested after these changes; it includes both bundled classifiers and the 25-tool catalog, starts with empty project data, and requires no training at install time.

---

# Research and dossier MVP verification — 2026-09-26

52 automated tests passed. JavaScript syntax and Python compilation passed. Tests cover personal dashboards versus content sites, mobile/platform filtering, offline RAG dependencies, impossible combinations, commercial-hosting restrictions, short requirement corrections, compatible typed Ollama choices, grounded resource IDs/excerpts, bounded/duplicate calls, offline research, unavailable sources, atomic dossier persistence, refusal preservation and semantic fact checks.

HTTP checks returned 403 for a missing token, foreign Origin and invalid Host; the page supplied its CSP. The API returned 40 registered sources, seven active hub entries and 23 catalog tools.

Real development checks used local `llama3.1:latest` with synthetic projects and an isolated data directory. The application itself generated and executed the research plans:

- Personal Pulse dashboard: public-apis queries for Strava, Valorant and crypto market data. Ollama selected the compatible individual stack with React/TypeScript/Vite, FastAPI and SQLite. No vector database or product AI was added. Typed explanations included the actual database and did not promise a monthly cost.
- Institutional content site: GitHub queries for UI components and static websites/SEO. Ollama selected Astro with Cloudflare Pages rather than the dashboard stack. Some selections were discarded for lacking acceptable type/evidence; empty recommendations stayed empty rather than being invented.

The final two direct-store runs took approximately 47.5 and 46.1 seconds on this machine. These are development timings, not hardware-independent promises. They are not independent accuracy or market-quality evaluations.

Browser checks used port 8766 and separate project storage. Sending a detailed product description opened the dossier automatically. The screen showed the model-directed query trace, selected stack, limitations and four prompts. Prompt copying returned “Copiado.”; JSON export included the stack, Ollama decision driver, three research calls and four prompts. Activating the Dossier tab again returned to chat. The source library distinguished active GitHub search from planned GitHub advisories and filtered two of 40 records. No modal dialog was present.

Failures found during development and addressed:

- Dashboard searches for a simple institutional site: constrain topics from the understood product and remove irrelevant source categories.
- “Cheap” converted to zero budget: exact-quote and semantic fact review, bounded repair, explicit unknown costs, and no free-form price explanation in stack decisions.
- A database omitted from the model's prose: accept a typed stack ID/priority and compose the explanation from actual members.
- Game assets presented as a player-rank source: discard entries without player/rank/statistics evidence for that use.
- Market queries matching marketing email, blockchain anchoring or a study timer: word-boundary/topic filters, price/rate evidence for crypto quote discovery, typed resource purposes and duplicate selection rejection.
- Beginner experience interpreted as project scale, or no-AI interpreted as public privacy: reject quotes unrelated to those fields before semantic review.

Quote matching proves provenance, not complete correctness. Semantic extraction may still omit or reject real requirements. Returned repository descriptions and directory entries do not establish production fitness or provider eligibility. Costs, prices, geographic payment routing and commercial model rankings remain unverified. The complete scope is in [RESEARCH.md](RESEARCH.md).

---

## Historical verification from earlier releases

# Verification — 2026-09-26

## Software-only domain release

27 automated tests passed after adding the bundled trained scope classifier and policy.
Tests cover direct role overrides, input denial before generation, invalid checker output,
an inference outage, rejection of unrelated generated text without persistence or profile
updates, relevant output acceptance, legacy database migration and asset failures.

With local `llama3.1:latest`, 22 regression cases passed: 18 request decisions and four
candidate-output reviews. They include recipe app vs cooking instructions, finance widget
vs investment advice, fitness app vs workout plan, budget and experience follow-ups,
software debugging, mixed unrelated requests and prompt-injection defense. Two initial
false rejections were corrected before the final pass. This is a small development test
suite, not independent security certification or a guarantee across every model.

Browser check: a request to build a recipe web app was accepted and collected four facts.
A subsequent request for an actual cake recipe was redirected, preserving those facts.
Returning to a construction-tool question stayed in the software workflow.

The release ZIP was extracted into an isolated directory. A fresh Python process loaded
the included trained classifier and domain policy without running a training step.

The standalone ML evaluation remains 25/32 on held-out authored examples. See
[the complete policy, installation behavior and limitations](DOMAIN-POLICY.md).

## Earlier discovery/frontend checks

14 automated tests passed. JavaScript syntax and HTTP security boundaries passed:
missing token, foreign Origin and invalid Host returned 403; the page sent its CSP.

Browser tests used a separate local server/data directory, preserving user projects:
- Create a project, converse with local llama3.1:latest, reload and restore conversation.
- Inspect source evidence; export JSON downloaded with schema version 1, discovery stage,
  six messages and corrected budget from the synthetic agenda project.
- Open/close the inline model picker; open source library and filter GitHub (2 of 40 sources).
- Reproduce the Pulse tool question. It now returns provisional construction guidance,
  separates named integrations from the stack, and does not assert unverified API access.

Problems found and changes:
- Invalid evidence blocked a real budget correction. Added one bounded extraction repair,
  with identical provenance validation. Repair failures preserve valid original facts.
  Live retest accepted the updated amount and geography. Interpretation still needs review:
  the model shortened the displayed budget; the evidence retained the monthly period.
- Conversation echoed tool questions and confused integrations with construction tools.
  Added inspectable Portuguese/English intent rules and short-confirmation handling,
  plus a small provisional catalog using official Vite, FastAPI and SQLite documentation.
- Strengthened discovery instructions against invented audiences, repeated questions and
  unsupported API claims. The final live Pulse check asked about platform and passed the
  construction-intent regression; extraction still omitted some explicitly named details.

Limitations: rules are not a trained classifier and do not cover every phrasing. This is
not Laya, fine-tuning, RAG or live hub ranking. The generative discovery reply can still
misinterpret facts. Exact quote validation establishes provenance, not semantic truth.
Broader cross-model evaluation and extraction completeness are still needed.

Reviewed source references:
- https://vite.dev/guide/
- https://fastapi.tiangolo.com/features/
- https://www.sqlite.org/whentouse.html


## Final release smoke check

The final UI run used a fresh synthetic Pulse project and current code. Ollama chose four public-apis calls: Strava, Valorant, crypto market data and a timer category. Three returned resources and the timer call was empty; research status was correctly partial. The shortlist contained Strava and crypto-rate candidates, excluding the game-item API from the player-rank recommendation. The dossier opened automatically and retained explicit unconfirmed facts. At the default 1280 px viewport the page had no horizontal overflow. A screenshot records this runtime result.

The distributable ZIP was extracted into an isolated directory. Its server booted with empty projects and the bundled 23-tool catalog, without a training step. The archive includes policy/model/catalog/research code and excludes SQLite data and Python cache files. The temporary smoke-check server was terminated.
