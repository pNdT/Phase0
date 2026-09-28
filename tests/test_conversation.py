import unittest
from phase0.core import blank_profile
from phase0.conversation import wants_build_tools
from phase0.planner import build_dossier


class ConversationTests(unittest.TestCase):
    def test_pulse_question_and_confirmation(self):
        question = 'quero saber quais preciso usar para fazer ele'
        self.assertTrue(wants_build_tools(question, []))
        self.assertTrue(wants_build_tools('isso', [{'role': 'user', 'content': question},
                                                 {'role': 'assistant', 'content': 'irrelevant'}]))
        self.assertFalse(wants_build_tools('sim', [{'role': 'user', 'content': 'Meu orçamento é zero'}]))

    def test_integrations_are_not_build_tools(self):
        project = {'profile': blank_profile(), 'messages': [
            {'role': 'user', 'content': 'Pulse reúne widgets de Strava e Valorant em um painel.'}]}
        dossier = build_dossier(project, 'quais ferramentas preciso usar para fazer ele?','local')
        self.assertEqual([i['id'] for i in dossier['integrations']],['strava-api','valorant-api'])
        self.assertNotIn('strava-api',dossier['selected_stack']['tool_ids'])
        self.assertEqual(project['profile'], blank_profile())

    def test_platform_is_not_asked_twice(self):
        project = {'profile': blank_profile(), 'messages': []}
        project['profile']['platform'] = {'value': 'desktop', 'evidence': 'desktop'}
        dossier = build_dossier(project, 'quais ferramentas usar?','local')
        self.assertEqual(dossier['platform'],'desktop')
        self.assertEqual(dossier['selected_stack']['id'],'desktop-local')

    def test_assistant_suggestions_do_not_become_user_integrations(self):
        project = {'profile': blank_profile(), 'messages': [
            {'role': 'assistant', 'content': 'Use Strava e Valorant'}]}
        self.assertEqual(build_dossier(project,'quais ferramentas usar?','local')['integrations'],[])
