"""Small, bundled intent classifier; a routing hint, not an LLM or domain boundary.

Training is maintainer-only. Runtime inference uses the committed artifact and
does not train on conversations, call a service, or download a model.
"""
import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

LABELS = ('plan', 'refine', 'explain', 'debug', 'chat')
MODEL_PATH = Path(__file__).parent / 'policy' / 'intent-model.json'
MIN_MARGIN = 0.22
MIN_TEXT_FEATURES = 3


def normalized_text(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


def features(text, has_dossier=False, pending_requirement=False):
    words = re.findall(r'[a-z0-9_]+', normalized_text(text))
    counts = Counter(words + [a + ':' + b for a, b in zip(words, words[1:])])
    counts['context__dossier' if has_dossier else 'context__no_dossier'] = 1
    counts['context__pending' if pending_requirement else 'context__no_pending'] = 1
    return counts


def train(rows):
    counts = {label: Counter() for label in LABELS}
    examples = Counter()
    for row in rows:
        if row['label'] not in counts or not row['text'].strip():
            raise ValueError('Invalid intent training row')
        counts[row['label']].update(features(row['text'], row.get('has_dossier', False),
                                            row.get('pending_requirement', False)))
        examples[row['label']] += 1
    if any(not examples[label] for label in LABELS):
        raise ValueError('Training requires examples for every intent')
    vocabulary = sorted(set().union(*(set(values) for values in counts.values())))
    likelihood = {}
    for label, count in counts.items():
        denominator = sum(count.values()) + len(vocabulary)
        likelihood[label] = {token: math.log((count[token] + 1) / denominator)
                             for token in vocabulary}
    return {'version': 1, 'feature_version': 1, 'algorithm': 'multinomial-naive-bayes',
            'alpha': 1, 'labels': list(LABELS), 'training_examples': dict(examples),
            'min_margin': MIN_MARGIN, 'min_text_features': MIN_TEXT_FEATURES,
            'log_likelihood': likelihood}


def predict(text, model, has_dossier=False, pending_requirement=False):
    tokens = features(text, has_dossier, pending_requirement)
    vocabulary = model['log_likelihood'][LABELS[0]]
    known = {token: min(count, 3) for token, count in tokens.items() if token in vocabulary}
    text_count = sum(count for token, count in known.items() if not token.startswith('context__'))
    if not text_count:
        return {'label': 'uncertain', 'candidate': None, 'score': 0.0, 'margin': 0.0,
                'known_features': 0}
    total = sum(known.values())
    # Equal class priors; averaged log likelihoods and margins are NOT probabilities.
    scores = {label: sum(count * model['log_likelihood'][label][token]
                         for token, count in known.items()) / total for label in LABELS}
    ranked = sorted(scores, key=lambda label: (-scores[label], label))
    best, runner_up = ranked[:2]
    margin = scores[best] - scores[runner_up]
    confident = text_count >= model['min_text_features'] and margin >= model['min_margin']
    return {'label': best if confident else 'uncertain', 'candidate': best,
            'score': round(scores[best], 6), 'margin': round(margin, 6),
            'known_features': text_count}


@lru_cache(maxsize=1)
def bundled_model():
    model = json.loads(MODEL_PATH.read_text(encoding='utf-8'))
    if (model.get('version') != 1 or model.get('feature_version') != 1
            or model.get('labels') != list(LABELS)):
        raise ValueError('Unsupported bundled intent model')
    return model


def classify(text, has_dossier=False, pending_requirement=False):
    return predict(text, bundled_model(), has_dossier, pending_requirement)
