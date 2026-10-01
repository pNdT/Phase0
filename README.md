# Phase 0 — arquiteto de software local para vibecoding

O Phase 0 recebe a descrição de um software, site ou aplicativo, usa um modelo **local no Ollama** para entender os requisitos e escolher pesquisas públicas, compara ferramentas compatíveis e prepara um **dossiê de arquitetura** com fontes, restrições, segurança e quatro prompts para começar a construir. Esta é uma versão inicial funcional; recomendações, preços e licenças ainda precisam de verificação antes de tomar decisões reais.

## Instale e execute

1. Instale **Python 3.10 ou superior** e [Ollama](https://ollama.com/download). O projeto usa apenas a biblioteca padrão do Python; não precisa instalar pacotes com pip.
2. Instale um modelo de **conversa** no Ollama. Exemplo: `ollama pull llama3.1`. Confira com `ollama list`. O exemplo não é uma recomendação universal: escolha um modelo adequado à memória e à capacidade do seu computador. Os pesos não vêm neste repositório.
3. No GitHub, use **Code → Download ZIP** e extraia os arquivos, ou clone o projeto:

```powershell
git clone https://github.com/pNdT/Phase0.git
cd Phase0
python -m phase0.server
```

Se baixou o ZIP, abra um terminal dentro da pasta extraída antes de executar `python -m phase0.server`. No macOS/Linux, use `python3 -m phase0.server` se necessário. Se o Ollama não estiver rodando, inicie o aplicativo; em instalações que exigem um processo manual, use `ollama serve` em outro terminal. Abra **http://127.0.0.1:8765** no navegador. Mantenha o terminal do Phase 0 aberto durante o uso; encerre-o com `Ctrl+C`.

### Do primeiro projeto aos prompts

1. Verifique **Ollama connected**. Em **Local chat model**, escolha um modelo instalado. Se acabou de instalar um, clique em **Refresh connection**.
2. Clique em **+ New project** e dê um nome à ideia, se quiser. A primeira mensagem também pode criar o projeto automaticamente.
3. Na aba **Chat**, descreva o produto: público, plataforma (web/mobile/desktop), funções da primeira versão, integrações, orçamento, países do negócio e dos usuários, receita, privacidade, necessidade de rodar offline e sua experiência técnica. Envie com **Send message** ou `Ctrl+Enter`.
4. **Search public sources** vem marcado. Nessa modalidade, o Ollama escolhe consultas entre categorias públicas permitidas; conectores locais fazem buscas limitadas e devolvem resultados para o modelo selecionar. Desmarque antes de enviar para usar apenas o catálogo local e evitar chamadas aos conectores públicos naquela rodada. Uma pesquisa pode levar alguns minutos.
5. Uma descrição detalhada ou pedido de ferramentas gera o **Dossier** automaticamente. Confira **O produto que entendi**, a pesquisa realizada, a stack, alternativas e motivos de descarte, custos não verificados, segurança, integrações e decisões pendentes. Dados desconhecidos aparecem como hipóteses ou pendências.
6. Para corrigir o plano, use **Refine in chat** ou a aba **Chat** e explique a alteração: “Correção: é um site, não um app mobile; não quero login na primeira versão.” Mudanças de requisitos recalculam o dossiê. Perguntas explicativas podem receber resposta sem substituir o plano.
7. Use **Copiar prompt 1–4** para levar os prompts ao seu editor com IA. Se o navegador bloquear a área de transferência, o texto será selecionado para copiar com `Ctrl+C`.
8. Use **Export notes** para baixar `phase0-discovery.json` com os dados do projeto e **Export dossier** para baixar `phase0-dossier.json` com o plano. Os exports podem conter informação privada.

Exemplo de primeira mensagem:

> Quero criar um painel web chamado Pulse para consolidar atividades do Strava, cotações de cripto, sessões de foco e eventos. A primeira versão será de uso pessoal no Brasil, com orçamento baixo. Prefiro integrar serviços existentes. Quero saber quais APIs existem, quais dados exigem autenticação e qual stack simples permite crescer depois.

Os projetos salvos aparecem em **Your projects** e continuam disponíveis depois de fechar o navegador. **Project notes** mostra requisitos extraídos de trechos das suas mensagens; corrija-os pelo chat. A aba **Sources** lista os hubs cadastrados e seus estados. Abrir a lista **não** inicia uma pesquisa.

## O que sai do dossiê

O dossiê mostra o produto entendido e requisitos confirmados, uma trilha das pesquisas públicas dirigidas pelo Ollama, recomendações com evidência, stack inicial e alternativas, combinações rejeitadas, integração e pagamento condicionais, segurança/autenticação e quatro prompts contextuais. Diretórios, descrições de repositórios e metadados de modelos são pistas para investigar, não prova de adequação em produção.

O Python aplica restrições essenciais de plataforma, offline, contas, banco de dados e ferramentas obrigatórias antes de oferecer candidatos ao Ollama. O catálogo inicial contém **25 ferramentas** e **nove combinações de stack**. Os **40 hubs** fornecidos estão registrados; **sete entradas** têm conectores públicos ativos. Estar na aba Sources não significa que o hub inteiro é pesquisável. Veja o [contrato de pesquisa implementado](docs/RESEARCH.md).

## Acessar de qualquer lugar (Vercel)

Para usar o Phase 0 fora de casa sem deixar o computador ligado, publique-o na Vercel: o app roda na nuvem com **senha**, guarda os projetos num Postgres gerenciado (Neon ou Supabase) e usa um modelo na nuvem (Groq por padrão) no lugar do Ollama. Nesse modo, a descrição e o histórico do projeto são enviados ao provedor do modelo. Veja o [passo a passo](docs/DEPLOY-VERCEL.md).

## Dados locais e pesquisa pública

O servidor escuta apenas em `127.0.0.1`, acessa o Ollama em `http://127.0.0.1:11434` e salva conversas, notas e dossiês no SQLite em `data/phase0.sqlite3`. O banco **não é criptografado em repouso**. Não há conta Phase 0, analytics, CDN ou chave de API obrigatória para o aplicativo.

Com **Search public sources** marcado, os conectores enviam consultas públicas predefinidas ou acessam URLs fixas de documentação; **não** enviam a descrição completa, o histórico nem as notas. Os serviços externos recebem a consulta, a requisição e metadados de rede como seu IP. Desmarcar a opção impede chamadas desses conectores naquela rodada. Downloads de modelos e eventuais recursos de nuvem configurados no próprio Ollama têm condições de rede separadas. O Phase 0 não oferece configuração de URL para modelos remotos.

A pasta `data/`, arquivos SQLite, `.env` e caches ficam fora do Git. Proteja também os JSON exportados. Não exponha esse servidor de desenvolvimento à internet.

## Ajustes e solução de problemas

```powershell
# Porta local diferente
python -m phase0.server --port 8766

# Outra pasta para guardar phase0.sqlite3
python -m phase0.server --data-dir ../meus-dados-phase0
```

`--data-dir` indica a **pasta** do banco. A variável `PHASE0_DATA_DIR` também funciona; `--data-dir` tem prioridade. Ao trocar a porta, abra a URL correspondente, como `http://127.0.0.1:8766`.

| Situação | O que verificar |
| --- | --- |
| **Ollama is offline** | Inicie o Ollama e clique em **Refresh connection**. Verifique a porta local 11434. |
| **Install a local chat model** | Rode `ollama list`. Se não houver modelo de conversa, instale um com `ollama pull <modelo>` e atualize a conexão. |
| A resposta demora | Pesquisas podem levar minutos; modelos grandes exigem mais RAM/VRAM. Experimente um modelo menor ou desmarque **Search public sources**. |
| Não há resultados externos | Confira a internet, a opção de pesquisa e a trilha do dossiê. Busca vazia não prova que não exista opção. |
| A stack foi bloqueada | Leia os motivos no dossiê e revise requisitos incompatíveis. |
| A porta 8765 está ocupada | Rode com `--port 8766` e abra a nova URL. |

## Estado do projeto

Dois classificadores locais treinados e empacotados ajudam a identificar o domínio de software e a intenção da mensagem. Quem baixa o repositório **não precisa treiná-los**. Regras locais e trechos literais das mensagens ajudam com correções e negações, mas não eliminam erros do modelo generativo.

**Laya ainda não está integrado.** O [roteiro](docs/ROADMAP.md) prevê avaliar Laya para decisões tipadas, ampliar conectores, adicionar recuperação semântica/RAG, validar preços e elegibilidade de pagamentos por país e comparar modelos externos. Totais mensais, planos pagos, disponibilidade de Pix e benchmarks comerciais **não são calculados nesta versão**. Trate custos e opções de pagamento como pendências a verificar.

### Testes e contribuição

```powershell
python -m unittest discover -s tests -v
```

Os testes automatizados simulam Ollama e fontes públicas; não fazem buscas reais. O treinamento dos classificadores em `training/` é para manutenção, não para instalação. Consulte [CONTRIBUTING.md](CONTRIBUTING.md), o [relatório de testes](docs/TEST-REPORT.md) e o [modelo de domínio](docs/DOMAIN-POLICY.md). O código usa [licença MIT](LICENSE); ferramentas, modelos e conteúdos externos conservam suas próprias licenças.

---

## Technical overview (English)

Describe a software product. Local Ollama extracts its requirements, chooses public research calls, selects useful returned resources, and chooses a compatible initial architecture. The application opens an on-page dossier with tools, alternatives, integration constraints, security guidance and four ready-to-copy build prompts.

**Current release: research and dossier MVP.** This is an initial catalog and bounded research workflow, not exhaustive market research or a guarantee of the world's best tools. All 40 supplied hubs are registered; seven public-source entries have connectors. Laya is not installed. See [the full roadmap](docs/ROADMAP.md) and [the implemented research contract](docs/RESEARCH.md).

The software-only policy and two trained local classifiers ship enabled: one signals software-domain scope, the other helps route chat intent. Downloaders do not train anything or configure a system prompt. They need Python and an installed local Ollama chat model. This package does not redistribute generative model weights.

## Run

Requires Python 3.10+ and Ollama. The application uses the Python standard library and has no third-party Python dependencies.

```powershell
cd <path-to-phase0>
python -m phase0.server
```

Open http://127.0.0.1:8765, choose an installed local chat model and describe your product. If Ollama is not running, start it first. Ctrl+Enter sends the message. A detailed product idea or construction-tool request generates the dossier automatically. Requirement changes recompute it; explanation and debugging questions receive direct replies while preserving the plan.

```powershell
python -m phase0.server --port 8766 --data-dir ./my-local-data
```

The **Search public sources** checkbox defaults on. Turn it off for local catalog-only operation. Inference and storage stay local in both modes; public research requires internet. Response quality, latency and hardware requirements depend on the installed model.

## What works

- Local Ollama model selection and software-focused chat, with bundled domain and chat-intent classifiers plus local domain checks. Training runs only for maintainers; downloaded copies already include both models.
- Structured requirements backed by exact user quotes. The decision engine uses the quoted words rather than a generated paraphrase, preserving negations, prices, units and corrections. Narrow literal recovery can still miss or misinterpret unusual wording.
- Model-directed research plans with up to four bounded calls. Python connectors execute the calls; results return to Ollama to select resource IDs. The software derives each resource type and evidence from the actual source, filters platform/domain mismatches and weak references, and marks unverified capabilities as gaps. Ollama may choose a bounded alternative public query from predefined variants after an empty B3 or booking search. Invalid source/topic combinations are skipped and shown as rejected tasks.
- GitHub repository search, Hugging Face model metadata search, resource retrieval from public-apis and free-for-dev, bounded public UI page retrieval, and documentation retrieval from catalog URLs. UI retrieval is not a full site-wide search.
- An authored initial catalog of 25 tools and nine architecture combinations, including local Python CLI and simple browser utilities. Code rejects incompatible platform, offline, account, database and mandatory-tool combinations; Ollama chooses among compatible candidates using typed decisions. Invalid choices fall back visibly to local ranking. An unsupported platform or fixed stack is reported as blocked.
- An automatic dossier containing product understanding, research trace, sources, stack, alternatives, rejected combinations, integration restrictions, unverified costs, conditional payment options, security checklist and four contextual build prompts.
- Persistent projects, messages, notes and dossiers in SQLite. Refused turns cannot change the dossier. Failed inference does not commit a partial turn.
- JSON exports and prompt copying. Mystic Jade and warm ivory UI with inline controls, on-page chat/dossier/source views, and no modal overlays.

## Current limits

Only the initial catalog combinations are supported. An incompatible request produces a blocked dossier instead of a fabricated stack. Search categories now distinguish ASR transcription, B3 stocks, cryptocurrency quotes, CLI file processing and bookings; they remain predefined public categories rather than unrestricted private queries. Source failures, empty searches and invalid selections are visible. Directory listings, repository descriptions and model metadata are discovery evidence, not proof of production fitness, complete documentation review or API eligibility.

Monthly totals, paid tier projections, payment country eligibility, Pix routing and commercial-model benchmarks are not implemented. Costs remain explicitly unverified. Payment entries are conditional options rather than a final checkout pipeline. Prompts are contextual templates, not proof that an external coding tool can build the product correctly. Laya, embeddings/vector RAG, broader connectors and complete deployment analysis remain on the roadmap. The prototype is not an absolute zero-hallucination or zero-drift guarantee.

## Cloud deployment

`phase0.wsgi:app` runs the same application on Vercel behind a password session (signed `HttpOnly` cookie plus CSRF token), stores projects in Postgres (`DATABASE_URL`) and calls an OpenAI-compatible provider (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODELS`). Product descriptions and history are then sent to that provider. See [docs/DEPLOY-VERCEL.md](docs/DEPLOY-VERCEL.md). The local server below is unchanged.

## Privacy and security

The server binds only to `127.0.0.1`. Inference requests go only to `http://127.0.0.1:11434`; known cloud model entries are excluded. The model's chosen public categories become predefined search strings or fixed catalog documentation URLs. The connectors do not transmit the product description, chat history, notes or arbitrary model-generated URLs. Public services receive the request, public query and network metadata such as IP address. No research keys, analytics or CDN assets are used.

Source registration alone does not contact sources. Disable public research to avoid connector network calls. Ollama/model downloads have their own connectivity requirements. For local-only inference, configure Ollama's cloud features accordingly; there is no remote-model URL setting in Phase 0.

SQLite is stored in `data/phase0.sqlite3` and is not encrypted at rest. Exports may include private project content. Host/Origin checks, API session tokens, text-node rendering and a restrictive CSP protect the local web interface. Fetched pages are untrusted data; their text cannot initiate arbitrary connector actions. Fetches have body/timeout limits and redirects are disabled. Do not expose this development server publicly.

## Verification

```powershell
python -m unittest discover -s tests -v
```

Automated tests use mocks for Ollama and source responses; they make no live searches. Real Ollama/source and browser checks are documented separately in [the test report](docs/TEST-REPORT.md). See [the domain model and its limitations](docs/DOMAIN-POLICY.md).

## Contributing and license

Code is MIT licensed. See [CONTRIBUTING.md](CONTRIBUTING.md). External tools, models, UI components and retrieved resources keep their own licenses; MIT does not grant their redistribution rights.
