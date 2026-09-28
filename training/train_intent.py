"""Rebuild the shipped intent hint and evaluate an untouched authored holdout."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from phase0 import intent_ml  # noqa: E402
from phase0.conversation import route_intent  # noqa: E402


def key(row):
    return ' '.join(intent_ml.normalized_text(row['text']).split())


def validate_dataset(data):
    training, evaluation = data['train'], data['evaluation']
    train_keys, evaluation_keys = {key(r) for r in training}, {key(r) for r in evaluation}
    if len(train_keys) != len(training) or len(evaluation_keys) != len(evaluation):
        raise ValueError('Duplicate intent examples')
    if train_keys & evaluation_keys:
        raise ValueError('Training/held-out overlap')
    return training, evaluation


def context_project(row):
    messages = []
    if row.get('pending_requirement'):
        messages = [
            {'role': 'user', 'content': 'Um aplicativo para organizar tarefas.'},
            {'role': 'assistant', 'content': 'Qual o orçamento, plataforma, país e escala esperada de usuários?'}]
    return {'dossier': {'id': 'evaluation-context'} if row.get('has_dossier') else None,
            'profile': {}, 'messages': messages}


def run():
    data_path = ROOT / 'training' / 'intent-data.json'
    data = json.loads(data_path.read_text(encoding='utf-8'))
    training, evaluation = validate_dataset(data)
    model = intent_ml.train(training)
    model['dataset_sha256'] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    model['license'] = 'MIT'
    intent_ml.MODEL_PATH.write_text(
        json.dumps(model, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    intent_ml.bundled_model.cache_clear()
    matrix = {label: {pred: 0 for pred in (*intent_ml.LABELS, 'uncertain')} for label in intent_ml.LABELS}
    routed_matrix = {label: {pred: 0 for pred in intent_ml.LABELS} for label in intent_ml.LABELS}
    mistakes, routed_mistakes = [], []
    for row in evaluation:
        prediction = intent_ml.predict(row['text'], model, row.get('has_dossier', False),
                                       row.get('pending_requirement', False))
        matrix[row['label']][prediction['label']] += 1
        if prediction['label'] != row['label']:
            mistakes.append({**row, 'prediction': prediction})
        routed = route_intent(row['text'], context_project(row))
        routed_matrix[row['label']][routed['intent']] += 1
        if routed['intent'] != row['label']:
            routed_mistakes.append({**row, 'route': routed})
    report = {
        'training_examples': len(training), 'evaluation_examples': len(evaluation),
        'dataset_sha256': model['dataset_sha256'],
        'model_only': {'correct': len(evaluation) - len(mistakes),
                       'abstentions': sum(values['uncertain'] for values in matrix.values()),
                       'confusion_matrix': matrix,
                       'mistakes_and_abstentions': mistakes},
        'rules_plus_model': {'correct': len(evaluation) - len(routed_mistakes),
                             'confusion_matrix': routed_matrix, 'mistakes': routed_mistakes},
        'limitations': [
            'Small authored synthetic PT/EN holdout; not a measured real-world success rate.',
            'Uncalibrated log-likelihood margins; low-confidence model predictions abstain.',
            'Routes request intent only. It does not judge source relevance, facts, or final answer quality.',
            'This trains a small local classifier, not Ollama, Laya, or a generative language model.',
            'Existing quality-evaluation conversations are regression checks, not training examples.'
        ]}
    (ROOT / 'training' / 'intent-evaluation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Trained {len(training)} examples; holdout {len(evaluation)}; '
          f'model {report["model_only"]["correct"]}; rules + model {report["rules_plus_model"]["correct"]}')
    return report


if __name__ == '__main__':
    run()
