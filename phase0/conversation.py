"""Route the current request before extracting facts or starting new research."""
import re
import unicodedata
from . import intent_ml


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


def wants_build_tools(text, messages):
    current = normalize(text)
    def request(value):
        return bool(re.search(
            r'(quais|que|qual|what|which).{0,90}(ferrament|software|stack|tecnolog|linguage|framework|tools)'
            r'|(preciso|usar|use|need).{0,60}(fazer|criar|construir|build|make)'
            r'|(ferrament|software|stack|tools).{0,60}(fazer|criar|construir|build|make)', value))
    if request(current):
        return True
    if current.strip(' .!') in {'isso', 'sim', 'exato', 'yes', 'exactly'}:
        previous = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), '')
        return request(normalize(previous))
    return False


PRODUCT = (r'\b(app|aplicativo|aplicacao|site|website|software|painel|dashboard|'
           r'plataforma|saas|cli|script|extensao|extension|plugin|bot|jogo|game|'
           r'application|automacao|automation|ferramenta|tool|servico|service)\b')


def _context(project):
    messages = project.get('messages') or []
    last_assistant = next((m.get('content', '') for m in reversed(messages)
                           if m.get('role') == 'assistant'), '')
    prompt = normalize(last_assistant)
    pending = bool('?' in prompt and re.search(
        r'orcamento|budget|pais|country|geograf|regiao|region|plataforma|platform|'
        r'mobile|desktop|monetiza|cobrar|charge|experiencia|experience|usuarios|users|'
        r'funcionalidades|features|integracoes|integrations|offline|privacidade|privacy', prompt))
    profile = project.get('profile') or {}
    has_product = bool((profile.get('product') or {}).get('value'))
    has_dossier = bool(project.get('dossier'))
    # An unplanned but explicit user product brief is also valid refinement context.
    has_brief = any(m.get('role') == 'user' and m.get('scope', 'legacy') in {'software', 'legacy'}
                    and re.search(PRODUCT, normalize(m.get('content', '')))
                    for m in messages[-8:])
    return has_dossier, pending, has_dossier or has_product or has_brief


