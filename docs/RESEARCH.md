# Ollama-directed research and dossier contract

Research is performed at application runtime. Maintainer-authored catalog records are starting references; they are not substitutes for runtime searches, and opening the source library does not execute a query.

## Request flow

1. The bundled scope policy and local Ollama domain checker accept a software-related request.
2. A bundled local intent classifier plus explicit rules route product plans, requirement changes, explanations, debugging and ordinary in-domain chat. Ollama extracts fields with exact user-message quotes; the decision engine uses those literal excerpts, preserving their negations and units. A bounded literal recovery fills obvious omitted facts, and corrections replace or append sourced requirements according to the user's wording.
3. The catalog rule engine filters incompatible combinations and exposes product capabilities and constraints. These limit available research categories, separating B3 stocks from cryptocurrencies and ASR from chat/coding models.
4. Ollama creates a structured `tasks` plan: public source, topic and catalog documentation ID. It chooses the calls; Python validates and executes them. If an explicit capability was omitted, Ollama gets a focused planning retry. For B3 data and booking, an empty first search can trigger an Ollama-selected broader query from a fixed public list. At most four calls execute per turn.
5. Local connectors return actual source results and a trace containing query, success/empty/failure status and result count. Failures are never converted into invented findings.
6. Ollama selects up to four returned resource IDs. Code derives each resource type, requirement topic and exact source excerpt from the fetched record, then checks platform, relevance, source quality and explicit user constraints. At most one recommendation per topic is shown. A focused Ollama selection may cover an explicit capability the first selection missed. Invalid IDs and incompatible results are discarded. A quoted source establishes provenance, not verified production fitness.
7. Ollama chooses a compatible stack ID and typed decision priority. Code composes the explanation from known stack members rather than accepting unsupported prose about costs or capabilities. Invalid choices use a visibly identified local ranking fallback. Explanations and debugging use the current dossier as context without rerunning research.
8. The software assembles and atomically saves a structured dossier, then opens its on-page view. Prompts carry the product brief, confirmed notes, stack, source URLs, returned resources and known integration restrictions.

## Network contract

Only predefined public search strings and bundled HTTPS documentation URLs leave the machine. There is no arbitrary URL or unrestricted free-text query parameter. The full product description, conversation and notes go only to local Ollama.

- GitHub: anonymous repository-search API, up to five results per call. Stars order discovery; they do not prove suitability. Anonymous quota failures are reported.
- Hugging Face: public model metadata API, up to five results. Returned metadata is not a benchmark, model download or license approval.
- public-apis/free-for-dev: retrieve the public README and return up to five topic-matching linked entries. No matching entries means an empty result, not unrelated fallback text. Listing a provider does not establish its current pricing or eligibility.
- UI: retrieve one public page from 21st.dev, Mobbin or Uiverse. This is bounded page retrieval, not authenticated access or full catalog search. Redirects/login/unsupported pages can fail visibly.
- Vendor documentation: retrieve only a URL belonging to a bundled tool record. A fetched page is not automatically a pricing verification. Paywalled/authenticated content is unsupported.

Each fetch has a 12-second timeout, a 750 KB body limit and no redirect following. Model calls have their own bounded timeouts. The bounded planning/selection retries above are visible in the dossier trace; no hidden background searches run. Data remains in the project's local dossier; no external database or analytics receives it.

## Decision scope

The initial catalog has nine combinations: content website, individual web dashboard, managed web service, web app with server rendering, managed mobile app, local mobile app, local desktop app, Python CLI and a simple browser-only utility. These are candidate starting points, not universal solutions.

Platform, offline needs and account requirements cannot be overridden by model preference. PostgreSQL/pgvector is added only for explicit vector/RAG requirements. Personal prototypes do not automatically need hosted auth, and free hosting is not assumed to be appropriate for a commercial product. Missing geography, costs and access approval remain pending.

`research.mode=local-reviewed-catalog` describes catalog provenance. `live_research` contains this turn's real calls and results. A dossier produced offline does not claim fresh research. `decision.driver` distinguishes `ollama` selection from `local-rules` fallback.

This MVP uses Ollama structured JSON orchestration plus two bundled local text classifiers. It does not install Laya, fine-tune the generative model, use native unrestricted tool execution, LangChain or vector RAG. Downloaders already receive the trained classifier artifacts, policy, catalog and orchestration code; there is no per-user training step.
