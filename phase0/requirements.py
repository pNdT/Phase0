"""Quote-grounded requirement updates and explicit compatibility constraints.

The LLM assigns facts to fields. Values used for decisions are the user's words,
not the model's paraphrases. Additions/removals preserve their source quotes.
"""
import re
from .conversation import normalize


FIELD_PATTERNS = {
    'platform': r'\b(web|site|website|mobile|android|ios|celular|desktop|terminal|cli|linha de comando|command.line|extensao|extension|jogo|game|indecis|undecided)\b',
    'budget': r'orcamento|budget|infraestrutura|infrastructure|hosped|hosting|publicacao barata|custo|cost|gastar|spend|para uma api|para api',
    'geography': r'brasil|brazil|sao paulo|portugal|europe|europa|united states|estados unidos|\bpais\b|country|global',
    'monetization': r'cobrar|cobro|cobranca|assinatura|subscription|monetiz|vender|vendo|gratuit|free|charge|paid|pago|checkout|doac',
    'technical_comfort': r'iniciante|beginner|novato|experien|ja sei|prefiro|prefer|obrigator|manter|nao trocar|sem trocar|nao mude',
    'scale': r'\d+\s*(?:usuarios|users|pessoas|clientes|contas|accounts|saloes|lojas|funcionarios|requests)|trafego|traffic|por dia|per day',
    'privacy': r'privac|lgpd|gdpr|sensiv|sensitive|local|offline|cloud|nuvem|armazen|storage|dados|data|internet|confidenc|computador|aparelho|gpu|\bram\b',
    'integrations': r'\b(api|apis|strava|valorant|pix|ia|ai|llm)\b|integrac|integration|inteligencia artificial|reconhecimento de fala|speech recognition|servicos externos',
}
EXCLUSIVE = r'\b(?:apenas|somente|so|only|just)\b.{0,45}(?:cronometro|timer|funcionalidade|recurso|feature|local|um|uma)|\b(?:substitua|replace|em vez de|instead of)\b'


def fact_text(fact):
    if fact.get('source_quotes'):
        return '\n'.join(fact['source_quotes'])
    return fact.get('evidence') or fact.get('value') or ''


def polarity(text, pattern):
    """Last explicit mention wins; negation spans coordinated lists, not sentences."""
    text = normalize(text)
    found = None
    # Portuguese "no" is normally "in/on the" ("no celular", "no Windows").
    # Treat it as the English negative article only in English-language text.
    english_no = '' if re.search(r'\b(quero|nao|sem|preciso|para|meu|minha|fica|ficam|sera|tenho|vou|uso)\b', text) else 'no\\s+|'
    markers = re.compile(
        r'(?P<negative>\b(?:nao\s+(?:(?:vou|vai|havera|quero|preciso|precisa|terei|teremos|usar|use|deve)\s+)*|'
        r'sem\s+|nenhum[a]?\s+|' + english_no + r'without\s+|not\s+|remove\w*\s+|remov\w*\s+|retir\w*\s+|exclu\w*\s+|dispenso\s+))'
        r'|(?P<positive>\b(?:mas|porem|but|quero|preciso|inclu\w*|adicione|adicionar|add|com|with|need|require|so|somente|apenas|only|manter|keep|e\s+(?:grava|salva|escreve)|and\s+(?:writes?|saves?|outputs?))\s+)')
    for match in re.finditer(pattern, text):
        prefix = re.split(r'[.;!?\n]', text[:match.start()])[-1]
        controls = list(markers.finditer(prefix))
        found = not controls or controls[-1].lastgroup != 'negative'
    return found


def positive(text, pattern):
    return polarity(text, pattern) is True


