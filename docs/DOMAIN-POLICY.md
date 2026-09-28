# Software-only chat, enabled by default

Phase 0 is for software creation and vibecoding: apps, websites, games, automations,
architecture, UI/UX, coding prompts, APIs, databases, auth, security, testing,
debugging, deployment and product requirements. Ordinary conversation and domain
advice unrelated to building software are outside its scope.

The repository already contains:

- `phase0/policy/scope-model.json`: a trained, dependency-free text classifier.
- `phase0/policy/intent-model.json`: a trained local classifier for plan, refine, explain, debug and chat routing.
- `phase0/policy/scope-policy.json`: the versioned input, generation and output policy.
- `phase0/scope.py`: server-side enforcement, including direct role-change redirects.
- `training/scope-data.json`, `train_scope.py` and `evaluation.json`: inspectable data,
  optional maintainer training and evaluation results.

Normal installation does **not** train anything, create an Ollama Modelfile or ask users
to configure a system prompt. Install Python and a supported local Ollama chat model,
then run `python -m phase0.server`. The server loads the bundled scope model and policy.
No extra ML package, remote inference, API key or hosted guard service is required.

## Enforcement

1. Direct requests to override the role are redirected with a fixed software-focused
   reply. A greeting opens software discovery rather than general chat.
2. A trained multinomial Naive Bayes classifier extracts word and word-bigram features
   from the new message. Its score is a **hint**, never authority to release a reply.
3. A local Ollama semantic checker decides `allow`, `redirect` or `clarify`, considering
   the actual action, software notes and recent context. It distinguishes a recipe app
   from a recipe, and software finance integrations from investment advice. Mixed
   unrelated tasks are redirected. Legitimate project-budget answers remain eligible.
4. Local intent routing distinguishes a new architecture dossier, an explicit requirement change, an explanation, debugging and ordinary software chat. It combines narrow explicit rules with a bundled multiclass classifier that can abstain. Explanations and debugging reuse the current dossier without mutating it or researching again.
5. Generation always receives the bundled specialist instruction. There is no public
   general-chat switch or client-controlled system prompt.
6. A second structured local check reviews conversational text for domain fit and relevance.
   Rejected candidates are not displayed, persisted or allowed to change project notes.
   Dossier planning also validates extracted facts, constrains research calls and accepts
   only compatible typed stack choices. Dossier template text uses catalog facts;
   resource explanations use typed purposes, and the assembled text receives the domain check.
7. Refused/clarifying turns carry a stored scope status and are excluded from subsequent
   generation history. Existing database conversations are preserved as legacy entries.

If the checker returns invalid JSON or a bundled asset is absent, the system asks a
software-focused clarification. A local inference outage reports an error without saving
the pending turn. It never falls back to unrestricted generation. Refused user messages
are retained in local conversation history for transparency; they are not training data.

## ML scope and limitations

This is actual supervised ML for domain classification, **not** fine-tuning the generative
Ollama model or installing Laya. It cannot make a generic LLM understand every project or
guarantee zero hallucinations. The small classifier was trained on 128 authored synthetic
Portuguese/English examples and got 25 of 32 separately held-out synthetic examples right:
16/16 software, 9/16 outside. The seven false accepts are why ML alone never authorizes a
response. These numbers do not measure real-world safety or multilingual performance.
The evaluation examples were not used for training.

The separate intent classifier is trained on 120 authored synthetic PT/EN examples and evaluated on 40 held-out examples. It made 20 direct correct decisions and abstained on 20; explicit routing rules plus the model matched 38 of 40 held-out labels. These are a small authored evaluation, not a real-world accuracy estimate. See `training/intent-evaluation.json` and `training/intent-data.json`; neither training nor user-conversation collection is required at install time.

The semantic checks can also misclassify ambiguous or adversarial language, especially
with weaker local models. They add inference time. Domain controls reduce drift; they do
not prove an absolute "never" guarantee or validate every technical factual claim. They
are not a harmful-content classifier. Open-source owners can edit the source and policy;
the original repository ships these restrictions on by default.

Future work: broader independently labeled examples, contextual classifier training,
held-out adversarial evaluations across supported models and deeper retrieval evaluation.
User conversations are not collected or used for automatic training.

## Maintainer reproduction

```powershell
python training/train_scope.py
python -m unittest discover -s tests -v
```

The generated artifact is deterministic, versioned and tied to the dataset SHA-256.
Training is optional maintainer work; distributable releases must include the weights.

Algorithm reference: [multinomial Naive Bayes documentation](https://scikit-learn.org/stable/modules/naive_bayes.html).
The implementation uses the Python standard library rather than importing scikit-learn.
The local semantic checks use [Ollama structured outputs](https://ollama.com/blog/structured-outputs).