def route_intent(text, project):
    """Return plan/refine/explain/debug/chat without changing project state.

    Explicit intent guards outrank the model. Uncertain ML predictions abstain to
    ordinary in-domain conversation; the caller still applies its domain and fact
    checks. Scores are uncalibrated log-likelihoods, never confidence percentages.
    """
    current = normalize(text).strip()
    messages = project.get('messages') or []
    has_dossier, pending, has_context = _context(project)

    def route(intent, reason):
        return {'intent': intent, 'source': 'rule:' + reason}

    if re.fullmatch(r'(oi|ola|hello|hi|hey|bom dia|boa tarde|boa noite|obrigad[oa]|'
                    r'valeu|thanks|thank you|ok|okay|entendi|perfeito|legal)[\s!.,]*', current):
        return route('chat', 'greeting_or_acknowledgement')

    # A report of a current fault is not an architecture change, even when long.
    debug_request = bool(re.search(
        r'\b(?:encontrei|estou com|tenho|have|got)\s+(?:um|uma|an?\s+)?(?:erro|bug|problema)\b|'
        r'\b(?:como|how)\b.{0,55}\b(?:loop|renderizacao|rerender)\b|'
        r'\b(traceback|typeerror|referenceerror|syntaxerror|exception|stack trace)\b|'
        r'(?:corrig|depur|debug|consert|diagnostic|fix|troubleshoot).{0,65}'
        r'(?:erro|error|bug|falha|failure|crash|loop|codigo|code|problema|issue)|'
        r'(?:erro|error|bug|falha|crash|loop).{0,70}(?:como|how|ajud|help|corrig|fix)|'
        r'(?:meu|minha|my|the|o|a)\s+(?:codigo|code|app|site|script|api|build|teste|test|componente|component)'
        r'.{0,70}(?:nao funciona|nao compila|quebra|falha|trava|crashes|fails|broken|does not work)|'
        r'\b(?:requisicoes|requests|chamadas|calls)\b.{0,60}(?:repet|render|loop)', current))
    explanation = bool(re.search(
        r'\b(compare|comparar|comparacao|comparison|versus|vs|explique|explica|explain|'
        r'diferenca|difference|diferencas|differences|tradeoff|tradeoffs)\b|'
        r'\b(por que|why)\b|'
        r'\bporque\b.{0,90}\b(escolh\w*|us\w*|recomend\w*|choose|chose|recommend)|'
        r'\b(pros e contras|pros and cons|vantagens e desvantagens)\b|'
        r'\b(como|how)\b.{0,70}\b(funciona|funcionam|works|work)\b|'
        r'\b(o que e|what is|o que significa|what does).{0,70}', current))
    if debug_request:
        return route('debug', 'current_fault')

    # Imperative requirement edits have priority over generic build-tools wording.
    correction = bool(re.search(
        r'\b(?:correcao|atualizacao)\s*[:\-]\s*(?:removi|remova|remover|retirei|mudei|troquei|agora|quero)\b|'
        r'\b(?:removi|retirei|eliminei|descartei)\b|\bquero\s+(?:so|apenas|somente)\b|'
        r'^(?:por favor[, ]+|please[, ]+)?(?:remov[ae]|retir[ae]|tire|tira|troqu[ae]|'
        r'substitua|adicione|acrescente|inclua|mude|altere|corrija os requisitos|'
        r'remove|replace|switch|add|change|update)\b|'
        r'\b(nao quero mais|nao preciso mais|agora quero|agora sera|agora precisa|'
        r'em vez de|ao inves de|mudei de ideia|quero apenas|quero somente|'
        r'i no longer want|i changed my mind|i only want|instead of)\b', current))
    if has_context and correction and not explanation:
        return route('refine', 'explicit_requirement_change')
    if explanation:
        return route('explain', 'comparison_or_explanation')

    if wants_build_tools(current, messages) or re.search(
            r'\b(dossie|dossier|blueprint|architecture plan|plano completo|stack completa)\b|'
            r'\b(qual|que|which|what)\b.{0,50}\b(stack|banco|database|linguagem|language|'
            r'framework|hospedagem|hosting|tecnologia|technology)\b.{0,40}'
            r'\b(usar|use|escolher|choose|recomenda|recommend|melhor|best)\b', current):
        return route('plan', 'architecture_request')

    explicit_product = bool(re.search(
        r'\b(quero|vou|pretendo|preciso|i want|i need|help me|we need|we want)\b.{0,45}'
        r'\b(criar|construir|fazer|desenvolver|build|create|make|develop)\b', current)
        and re.search(PRODUCT, current))
    product_description = bool(re.search(PRODUCT, current) and (
        re.search(r'\b(produto|projeto|ideia|product|project|idea)\b.{0,35}'
                  r'\b(e|sera|is|will|consiste|trata)\b', current)
        or (len(current) > 75 and re.search(
            r'\b(usuarios|users|clientes|customers|permite|allows|deve|should|precisa|'
            r'needs|offline|assinatura|subscription|exporta|exports|gerencia|manages|'
            r'organiza|organizes|automatiza|automates|mensal|monthly)\b', current))))
    if explicit_product or product_description:
        return route('plan', 'product_brief')

    fact_answer = bool(re.search(
        r'^(?:meu |o |my |the )?(?:orcamento|budget|publico|audience|pais|country|'
        r'plataforma|platform|monetizacao|monetization|experiencia|experience)\b|'
        r'^(?:vai|deve|it will|it should)\s+(?:rodar|funcionar|ser|run|work|be)\b|'
        r'^(?:brasil|brazil|portugal|android|ios|web|desktop|mobile|offline|'
        r'r\$\s*\d|\$\s*\d|\d+\s*(?:reais|euros|dolares|usuarios|users))\b', current))
    confirmation = current.strip(' .!?') in {'sim', 'isso', 'exato', 'yes', 'exactly', 'nao', 'no'}
    if has_context and (fact_answer or (pending and (confirmation or len(current) < 100))):
        return route('refine', 'requirement_answer')

    try:
        prediction = intent_ml.classify(text, has_dossier, pending)
    except (OSError, ValueError, KeyError, TypeError):
        return {'intent': 'chat', 'source': 'fallback:model_unavailable'}
    label = prediction['label']
    if label == 'refine' and not has_context:
        label = 'chat'
    # A model alone does not turn an acknowledgement into a fresh dossier.
    if label == 'plan' and len(current.split()) < 5:
        label = 'chat'
    return {'intent': label if label in intent_ml.LABELS else 'chat',
            'source': 'ml' if label in intent_ml.LABELS else 'fallback:uncertain',
            'score': prediction['score'], 'margin': prediction['margin']}