def quoted_updates(updates, text, *, planning=False):
    """Canonicalize model updates to exact excerpts and recover explicit constraints.

    No model-authored currency, count, audience or free-tier assumption is stored.
    Narrow literal recovery covers facts the model sometimes drops or misquotes.
    """
    accepted, rejected = {}, []
    for key, fact in updates.items():
        quote = fact.get('evidence') or ''
        if not quote or quote not in text:
            rejected.append(key)
            continue
        if key in FIELD_PATTERNS and not re.search(FIELD_PATTERNS[key], normalize(quote)):
            rejected.append(key)
            continue
        accepted[key] = {'value': quote, 'evidence': quote, 'source_quotes': [quote]}
    if planning:
        sentences = [piece.strip() for piece in re.split(r'(?<=[.!?])\s+|\n+', text) if piece.strip()]
        for field in ('budget', 'monetization', 'privacy', 'technical_comfort', 'scale', 'platform', 'integrations'):
            matches = [piece for piece in sentences if re.search(FIELD_PATTERNS[field], normalize(piece))]
            # Use the full literal sentence to preserve a negation or a currency/period.
            if matches:
                quote = '\n'.join(matches)
                accepted[field] = {'value': quote, 'evidence': matches[-1], 'source_quotes': matches}
        if 'features' not in accepted and len(text) > 45:
            accepted['features'] = {'value': text, 'evidence': text, 'source_quotes': [text]}
        if 'product' not in accepted and sentences and re.search(r'criar|construir|build|create|o .* e um|my .* is', normalize(text)):
            accepted['product'] = {'value': sentences[0], 'evidence': sentences[0], 'source_quotes': [sentences[0]]}
    return accepted, [key for key in rejected if key not in accepted]


def apply_updates(project, updates, text, *, refine=False):
    """Merge feature changes as sourced statements; explicit narrowing replaces them."""
    narrowed = bool(re.search(EXCLUSIVE, normalize(text)))
    old_profile = project['profile']
    for key, fact in updates.items():
        previous = old_profile[key]
        if refine and key in {'features', 'integrations'} and previous.get('value'):
            replace = narrowed or (key == 'integrations' and polarity(text, r'integrac\w*|integration\w*|servicos externos') is False)
            if not replace:
                quotes = previous.get('source_quotes') or [fact_text(previous)]
                quotes = list(dict.fromkeys(quotes + fact.get('source_quotes', [fact['evidence']])))
                fact = {**fact, 'value': '\n'.join(quotes), 'source_quotes': quotes}
        old_profile[key] = fact
    if refine and narrowed:
        # A narrowed product scope is authoritative even if extraction omitted features.
        old_profile['features'] = {'value': text, 'evidence': text, 'source_quotes': [text]}
        if polarity(text, r'integrac\w*|integration\w*|servicos externos') is False:
            old_profile['integrations'] = {'value': text, 'evidence': text, 'source_quotes': [text]}


