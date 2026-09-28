"""Maintainer-only training. Normal installation uses the committed model artifact."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from phase0.scope_ml import train, predict  # noqa: E402


def rows(group):
    return [{'label': label, 'text': text} for label, texts in group.items() for text in texts]


if __name__ == '__main__':
    data_path = ROOT / 'training' / 'scope-data.json'
    data = json.loads(data_path.read_text(encoding='utf-8'))
    training, evaluation = rows(data['train']), rows(data['evaluation'])
    assert not {r['text'] for r in training} & {r['text'] for r in evaluation}
    model = train(training)
    model['dataset_sha256'] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    model['license'] = 'MIT'
    (ROOT / 'phase0' / 'policy' / 'scope-model.json').write_text(
        json.dumps(model, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    mistakes = []
    matrix = {label: {'software': 0, 'outside': 0, 'uncertain': 0} for label in data['evaluation']}
    for row in evaluation:
        prediction = predict(row['text'], model)
        matrix[row['label']][prediction['label']] += 1
        if prediction['label'] != row['label']:
            mistakes.append({**row, 'prediction': prediction})
    report = {'training_examples': len(training), 'evaluation_examples': len(evaluation),
              'correct': len(evaluation) - len(mistakes), 'confusion_matrix': matrix,
              'mistakes': mistakes, 'dataset_sha256': model['dataset_sha256'],
              'limitations': 'Small authored synthetic PT/EN set. This is not real-world accuracy or a jailbreak guarantee. '
                             'Scores are uncalibrated and contextual follow-ups require the policy gate.'}
    (ROOT / 'training' / 'evaluation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Trained {len(training)} examples; held-out: {report['correct']}/{len(evaluation)}")
