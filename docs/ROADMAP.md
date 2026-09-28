# Complete implementation roadmap

## Product commitment

An open-source, local-first software architect for vibecoders. Users explain a product in a desktop or local-browser chat connected to Ollama. The software discovers requirements, uses a decision model such as Laya, researches relevant tools, verifies evidence, selects compatible stacks, and exports a Project Architecture Dossier plus ordered prompts for AI coding tools.

Local inference and storage are the default. Connected research necessarily contacts remote sources. Free local inference means no per-token hosted-model fee; hardware, electricity, third-party API usage, and the user's eventual deployed application may still cost money.

Every step below includes a delivery gate. Completion requires implementation and validation, not just documentation. Current status: **Step 1 implemented; research/dossier MVP covers parts of steps 2–7 and 10–11**. The full gates remain open: Laya, semantic retrieval, exhaustive catalog matching, verified pricing/payment routing and external-model benchmarking are not implemented.

The current runtime uses Ollama to plan public searches, select returned resources and choose among nine compatible initial stacks from a 25-tool catalog. Two local trained classifiers signal domain and chat intent; requirement correction and capability matching have explicit rules. It opens a dossier with source traces and four contextual prompts. Forty hubs are registered; seven entries have public connectors. UI connectors retrieve bounded pages rather than search the complete sites. See [the implemented contract](RESEARCH.md) for exact scope and [the README](../README.md) to run it.

## 1. Local chat and structured discovery — implemented

Deliver a runnable local interface and Python backend. Detect installed Ollama chat models; reject known cloud entries. Gather product scope, audience, platform, essential features, monetization, business/user geography, technical comfort, expected usage, privacy, integrations, and separate cost constraints.

Persist projects and conversations in SQLite. Store missing requirements as null; distinguish explicit facts from later inferred requirements. Support user corrections. Require exact user-message evidence for extracted facts. Export the discovery profile as versioned JSON. Show progress as coverage, never as a guarantee of readiness.

Gate: local chat works with installed Ollama; saved projects survive reload; invalid model output does not corrupt previous state; grounded corrections update the profile; offline status is actionable. The later dossier MVP adds provisional architecture recommendations without declaring the remaining roadmap complete.

## 2. Decision schema and dual-brain integration

Introduce a decision adapter with interchangeable Laya and Ollama implementations. Ollama handles conversation, open-ended extraction, explanation, and final prompt composition. Laya answers focused typed questions about platform, feature requirements, real-time behavior, privacy, UI complexity, cost categories, and relevant source categories.

Use compact, provenance-bearing project context, language-aware checkpoint selection, and explicit unknown/undecided choices. Retain the user's own facts as authoritative. Keep evidence-confidence metadata separate from ranking scores. Calibrate abstention on domain examples; do not invent universal confidence thresholds or promise millisecond latency on every laptop. Ollama models are user-selectable: Llama and Mistral are examples, not permanent recommendations. Keep orchestration explicit in Python initially; evaluate LangChain or LlamaIndex later against concrete retrieval/integration needs rather than installing both by default.

Gate: compare classifiers on annotated English and multilingual project cases, ambiguous budgets, changing requirements, and conflicting statements. Measure accuracy, abstention, RAM, and latency on CPU and available GPU hardware. Keep Laya only where evidence shows a benefit; falling back to Ollama must be visible.

## 3. Unified tool catalog and complete source registry

Represent tools separately from their discovery locations. Model tools, services, repositories, APIs, datasets, models, UI assets, templates, prompts, workflow platforms, security guidance, and payment providers as distinct resource types.

Each record includes canonical identity, source URLs, capabilities, limitations, deployment mode, license, setup complexity, supported platforms, integration constraints, hardware requirements where relevant, pricing/quotas, currency, geography, verification date, and evidence excerpts. Deduplicate across directories. Maintain compatibility relationships and source-specific confidence.

All hubs from Text.txt are already registered in `hubs.json`. Some names are ambiguous: confirm exact identity before implementing their connectors. Merchant of record is a provider category, not a single search endpoint. Fabric needs repository identity confirmation. Interpret 'infiscal' provisionally as Infisical, retaining the supplied spelling in source provenance.

Gate: schema validation and migration work; duplicate sightings merge without losing evidence; stale/unknown facts remain visible; licenses and resource types are explicit.

## 4. Source connectors and autonomous web research

Implement one connector contract: availability, search, fetch, normalize, and provenance. Connectors run locally and use documented APIs or permitted page retrieval. Check access requirements, terms, robots rules where applicable, and licensing individually. Never imply a source is searchable merely because it appears in the registry.

