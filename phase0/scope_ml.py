"""Dependency-free multinomial Naive Bayes inference and reproducible training.

This small classifier is a routing signal, not a security boundary or a general LLM.
"""
import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).parent / 'policy' / 'scope-model.json'


def features(text):
    normalized = ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                         if unicodedata.category(c) != 'Mn')
    words = re.findall(r'[a-z0-9_]+', normalized)
    return Counter(words + [a + ':' + b for a, b in zip(words, words[1:])])


def train(rows):
    counts = {label: Counter() for label in ('software', 'outside')}
    examples = Counter()
    for row in rows:
        counts[row['label']].update(features(row['text']))
        examples[row['label']] += 1
    vocabulary = sorted(set(counts['software']) | set(counts['outside']))
    likelihood = {}
    for label, count in counts.items():
        denominator = sum(count.values()) + len(vocabulary)
        likelihood[label] = {word: math.log((count[word] + 1) / denominator) for word in vocabulary}
    return {'version': 1, 'algorithm': 'multinomial-naive-bayes', 'alpha': 1,
            'feature_version': 1, 'training_examples': dict(examples),
            'log_likelihood': likelihood}


def predict(text, model):
    tokens = features(text)
    known = {word: min(count, 3) for word, count in tokens.items()
             if word in model['log_likelihood']['software']}
    total = sum(known.values())
    if not total:
        return {'label': 'uncertain', 'margin': 0.0, 'known_features': 0}
    # Equal class priors. Mean log-odds is a score, deliberately not a probability.
    margin = sum(count * (model['log_likelihood']['software'][word] -
                          model['log_likelihood']['outside'][word])
                 for word, count in known.items()) / total
    return {'label': 'software' if margin >= 0 else 'outside',
            'margin': round(margin, 6), 'known_features': total}


@lru_cache(maxsize=1)
def bundled_model():
    model = json.loads(MODEL_PATH.read_text(encoding='utf-8'))
    if model.get('version') != 1 or model.get('feature_version') != 1:
        raise ValueError('Unsupported bundled scope model')
    return model


def classify(text):
    return predict(text, bundled_model())
