import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from phase0 import intent_ml
from phase0.conversation import route_intent, wants_build_tools

ROOT = Path(__file__).resolve().parents[1]


def project(dossier=True, pending=False):
    return {'dossier': {'brief': 'A web app for volunteers'} if dossier else None,
            'profile': {'product': {'value': 'Volunteer app', 'evidence': 'volunteer app'}},
            'messages': [{'role': 'assistant', 'content': 'Qual é o orçamento mensal?'}] if pending else []}


class IntentClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_path = ROOT / 'training' / 'intent-data.json'
        cls.data = json.loads(cls.data_path.read_text(encoding='utf-8'))

    def test_committed_model_is_reproducible_without_network(self):
        trained = intent_ml.train(self.data['train'])
        committed = copy.deepcopy(intent_ml.bundled_model())
        self.assertEqual(committed.pop('dataset_sha256'), hashlib.sha256(self.data_path.read_bytes()).hexdigest())
        self.assertEqual(committed.pop('license'), 'MIT')
        self.assertEqual(trained, committed)
        self.assertEqual(trained, intent_ml.train(list(reversed(self.data['train']))))

    def test_training_and_holdout_are_distinct_after_normalization(self):
        def keys(group):
            return [' '.join(intent_ml.normalized_text(row['text']).split()) for row in self.data[group]]
        training, heldout = keys('train'), keys('evaluation')
        self.assertEqual(len(training), len(set(training)))
        self.assertEqual(len(heldout), len(set(heldout)))
        self.assertFalse(set(training) & set(heldout))
        self.assertEqual({row['label'] for row in self.data['train']}, set(intent_ml.LABELS))

    def test_context_features_are_present_but_do_not_classify_unknown_text(self):
        self.assertIn('context__dossier', intent_ml.features('same message', True))
        self.assertIn('context__pending', intent_ml.features('same message', False, True))
        self.assertNotIn('context__dossier', intent_ml.features('same message', False))
        unknown = intent_ml.predict('zqxv flbrz qyzx', intent_ml.bundled_model(), True, True)
        self.assertEqual(unknown['label'], 'uncertain')
        self.assertEqual(unknown['known_features'], 0)

    def test_report_matches_recomputed_predictions_and_routes(self):
        spec = importlib.util.spec_from_file_location('intent_training', ROOT / 'training' / 'train_intent.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = json.loads((ROOT / 'training' / 'intent-evaluation.json').read_text(encoding='utf-8'))
        predicted, routed, abstentions = 0, 0, 0
        for row in self.data['evaluation']:
            result = intent_ml.predict(row['text'], intent_ml.bundled_model(),
                                       row.get('has_dossier', False), row.get('pending_requirement', False))
            predicted += result['label'] == row['label']
            abstentions += result['label'] == 'uncertain'
            routed += route_intent(row['text'], module.context_project(row))['intent'] == row['label']
        self.assertEqual(report['model_only']['correct'], predicted)
        self.assertEqual(report['model_only']['abstentions'], abstentions)
        self.assertEqual(report['rules_plus_model']['correct'], routed)


class IntentRoutingTests(unittest.TestCase):
    def test_explanations_and_debugging_do_not_request_new_dossiers(self):
        samples = {
            'Por que FastAPI e não Django neste projeto?': 'explain',
            'Compare a solução local com a versão hospedada e explique o custo de manutenção.': 'explain',
            'Explain the choices in the existing software blueprint.': 'explain',
            'Meu aplicativo tem um bug: as chamadas de API são repetidas a cada renderização do componente. '
            'Como corrigir o loop mantendo a arquitetura que já escolhemos?': 'debug',
            'TypeError: object is not iterable. Me ajude a corrigir isso.': 'debug',
        }
        for text, expected in samples.items():
            with self.subTest(text=text):
                self.assertEqual(route_intent(text, project())['intent'], expected)

    def test_product_briefs_cover_saas_cli_extension_and_game(self):
        samples = [
            'O produto é um SaaS para pequenos teatros. Cada cliente precisa publicar a programação, '
            'vender ingressos e gerenciar os convites dos espectadores.',
            'Preciso criar um CLI para reconciliar dados de inventário usando arquivos CSV.',
            'Quero fazer uma extensão para salvar as cores usadas em sites.',
            'Vou desenvolver um jogo simples de adivinhar palavras.',
            'Nosso software permite que universidades controlem laboratórios, gerenciem agendamentos '
            'e exportem relatórios mensais de ocupação.',
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(route_intent(text, {'messages': []})['intent'], 'plan')

    def test_explicit_edits_and_short_fact_answers_refine_with_context(self):
        samples = [
            'Remova as funções sociais. Quero somente um caderno particular.',
            'Troque o banco remoto por armazenamento no aparelho.',
            'Agora quero suportar equipes com dez pessoas.',
            'Meu orçamento é cem reais por mês.',
            'Brasil',
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(route_intent(text, project())['intent'], 'refine')
        self.assertEqual(route_intent('sim', project(pending=True))['intent'], 'refine')
        self.assertEqual(route_intent('Chile', project(pending=True))['intent'], 'refine')

    def test_acknowledgements_do_not_research_again(self):
        for text in ('Obrigado!', 'Entendi.', 'ok', 'Thanks!', 'Oi'):
            with self.subTest(text=text):
                self.assertEqual(route_intent(text, project())['intent'], 'chat')

    def test_confirmation_keeps_build_tools_compatibility(self):
        question = 'Quais ferramentas preciso usar para fazer esse software?'
        messages = [{'role': 'user', 'content': question}, {'role': 'assistant', 'content': 'Vamos definir a arquitetura?'}]
        self.assertTrue(wants_build_tools('isso', messages))
        self.assertEqual(route_intent('isso', {'messages': messages})['intent'], 'plan')

    def test_routing_does_not_change_saved_state(self):
        original = project(pending=True)
        before = copy.deepcopy(original)
        route_intent('Por que usar essa linguagem?', original)
        self.assertEqual(original, before)

    def test_unavailable_model_keeps_explicit_rules_and_safe_fallback(self):
        with patch('phase0.conversation.intent_ml.classify', side_effect=OSError('not found')):
            self.assertEqual(route_intent('zqxv flbrz qyzx', project())['intent'], 'chat')
            self.assertEqual(route_intent('Explique essa recomendação.', project())['intent'], 'explain')
            self.assertEqual(route_intent('Quero criar um app de notas.', project())['intent'], 'plan')

    def test_ml_refinement_requires_existing_product_context(self):
        guessed = {'label': 'refine', 'score': -3.2, 'margin': 0.7}
        with patch('phase0.conversation.intent_ml.classify', return_value=guessed):
            self.assertEqual(route_intent('interessante ideia adicional', {'messages': []})['intent'], 'chat')


if __name__ == '__main__':
    unittest.main()