def specification(project, brief):
    fields = {key: fact_text(fact) for key, fact in project['profile'].items()}
    features = fields['features'] or brief
    narrowed = bool(re.search(EXCLUSIVE, normalize(features)))
    context = features if narrowed else '\n'.join([fields['product'], features])
    context += '\n' + fields['integrations']
    personal_context = context+'\n'+fields['platform']+'\n'+fields['privacy']
    platform_text = fields['platform'] or brief
    platform = 'web'
    for name, pattern in [('web', r'\b(web|site|website)\b'), ('mobile', r'\b(mobile|android|ios|celular)\b'),
                          ('desktop', r'\b(desktop|aplicativo instalado)\b'),
                          ('cli', r'\b(cli|terminal|linha de comando|command.line)\b'),
                          ('extension', r'\b(extensao|extension)\b'), ('game', r'\b(jogo|game)\b')]:
        if positive(platform_text, pattern):
            platform = name
    if re.search(r'undecided|indecis|nao sei|maybe', normalize(platform_text)):
        platform = 'undecided'
    privacy = fields['privacy'] or brief
    local = positive(privacy, r'\boffline\b|100% local|totalmente local|entirely local') or bool(re.search(
        r'sem (?:internet|nuvem)|no cloud|dados ficam so|dados.*nao podem sair|so no (?:meu )?(?:computador|aparelho)|rodar localmente', normalize(privacy)))
    money = fields['monetization'] or context
    paid = any(positive(money, pattern) for pattern in (
        r'\b(assinatura|subscription)\b', r'\b(vender|monetizar|cobrar)\b', r'\b(paid|pago)\b', r'\bcheckout\b'))
    multi = any(positive(context, pattern) for pattern in (
        r'\b(login|autenticacao|sso)\b', r'\b(contas|accounts)\b', r'\b(multiusuario|multiuser|marketplace|saas)\b'))
    capabilities = []
    patterns = {
        'speech_recognition': r'transcrev\w*|transcric\w*|reconhecimento de fala|speech recognition|\basr\b',
        'stock_data': r'\bb3\b|acoes brasileiras|stock prices?|dividendos|dividends',
        'crypto_data': r'criptomoedas?|cryptocurrenc\w*|\bcrypto\b|bitcoin',
        'timer': r'cronometro|pomodoro|\btimer\b',
        'file_processing': r'\bcsv\b|renomear arquivos|rename files|consolidar arquivos',
        'booking': r'agendament\w*|reservam horarios|reservas?|bookings?|appointments?',
        'strava': r'\bstrava\b', 'valorant': r'\bvalorant\b',
    }
    for name, pattern in patterns.items():
        if positive(context, pattern):
            capabilities.append(name)
    no_integrations = polarity(context, r'integrac\w*|integration\w*|servicos externos|external services') is False
    if no_integrations:
        capabilities = [name for name in capabilities if name not in {'strava', 'valorant', 'crypto_data', 'stock_data'}]
    vector = positive(context, r'\b(rag|vetorial|vector|embeddings|busca semantica|semantic search)\b')
    ai = positive(context, r'\b(ia|ai|llm|inteligencia artificial|ollama)\b') or vector or 'speech_recognition' in capabilities
    integrations = not no_integrations and (positive(context, r'\b(api|apis|integrac\w*|integration\w*)\b') or any(
        name in capabilities for name in ('strava', 'valorant', 'crypto_data', 'stock_data')))
    # A program running on one computer can still need a network API. Treat offline as a
    # no-network constraint, not as a synonym for local installation or personal use.
    if integrations:
        local = False
    static = positive(context, r'site institucional|landing page|portfolio|blog|site de conteudo|marketing site')
    dashboard = positive(context, r'widgets?|dashboard|painel|central de comando')
    budget = fields['budget']
    if not budget:
        budget = '\n'.join(piece for piece in re.split(r'[.!?\n]', brief) if re.search(FIELD_PATTERNS['budget'], normalize(piece)))
    signals = {
        'dashboard': dashboard, 'static': static and not (dashboard or multi or integrations or vector),
        'seo': positive(context, r'\b(seo|blog|site institucional|portfolio)\b'),
        'integrations': integrations, 'realtime': positive(context, r'tempo real|real.time|cotacoes|rank atualizado'),
        'vector': vector, 'ai': ai, 'multiuser': multi or paid, 'paid': paid, 'offline': local,
        'personal': positive(personal_context, r'para mim|minha vida|pessoal|personal|my life|so no meu computador|uso pessoal') and not (multi or paid),
        'beginner': positive(fields['technical_comfort'] or brief, r'iniciante|beginner|novato'),
        'zero_budget': positive(budget, r'(?:r\$|\$)\s*0\b|orcamento\s+(?:(?:e|de|sera)\s+)?zero|budget\s+(?:(?:is|of)\s+)?(?:zero|free)|free (?:hosting|to host)') or normalize(budget).strip() in {'zero','0','free','gratis','gratuito'},
        'speech': 'speech_recognition' in capabilities,
        **{name: name in capabilities for name in ('stock_data', 'crypto_data', 'timer', 'file_processing', 'booking')},
    }
    constraint_text = context + '\n' + fields['technical_comfort'] + '\n' + fields['privacy']
    constraints = {
        'no_integrations': no_integrations,
        'no_database': polarity(constraint_text, r'banco de dados|database|\bbanco\b') is False,
        'no_backend': polarity(constraint_text, r'servidor|server|backend') is False,
        'no_ui': polarity(constraint_text, r'interface grafica|graphical interface|\bgui\b') is False,
        'required_tools': [],
    }
    preference = fields['technical_comfort'] or brief
    if positive(preference, r'obrigator\w*|\b(manter|must|mandatory|keep)\b') or re.search(r'nao troq\w*|sem trocar|nao mude|do not (?:change|replace)', normalize(preference)):
        for name, pattern in {'vue':r'\bvue\b', 'django':r'\bdjango\b', 'postgres':r'postgres(?:ql)?',
                              'react-native':r'react native', 'expo':r'\bexpo\b', 'python':r'\bpython\b',
                              'flutter':r'\bflutter\b', 'sqlite':r'\bsqlite\b'}.items():
            if re.search(pattern, normalize(preference)):
                constraints['required_tools'].append(name)
    return platform, signals, capabilities, constraints