Initial connector priority: GitHub, Hugging Face, public-apis, free-for-dev, one UI source, OWASP, and vendor documentation. Then add the full remaining registry by category:

- AI discovery: TAAFT, Toolify, FutureTools, Product Hunt.
- Models/data/research: Hugging Face, Kaggle, ModelScope, Papers with Code (verify current availability before integration).
- Design/components: Figma Community, Mobbin, 21st.dev, Uiverse.
- API/service discovery: public-apis repository, free-for-dev, Free API, PublicAPIs, RapidAPI Hub, Postman Public API Network.
- Workflows/prompts/integrations: Composio, LangChain Hub, Dify, Coze, Flowise, Langflow, PromptBase, Fabric, Make.
- Security: OWASP, Snyk, GitHub Security Advisories, Infisical, Doppler, Lakera Guard.
- Payment research: Stripe and explicitly identified merchant-of-record providers.
- Collection infrastructure: Apify as an optional provider, with clear network and cost implications.

Also include Civitai from the original product brief as a later model/asset source, with license and content suitability checks. Evaluate a search provider such as DuckDuckGo only through an appropriate supported access method; it is separate from Ollama inference and hub-specific APIs.

Route searches by task instead of querying every hub for every message. Use an initial candidate pass, then targeted research for missing facts. Cache results, enforce time/request budgets, support cancellation and rate limits, and report skipped/unavailable sources. Local HTTP fetching can be free; hosted search or scraping APIs may not be.

Keep private chat local. Generate minimized search terms, show the network mode, and require deliberate opt-in for sensitive queries. Treat fetched content as untrusted data, never as instructions. Block private-network fetch destinations, limit redirects/body sizes, redact secrets from logs, and prevent scraped pages from initiating arbitrary tool actions.

Gate: real connectors have repeatable integration checks, bounded requests, provenance, rate-limit recovery, clear credential requirements, and honest availability reporting. No blind mass scraping.

## 5. Local retrieval and vetted architectural knowledge

Separate structured catalog facts, retrieved documents, conversation memory, and versioned rules. Start with SQLite filtering/full-text search. Add local embeddings and a supported ChromaDB or FAISS adapter when semantic retrieval improves measured recall. Track embedding model/version and rebuild indexes when necessary.

Load reviewed architecture guidance covering frontend/backend boundaries, simple hosting, serverless limitations, relational data, state, queues, real-time systems, and RAG. Refresh volatile pricing independently of stable guidance. A vector index retrieves relevant text; it never substitutes for rule enforcement.

Gate: retrieval benchmarks show relevant evidence; stale sources are identified; facts do not become authoritative merely because they are embedded; offline cached operation works.

## 6. Constraint filtering, compatible-stack ranking, and explanations

Define hard constraints before preferences: offline/local requirements, license rights, essential capabilities, geography/provider eligibility, available hardware, and budget boundaries. Reject incompatible candidates. Unknown hard-constraint facts require research or an explicit provisional recommendation.

Rank viable complete stacks across feature fit, ease of setup, expected total cost, maintenance, security evidence, integration fit, and portability. Version and expose ranking weights; adapt priorities to user experience and budget. Use popularity only as one supporting signal. Do not favor any provider because it was named in an example.

Evaluate combinations: a good database and good frontend may still make a poor stack. Penalize redundant services, unnecessary AI, and unneeded infrastructure. Recommend relational storage or vector search only when requirements justify them. Give a primary stack and credible alternative with evidence, tradeoffs, and rejected options. Handle unsatisfiable constraints honestly.

Gate: deterministic ranking is reproducible; constraint violations cannot win by a high preference score; small changes in irrelevant popularity do not change the recommendation; user overrides trigger recomputation.

## 7. Security and authentication guardrails

Apply versioned executable rules, informed by OWASP and relevant vendor guidance. Cover managed authentication options, authorization, tenant isolation, server-only credentials, environment configuration, OS keychain storage for local connector credentials, secret managers where justified, upload validation, rate limits, abuse controls, dependency/advisory checks, and backup/recovery.

Consider Cloudflare/DDoS protection when the deployment benefits from it. Avoid unconditional vendor mandates. Include OAuth flows, redirect configuration, least privilege, webhook signature verification, and public-vs-secret key distinctions. Guidance cannot block unsafe code in an external editor; enforcement there requires later integrations or checks.

Gate: deliberately unsafe architecture examples are flagged, recommended prompts contain the relevant protections, and no credential is included in generated artifacts or logs.

