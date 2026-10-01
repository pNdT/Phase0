# Publicar o Phase 0 na Vercel

Com isto, o Phase 0 fica num endereço `https://….vercel.app` que abre de qualquer computador, sem deixar nada ligado em casa. É o mesmo modelo do lead-robot: o app roda na Vercel, os projetos ficam num Postgres gerenciado e o modelo de IA é um provedor na nuvem (Groq por padrão).

O modo local não mudou: `python -m phase0.server` continua usando Ollama e SQLite, sem pip.

## O que muda na nuvem

| | Local | Vercel |
| --- | --- | --- |
| Modelo | Ollama no seu PC | Groq ou outra API compatível com OpenAI |
| Projetos | `data/phase0.sqlite3` | Postgres (`DATABASE_URL`) |
| Acesso | só `127.0.0.1` | qualquer lugar, **com senha** |
| Privacidade | a conversa não sai do PC | a descrição e o histórico vão para o provedor do modelo |

Os projetos do SQLite local **não são copiados** para o Postgres.

## Passo a passo

1. **Projeto na Vercel.** Em vercel.com → **Add New → Project**, importe o repositório `pNdT/Phase0`. Não precisa escolher framework: a Vercel lê `pyproject.toml` (entrada `phase0.wsgi:app`) e instala o `psycopg`.
2. **Banco.** Na aba **Storage** do projeto, crie um **Neon Postgres** pelo Marketplace e conecte ao projeto. Ele cria `DATABASE_URL` sozinho. Se preferir o Supabase, use a URL do **pooler** (porta 6543). As tabelas são criadas no primeiro acesso.
3. **Chave do modelo.** Crie uma chave em console.groq.com → **API Keys**.
4. **Variáveis de ambiente** (Settings → Environment Variables, ambiente *Production*):

   | Variável | Valor |
   | --- | --- |
   | `PHASE0_PASSWORD` | senha longa para entrar no app |
   | `LLM_PROVIDER` | `groq` |
   | `LLM_API_KEY` | a chave do Groq |
   | `LLM_MODELS` | por exemplo `openai/gpt-oss-120b,openai/gpt-oss-20b` (o primeiro é o padrão) |
   | `DATABASE_URL` | já criada pelo passo 2 |
   | `PHASE0_SECRET` | opcional: texto aleatório longo que assina o login. Trocar desconecta todos |

   Para OpenRouter use `LLM_PROVIDER=openrouter`. Para outra API compatível com OpenAI, use `LLM_PROVIDER=openai` e `LLM_BASE_URL=https://…/v1`.
5. **Deploy.** Clique em **Redeploy** (variáveis só valem em deploys novos). Abra o endereço de produção, entre com a senha e use normalmente.

Se faltar alguma variável, a página mostra `Phase 0 is not configured: missing environment variables: …` em vez de abrir sem proteção.

## Limites conhecidos

- **Tempo:** cada mensagem pode levar até 300 s (teto do plano Hobby). Um dossiê faz várias chamadas ao modelo e às fontes públicas; com o Groq costuma caber, mas pesquisa lenta pode estourar. Se acontecer, desmarque **Search public sources** e tente de novo.
- **Limite de uso do provedor:** o plano gratuito do Groq tem limites por minuto. Um dossiê faz várias chamadas seguidas; um erro "rate limit" pede só para esperar e reenviar. Confira os limites e preços atuais no painel do Groq.
- **Qualidade:** o Phase 0 foi ajustado com modelos do Ollama. Com outro modelo, extração e escolhas podem mudar; o modelo precisa seguir JSON bem (os `gpt-oss` do Groq aceitam esquema JSON).
- **Senha única:** é um app pessoal, não multiusuário. Quem tiver a senha vê todos os projetos.
- **Domínio próprio:** funciona sem configuração extra; o app exige apenas que a origem da requisição seja o mesmo endereço aberto no navegador.

## Testar contra um Postgres

```powershell
$env:PHASE0_TEST_DATABASE_URL="postgresql://usuario:senha@host:5432/banco"
python -m unittest discover -s tests -v
```

Sem essa variável, os testes de Postgres são pulados e o resto roda só com a biblioteca padrão (os testes de nuvem não precisam do `psycopg`).
