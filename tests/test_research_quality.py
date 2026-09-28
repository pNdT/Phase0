"""Research regression contracts; synthetic sources, no network or inference."""
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from phase0 import planner, research


def response(value):
    return {'message':{'content':json.dumps(value)}}


def understanding(platform='web', capabilities=(), constraints=None, **signals):
    return {'language':'pt','platform':platform,'signals':signals,
            'capabilities':list(capabilities),'constraints':constraints or {}}


class ResearchQualityTests(unittest.TestCase):
    def test_flutter_directory_lookup_does_not_accept_app_word_or_signup_link(self):
        markdown='''| [Sign up](https://example.test/signup) | Try our mobile app |
| [Axolotl](https://example.test/axolotl) | Axolotl pictures app |
| [Dog](https://example.test/dog) | Random dog data in your app |
| [Flutter SDK](https://example.test/flutter) | Flutter mobile SDK |'''
        results=research.registry_results(markdown,'public-apis','mobile','https://directory.test')
        self.assertEqual([r['name'] for r in results],['Flutter SDK'])
        self.assertFalse(research.source_supports('public-apis','mobile'))

    def test_explicit_capabilities_override_stale_brief_and_removed_integrations(self):
        current=understanding(capabilities=['timer'], constraints={'no_integrations':True}, offline=True)
        topics=research.allowed_topics('Antes: Strava, Valorant e criptomoedas.',current)
        self.assertIn('timer',topics)
        self.assertTrue(set(topics).isdisjoint({'strava','valorant','market_data','crypto_data','stock_data'}))

    def test_local_browser_timer_excludes_backend_and_database_searches(self):
        current=understanding(capabilities=['timer'],constraints={'no_integrations':True},timer=True,personal=True)
        current['selected_stack']={'id':'browser-local','tool_ids':['browser-native']}
        topics=research.allowed_topics('Um cronômetro local',current)
        self.assertIn('timer',topics)
        self.assertNotIn('backend',topics)
        self.assertNotIn('database',topics)

    def test_cpu_offline_speech_selects_asr_instead_of_coder_or_chat_models(self):
        current=understanding('desktop',['speech'],offline=True,ai=True,speech=True)
        topics=research.allowed_topics('Transcrever reuniões em português; CPU, 8 GB.',current)
        self.assertIn('speech_recognition',topics)
        self.assertNotIn('ai_models',topics)
        self.assertTrue(research.source_supports('huggingface','speech_recognition',current))
        self.assertFalse(research.source_supports('huggingface','desktop',current))
        with patch('phase0.research.fetch',return_value=[]) as fetch:
            research.run_task({'source':'huggingface','topic':'speech_recognition','tool_id':''},{})
        query=parse_qs(urlparse(fetch.call_args.args[0]).query)
        self.assertEqual(query['filter'],['automatic-speech-recognition'])
        self.assertNotIn('coder',fetch.call_args.args[0])

    def test_b3_requires_stock_coverage_and_cannot_be_replaced_with_crypto(self):
        current=understanding(capabilities=['stock_data'],stock_data=True,crypto_data=False)
        topics=research.allowed_topics('Ações B3; não quero criptomoedas',current)
        self.assertIn('stock_data',topics)
        self.assertTrue(set(topics).isdisjoint({'crypto_data','market_data'}))
        markdown='''| [Crypto](https://example.test/crypto) | Cryptocurrency prices worldwide |
| [US stocks](https://example.test/us) | US stock prices and dividends |
| [Brazil](https://example.test/br) | Brazil B3 stock prices and dividends |
| [Tourism](https://example.test/travel) | Brazil tourism data |'''
        results=research.registry_results(markdown,'public-apis','stock_data','https://directory.test')
        self.assertEqual([r['name'] for r in results],['Brazil'])

    def test_ollama_focuses_a_missing_explicit_stock_capability(self):
        generic={'source':'github','topic':'dashboard','tool_id':''}
        stock={'source':'public-apis','topic':'stock_data','tool_id':''}
        broader={'source':'github','topic':'stock_data','query_id':'b3-api'}
        replies=iter([response({'tasks':[generic]}),response({'tasks':[stock]}),response({'tasks':[broader]})])
        chosen=[]
        def request(*args,**kwargs):
            chosen.append(next(replies))
            return chosen[-1]
        with patch('phase0.research.run_task',return_value=[]) as run:
            report=research.research_product({'profile':{}},'Ações brasileiras B3','local',request,
                planner.catalog(),understanding=understanding(capabilities=['stock_data'],dashboard=True,stock_data=True))
        self.assertEqual(len(chosen),3)
        self.assertEqual([call.args[0]['topic'] for call in run.call_args_list],['stock_data','dashboard','stock_data'])
        self.assertEqual(report['tasks'][-1]['query'],'B3 API')
        self.assertFalse(any(task['topic']=='crypto_data' for task in report['tasks']))

    def test_cli_research_does_not_add_ui_database_server_or_service_directory(self):
        current=understanding('cli',['file_processing'],
            {'no_ui':True,'no_database':True,'no_backend':True,'no_integrations':True},offline=True)
        topics=research.allowed_topics('Python CSV pelo terminal',current)
        self.assertEqual(set(topics),{'cli','file_processing'})
        self.assertTrue(all(not research.source_supports('free-for-dev',t,current) for t in topics))
        self.assertFalse(research.topic_matches('Random files generated for a mobile app','cli'))
        generic={'source':'github','topic':'cli','name':'example/jc','stars':500,
                 'description':'Python CLI to parse command output into JSON'}
        self.assertFalse(research.relevant_resource(generic,'cli',current))

    def test_local_sqlite_app_does_not_search_remote_postgres_by_default(self):
        current=understanding('mobile',offline=True,personal=True)
        current['selected_stack']={'id':'mobile-local','tool_ids':['flutter','sqlite']}
        topics=research.allowed_topics('Diário Android offline',current)
        self.assertNotIn('database',topics)
        self.assertIn('mobile',topics)

    def test_required_vue_and_django_change_query_subjects(self):
        current=understanding(constraints={'required_tools':['vue','django','postgres']},dashboard=True)
        topics=research.allowed_topics('Estoque',current)
        self.assertIn('vue_ui',topics)
        self.assertIn('django_backend',topics)
        self.assertNotIn('dashboard',topics)
        self.assertNotIn('backend',topics)

    def test_booking_realtime_does_not_imply_financial_market_research(self):
        current=understanding(capabilities=['booking'],booking=True,realtime=True,multiuser=True,paid=True)
        topics=research.allowed_topics('Calendário em tempo real',current)
        self.assertIn('booking',topics)
        self.assertTrue(set(topics).isdisjoint({'crypto_data','stock_data','market_data'}))

    def test_exact_quote_without_matching_capability_is_not_recommended(self):
        task={'source':'huggingface','topic':'speech_recognition','tool_id':''}
        resource={'id':'hf:coder','name':'Coder','url':'https://huggingface.co/example/coder',
            'description':'A language model for code generation', 'source':'huggingface','topic':'speech_recognition'}
        replies=iter([response({'tasks':[task]})])
        with patch('phase0.research.run_task',return_value=[resource]):
            report=research.research_product({'profile':{}},'ASR','local',lambda *a,**k:next(replies),
                planner.catalog(),understanding=understanding('desktop',['speech'],speech=True,offline=True))
        self.assertEqual(report['results'],[])
        self.assertEqual(report['recommendations'],[])
        self.assertEqual(report['tasks'][0]['filtered_count'],1)

    def test_relevant_asr_candidate_still_exposes_hardware_and_language_checks(self):
        task={'source':'huggingface','topic':'speech_recognition','tool_id':''}
        resource={'id':'hf:example/asr','name':'ASR','url':'https://huggingface.co/example/asr',
            'description':'Model metadata: automatic-speech-recognition; multilingual',
            'source':'huggingface','topic':'speech_recognition'}
        item={'id':resource['id'],'purpose':'model_candidate','evidence':'automatic-speech-recognition',
              'relevance_topic':'speech_recognition'}
        replies=iter([response({'tasks':[task]}),response({'recommendations':[item]})])
        with patch('phase0.research.run_task',return_value=[resource]):
            report=research.research_product({'profile':{}},'ASR','local',lambda *a,**k:next(replies),
                planner.catalog(),understanding=understanding('desktop',['speech'],speech=True,offline=True))
        selected=report['recommendations'][0]
        self.assertEqual(selected['relevance_topic'],'speech_recognition')
        self.assertTrue(any('Portuguese' in check for check in selected['verification_needed']))
        self.assertTrue(any('CPU' in check for check in selected['verification_needed']))

    def test_model_selects_ids_while_source_controls_type_and_evidence(self):
        task={'source':'public-apis','topic':'strava','tool_id':''}
        resource={'id':'public-apis:https://example.test/strava','name':'Strava',
                  'url':'https://example.test/strava','description':'| [Strava](https://example.test/strava) | Activities API |',
                  'source':'public-apis','topic':'strava'}
        replies=iter([response({'tasks':[task]}),response({'recommendations':[resource['id']]})])
        with patch('phase0.research.run_task',return_value=[resource]):
            report=research.research_product({'profile':{}},'Strava','local',lambda *a,**k:next(replies),
                planner.catalog(),understanding=understanding(capabilities=['strava'],strava=True))
        selected=report['recommendations'][0]
        self.assertEqual(selected['purpose'],'api_candidate')
        self.assertEqual(selected['evidence'],resource['description'])
        self.assertEqual(report['status'],'complete')

    def test_research_does_not_offer_desktop_timers_to_a_web_product(self):
        current=understanding(capabilities=['timer'],timer=True)
        desktop={'source':'github','topic':'timer','name':'macOS/Timer','description':'Pomodoro timer for macOS menu bar','stars':250}
        self.assertFalse(research.relevant_resource(desktop,'timer',current))
        web={**desktop,'name':'example/web-timer','description':'JavaScript Pomodoro timer for web browsers'}
        self.assertTrue(research.relevant_resource(web,'timer',current))

    def test_booking_references_need_quality_and_matching_domain(self):
        current=understanding(capabilities=['booking'],booking=True)
        current['brief']='SaaS de agendamento para salões de beleza'
        medical={'source':'github','topic':'booking','name':'demo/clinic',
                 'description':'Healthcare appointment booking calendar with patients','stars':300}
        weak={**medical,'name':'demo/salon','description':'Salon appointment booking calendar','stars':2}
        good={**weak,'stars':120}
        self.assertFalse(research.relevant_resource(medical,'booking',current))
        self.assertFalse(research.relevant_resource(weak,'booking',current))
        self.assertTrue(research.relevant_resource(good,'booking',current))

    def test_database_directory_skips_design_geolocation_and_analytics_entries(self):
        markdown='''* [DB Designer](https://example.test/designer) - Cloud-based Database schema design and modeling tool.
* [DB-IP](https://example.test/ip) - IP geolocation API with a database.
* [EverSQL](https://example.test/optimizer) - Database optimization and SQL analyzer.
* [Example Postgres](https://example.test/postgres) - Managed PostgreSQL database hosting for applications.'''
        result=research.registry_results(markdown,'free-for-dev','database','https://example.test/index')
        self.assertEqual([item['name'] for item in result],['Example Postgres'])

    def test_b3_analysis_without_a_data_api_is_not_a_data_source(self):
        current=understanding(capabilities=['stock_data'],stock_data=True)
        resource={'source':'github','topic':'stock_data','name':'example/b3analysis','stars':128,
                  'description':'Agente de análise de ações brasileiras (B3) com Claude Code — sem API keys'}
        self.assertFalse(research.relevant_resource(resource,'stock_data',current))

    def test_windows_portuguese_asr_filters_unrelated_model_metadata(self):
        current=understanding('desktop',['speech'],speech=True,offline=True)
        current['brief']='Windows offline, transcrição em português'
        base={'source':'huggingface','topic':'speech_recognition',
              'description':'Model metadata: automatic-speech-recognition, Portuguese, pt'}
        self.assertTrue(research.relevant_resource({**base,'name':'model/portuguese-asr'},'speech_recognition',current))
        self.assertFalse(research.relevant_resource({**base,'name':'model/coreml','description':base['description']+' coreml'},
                                                    'speech_recognition',current))
        self.assertFalse(research.relevant_resource({**base,'name':'speaker-diarization','description':base['description']+' speaker-diarization'},
                                                    'speech_recognition',current))
        self.assertFalse(research.relevant_resource({**base,'name':'japanese-asr',
                                                    'description':'Model metadata: automatic-speech-recognition, ja'},
                                                    'speech_recognition',current))

    def test_source_topic_mismatch_cannot_execute_network(self):
        task={'source':'public-apis','topic':'mobile','tool_id':''}
        with patch('phase0.research.run_task') as run:
            report=research.research_product({'profile':{}},'Diário Android','local',
                lambda *a,**k:response({'tasks':[task]}),planner.catalog(),
                understanding=understanding('mobile',offline=True))
        run.assert_not_called()
        self.assertEqual(report['status'],'invalid-plan')
        self.assertEqual(len(report['rejected_tasks']),1)
        self.assertTrue(report['gaps'])

    def test_bad_source_topic_pair_does_not_discard_a_valid_model_selected_call(self):
        tasks=[{'source':'public-apis','topic':'mobile','tool_id':''},
               {'source':'github','topic':'mobile','tool_id':''}]
        with patch('phase0.research.run_task',return_value=[]) as run:
            report=research.research_product({'profile':{}},'Diário Android','local',
                lambda *a,**k:response({'tasks':tasks}),planner.catalog(),
                understanding=understanding('mobile',offline=True))
        self.assertEqual(run.call_count,1)
        self.assertEqual(run.call_args.args[0],tasks[1])
        self.assertEqual(report['status'],'partial')
        self.assertEqual(report['rejected_tasks'][0]['source'],'public-apis')
        self.assertEqual(report['tasks'][0]['source'],'github')

    def test_stack_context_contains_only_candidate_tools(self):
        dossier={'selected_stack':{'id':'python-cli','tool_ids':['sqlite']},'alternatives':[],
            'signals':{'static':False,'seo':False,'offline':True,'personal':True},
            'requirements':{},'brief':'local files','language':'pt'}
        requests=[]
        def request(path,payload,**kwargs):
            requests.append(payload)
            return response({'stack_id':'python-cli','primary_reason':'simple_mvp'})
        result=research.choose_stack(dossier,'local',request,planner.catalog())
        context=json.loads(requests[0]['messages'][1]['content'])
        self.assertEqual([tool['id'] for tool in context['tools']],['sqlite'])
        self.assertEqual(requests[0]['options']['num_ctx'],8192)
        self.assertEqual(result['evidence_sources'][0]['tool_id'],'sqlite')


if __name__=='__main__':
    unittest.main()