## 8. Payment and monetization decision pipeline

Distinguish a payment processor from a merchant-of-record arrangement. Collect business country, customer geography, product type, currency, subscription/one-time needs, marketplace/seller structure, and who assumes relevant obligations. Compare eligible providers such as Stripe and Paddle using current official sources and their actual service arrangements. Include regional instant transfers such as Pix when appropriate, alongside global alternatives.

Output checkout, server-side fulfillment, verified and idempotent webhooks, subscriptions, refunds/cancellations, and entitlement management. Mark tax/legal questions needing qualified review rather than promising legal coverage. Record fees and projections with explicit dates, assumptions, and unknowns.

Gate: a provider cannot be recommended without checking required eligibility; payment confirmation cannot rely solely on a client redirect; tests cover duplicate events and failed payments.

## 9. Coding-tool and language-model recommendations

Maintain an updateable model/tool capability catalog rather than hardcoded legacy model names. Include coding, UI, reasoning, context, vision, tool use, availability in Cursor/Claude/v0 or other editors, costs, privacy, local hardware fit, and dated evaluation evidence.

Recommend per task when useful, but account for the user's existing subscriptions and switching friction. External model use is a user choice; the architect itself stays local. Benchmark claims must have provenance and cannot establish a universally best model.

Gate: recommendations explain task fit and costs; unavailable/stale models are not presented as current; a local-only preference is respected.

## 10. Project Architecture Dossier

Generate a structured canonical document first, then render readable exports. Include executive brief, confirmed requirements, assumptions/unknowns, categorized frontend/backend/database/cloud stack, alternatives and tradeoffs, system/data flow, entity relationships, integration plan, security/auth checklist, payment pipeline, deployment instructions, and staged implementation milestones.

Cost projections include free-tier limits, usage scenarios, recurring vs usage charges, currency, date checked, and upgrade triggers. Never equate a free hosting tier with a zero-cost product. Attach sources to material claims. Support Markdown/JSON first; add visually verified PDF export later if useful.

Gate: every recommendation traces to requirements and evidence; no invented pricing; dossier and JSON agree; unresolved decisions are clearly labeled.

## 11. Ready-to-use engineering prompt deck

Generate ordered, copy-paste prompts tailored to selected tools and stack: project setup, database schema/migrations, authorization, interface design/components, APIs/integrations, AI matching or RAG where justified, payment flows, testing, deployment, and security review.

Each prompt includes exact task context, prerequisites, constraints, expected changes, acceptance criteria, and validation commands where appropriate. Carry architecture decisions consistently across prompts; keep secrets as placeholders; reference licensed UI assets properly. External tools require the user to supply files/context that they cannot access automatically.

Gate: prompts build incrementally without contradicting the dossier; representative projects can be scaffolded from them and reviewed against acceptance criteria.

## 12. End-to-end quality, packaging, and open-source release

Evaluate representative products including dog matching, SaaS dashboards, mobile apps, local tools, automation, AI-heavy apps, and marketplaces across languages and budgets. Measure unsupported claims, unsafe choices, source coverage, ranking stability, privacy leakage, latency, RAM, and research cost.

Add a reproducible dependency lock when dependencies are introduced, CI, supported-platform installation instructions, first-run diagnostics, data export/deletion controls, accessible UI, contribution guidelines, connector documentation, license attribution, and a threat model. Package a desktop shell if it improves setup while preserving local-browser access. Do not require paid research providers to use the core offline product.

Gate: a new user can install, discover, research, compare, export a dossier, and follow its prompts; offline and connected modes have accurate privacy claims. Review release artifacts and third-party redistribution rights before publication.

## Architecture contracts to preserve

`ProjectProfile -> DecisionAdapter -> ResearchPlan -> SourceConnectors -> EvidenceCatalog -> ConstraintEngine -> StackRanker -> Dossier -> PromptDeck`

Ollama currently understands, directs searches, selects resources and makes typed architecture decisions. Laya remains an optional future classifier adapter. Ordinary code enforces compatibility, computes fallback rankings and renders the dossier. Sources supply evidence. User corrections trigger recomputation.

## Technical references

- Ollama structured output: https://docs.ollama.com/capabilities/structured-outputs
- Ollama privacy/local mode: https://docs.ollama.com/faq
- Laya checkpoints and typed decisions: https://github.com/NandhaKishorM/laya
- GitHub source search: https://docs.github.com/en/rest/search/search
- Hugging Face API access: https://huggingface.co/docs/hub/api

These links informed the initial design. Connector implementation must recheck current access, pricing, and API contracts.
