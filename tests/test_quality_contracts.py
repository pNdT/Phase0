"""Behavioral contracts from the live 2026-09-27 quality evaluation.

These tests supply accurate, quoted facts directly to isolate decision defects
from extraction mistakes. They use no network or model; the live evaluation is
still needed to assess the complete conversation and research pipeline.
"""
import re
import unittest

from phase0 import planner, requirements, research
from phase0.conversation import normalize, route_intent
from phase0.core import blank_profile


def project(**facts):
    profile = blank_profile()
    for key, value in facts.items():
        profile[key] = {"value": value, "evidence": value}
    return {"profile": profile, "messages": [], "dossier": None}


def dossier(current, brief):
    return planner.build_dossier(current, brief, "test:local")


def pending_text(result):
    return normalize(" ".join(result.get("pending", [])))


def recovered_specification(text):
    """Exercise the literal recovery used when an LLM omits explicit facts."""
    current = project()
    updates, _ = requirements.quoted_updates({}, text, planning=True)
    requirements.apply_updates(current, updates, text)
    return requirements.specification(current, text)


class QualityContracts(unittest.TestCase):
    def test_personal_local_dashboard_with_external_stock_api_is_not_offline(self):
        description = ('Painel pessoal de ações brasileiras B3 e dividendos. '
                       'Usarei só no meu computador e preciso de uma API de dados.')
        result = dossier(project(product=description, features=description,
                                 privacy='Usarei só no meu computador',
                                 integrations='Preciso de uma API de dados de ações B3'), description)
        self.assertTrue(result['signals']['personal'])
        self.assertTrue(result['signals']['integrations'])
        self.assertFalse(result['signals']['offline'])
        self.assertIn('stock_data', research.allowed_topics(result['brief'], result))
        scheduled = dossier(project(product=description,
                                    features=description+' Atualização a cada 15 minutos.',
                                    integrations='Preciso de uma API de dados de ações B3'),
                            description+' Atualização a cada 15 minutos.')
        self.assertNotIn('Definir a frequência', ' '.join(scheduled['pending']))

    def test_portuguese_no_is_not_an_english_negation_of_mobile_or_cli(self):
        for description, expected in [
            ('Quero um aplicativo Android no celular, pessoal e offline.', 'mobile'),
            ('Quero uma ferramenta de linha de comando no Windows, pelo terminal, sem interface gráfica.', 'cli'),
        ]:
            with self.subTest(description=description):
                current = project(features=description, platform=description, privacy=description)
                dossier = planner.build_dossier(current, description, 'test:local')
                self.assertEqual(dossier['platform'], expected)

    def test_removing_duplicate_rows_does_not_negate_csv_output(self):
        text=('Quero um CLI Python que lê arquivos CSV, valida colunas, remove linhas duplicadas '
              'e grava um CSV consolidado; sem banco nem serviços externos.')
        _, signals, capabilities, _ = recovered_specification(text)
        self.assertIn('file_processing',capabilities)
        self.assertTrue(signals['file_processing'])

    def test_named_removal_is_refinement_and_drops_old_capabilities(self):
        prior = project(features='Painel pessoal com Strava, Valorant e criptomoedas', platform='web')
        prior['dossier'] = planner.build_dossier(prior, 'Painel pessoal com Strava, Valorant e criptomoedas', 'test:local')
        correction = 'Correção: removi Strava, Valorant e criptomoedas; quero só um cronômetro local, sem integrações externas e sem IA.'
        self.assertEqual(route_intent(correction, prior)['intent'], 'refine')
        facts, _ = requirements.quoted_updates({}, correction, planning=True)
        requirements.apply_updates(prior, facts, correction, refine=True)
        revised = planner.build_dossier(prior, correction, 'test:local')
        self.assertEqual(revised['capabilities'], ['timer'])
        self.assertFalse(revised['integrations'])
        self.assertNotIn('crypto_data', research.allowed_topics(revised['brief'], revised))

    def test_explicitly_free_product_does_not_enable_payments(self):
        for statement in (
            "gratuito para todos, sem assinatura paga nem checkout",
            "Não vou cobrar; sem pagamentos online",
            "No subscription, no paid plans, no checkout",
        ):
            with self.subTest(statement=statement):
                current = project(platform="web", features="contas de voluntários e pedidos de adoção",
                                  monetization=statement, budget="R$ 100 por mês para infraestrutura")
                result = dossier(current, "Site de adoção de animais")
                self.assertFalse(result["signals"]["paid"])
                self.assertEqual(result["payments"], [])
                self.assertTrue(result["signals"]["multiuser"], "Free does not mean single-user")

    def test_free_access_is_not_a_zero_infrastructure_budget(self):
        current = project(platform="web", product="Site de ONG de adoção",
                          features="contas e pedidos de adoção", monetization="Será gratuito para todos")
        result = dossier(current, "Quero criar um site de adoção de animais gratuito para todos, com contas de voluntários e pedidos. A infraestrutura pode custar até R$ 100 por mês.")
        self.assertFalse(result["signals"]["zero_budget"], "Product price is not the infrastructure budget")
        self.assertIsNone(result["costs"]["total_monthly"], "An unverified amount is not a confirmed quote")

    def test_budget_recovery_keeps_free_product_and_cost_in_the_same_sentence_separate(self):
        for text in (
            "O site será gratuito para todos e o orçamento de infraestrutura é R$ 100 por mês.",
            "Não quero orçamento zero; tenho até R$ 200 por mês.",
            "O orçamento não é zero nem grátis: posso gastar R$ 200.",
        ):
            with self.subTest(text=text):
                _, signals, _, _ = recovered_specification(text)
                self.assertFalse(signals["zero_budget"], "Quoted words must retain their object and negation")

    def test_no_subscription_does_not_cancel_one_time_payment(self):
        _, signals, _, _ = recovered_specification("Vou cobrar por compra, sem assinatura.")
        self.assertTrue(signals["paid"], "A one-time paid purchase remains a payment requirement")

    def test_negated_mandatory_label_does_not_make_preferences_required(self):
        _, _, _, constraints = recovered_specification("Não é obrigatório usar Vue; prefiro Django.")
        self.assertEqual(constraints["required_tools"], [], "Preference and mandatory constraint are different")

    def test_no_local_accounts_does_not_remove_sso_login(self):
        _, signals, _, _ = recovered_specification("Quero login com SSO, sem contas locais.")
        self.assertTrue(signals["multiuser"], "External login still requires authenticated user isolation")

    def test_positive_only_clause_does_not_inherit_the_previous_negation(self):
        _, signals, capabilities, _ = recovered_specification("Não quero criptomoedas, só ações da B3 e dividendos.")
        self.assertIn("stock_data", capabilities)
        self.assertNotIn("crypto_data", capabilities)
        self.assertTrue(signals["stock_data"])

    def test_local_speech_stays_enabled_without_external_integrations_or_generative_chat(self):
        _, signals, capabilities, constraints = recovered_specification(
            "Quero transcrever áudios offline em português, sem IA generativa nem integrações externas.")
        self.assertIn("speech_recognition", capabilities)
        self.assertTrue(signals["offline"])
        self.assertFalse(signals["integrations"])
        self.assertTrue(constraints["no_integrations"])

    def test_negated_integrations_do_not_turn_a_brochure_into_a_dynamic_app(self):
        for statement in ("não preciso de integrações", "não quero integrações externas", "no external integrations"):
            with self.subTest(statement=statement):
                current = project(platform="web", features="site institucional com blog SEO", integrations=statement)
                result = dossier(current, "Site institucional de uma oficina")
                self.assertFalse(result["signals"]["integrations"])
                self.assertTrue(result["signals"]["static"])
                self.assertEqual(result["integrations"], [])

    def test_static_prompts_do_not_require_unselected_database_or_api(self):
        current = project(platform="web", features="site institucional com blog SEO sem login e sem integrações")
        result = dossier(current, "Site institucional simples")
        self.assertIsNotNone(result["selected_stack"])
        self.assertNotIn("sqlite", result["selected_stack"]["tool_ids"])
        self.assertNotIn("supabase", result["selected_stack"]["tool_ids"])
        self.assertTrue(result["prompts"])
        for prompt in result["prompts"]:
            # The preceding JSON includes user facts; assess the actual build instruction.
            instruction = normalize(prompt["text"].rsplit("\n\n", 1)[-1])
            self.assertNotRegex(instruction, r"modele[^.]*migrations|model[^.]*migrations")
            self.assertNotRegex(instruction, r"implemente persistencia compativel com o banco selecionado")
            self.assertNotRegex(instruction, r"implement persistence compatible with the selected database")

    def test_cli_is_local_file_processing_or_explicitly_unsupported(self):
        current = project(platform="linha de comando no terminal Windows",
                          features="CSV local: ler arquivos, validar colunas, deduplicar e consolidar; sem interface gráfica, sem servidor, sem banco de dados",
                          privacy="arquivos ficam no computador", integrations="sem serviços externos")
        result = dossier(current, "Software CLI em Python para consolidar arquivos CSV")
        if result["status"] == "blocked":
            self.assertIsNone(result["selected_stack"])
            self.assertTrue(result["pending"])
            return
        self.assertEqual(result["platform"], "cli")
        ids = set(result["selected_stack"]["tool_ids"])
        self.assertFalse(ids & {"vite-react", "nextjs", "astro", "fastapi", "supabase", "sqlite", "postgres", "pgvector", "cloudflare-pages", "tauri", "flutter"})
        self.assertTrue(all(tool["local"] for tool in result["tools"]))
        self.assertNotRegex(normalize(" ".join(prompt["title"] for prompt in result["prompts"])),
                            r"interface e experiencia|interface and experience")
        topics = set(research.allowed_topics(result["brief"], result))
        self.assertFalse(topics & {"ui_components", "backend", "database"})

    def test_mandatory_technologies_are_respected_or_the_catalog_abstains(self):
        current = project(platform="web", features="estoque, login para funcionários e relatórios",
                          technical_comfort="Vue, Django e PostgreSQL são obrigatórios; não trocar")
        result = dossier(current, "Site de controle de estoque da minha loja")
        if result["status"] == "blocked":
            self.assertIsNone(result["selected_stack"])
            self.assertEqual(result["prompts"], [])
            self.assertRegex(pending_text(result), r"vue|django|obrigator|restri")
            return
        names = normalize(" ".join(tool["name"] for tool in result["tools"]))
        self.assertTrue(all(name in names for name in ("vue", "django", "postgres")), names)

    def test_updated_current_requirements_remove_historical_integrations(self):
        current = project(platform="web", product="Painel pessoal",
                          features="apenas cronômetro local", integrations="sem integrações externas")
        stale = "Painel com Strava, Valorant e criptomoedas. Atualização: removi tudo; apenas cronômetro local."
        result = dossier(current, stale)
        self.assertFalse(result["signals"]["integrations"])
        self.assertEqual(result["integrations"], [])
        self.assertFalse(result["signals"]["realtime"])
        topics = set(research.allowed_topics(result["brief"], result))
        self.assertFalse(topics & {"strava", "valorant", "market_data", "stock_data", "crypto_data"})

    def test_offline_speech_product_keeps_the_actual_model_capability(self):
        current = project(product="Transcrição de áudio de reuniões em português", platform="desktop",
                          features="transcrever arquivos de áudio, reconhecimento de fala em português",
                          privacy="100% offline, áudios confidenciais ficam no computador",
                          technical_comfort="Windows, 8 GB RAM, sem GPU dedicada")
        result = dossier(current, "Aplicativo desktop de reconhecimento de fala 100% offline; não quero chat nem geração de texto")
        topics = research.allowed_topics(result["brief"], result)
        speech_search = any(re.search(r"speech|asr|transcri|fala", topic) for topic in topics)
        explicit_gap = bool(re.search(r"fala|transcri|speech", pending_text(result)))
        self.assertTrue(speech_search or explicit_gap, "Recognize ASR or state an explicit coverage gap")
        self.assertNotIn("ollama", (result["selected_stack"] or {}).get("tool_ids", []),
                         "A chat model must not silently stand in for speech recognition")
        self.assertTrue(all(tool["local"] for tool in result["tools"]))

    def test_brazilian_equities_do_not_become_crypto_searches(self):
        current = project(product="Painel pessoal de ações brasileiras B3 e dividendos", platform="web",
                          features="ações B3, dividendos, gráficos; atualização a cada 15 minutos; não quero criptomoedas",
                          integrations="API para ações brasileiras B3 e dividendos", budget="R$ 50 por mês para API de dados")
        result = dossier(current, "Painel pessoal de ações brasileiras B3, sem criptomoedas")
        topics = research.allowed_topics(result["brief"], result)
        stock_search = any(re.search(r"stock|b3|equities|acoes", topic) for topic in topics)
        explicit_gap = bool(re.search(r"acoes|b3|stock|dividend", pending_text(result)))
        self.assertTrue(stock_search or explicit_gap, "Brazilian stock coverage must be researched or explicitly pending")
        self.assertFalse(any("crypto" in topic for topic in topics))
        if "market_data" in topics:
            self.assertNotRegex(normalize(str(research.TOPICS.get("market_data", ""))), r"crypto|criptomoeda")

    def test_realtime_booking_does_not_create_market_data_requirements(self):
        current = project(product="SaaS de agendamento de salões", platform="web",
                          features="contas por salão, reservas, lembretes, calendário em tempo real para evitar dupla reserva",
                          monetization="Cobrar R$ 49 por mês por salão via Pix", geography="Brasil")
        result = dossier(current, "SaaS web de agendamento para salões")
        self.assertTrue(result["signals"]["multiuser"])
        self.assertTrue(result["signals"]["realtime"])
        self.assertNotRegex(pending_text(result), r"fornecedor de cotacoes|market.data provider")
        self.assertFalse(set(research.allowed_topics(result["brief"], result)) & {"market_data", "stock_data", "crypto_data"})

    def test_explanations_and_debugging_preserve_the_existing_plan(self):
        current = project(platform="web", features="painel pessoal com widgets")
        current["dossier"] = dossier(current, "Meu painel pessoal web")
        for text in (
            "Por que você escolheu SQLite em vez de Supabase? Explique as diferenças para o meu produto.",
            "Estou implementando o painel web e encontrei um erro: o widget de cotação faz uma chamada da API em toda renderização React. Como evito esse loop e organizo o cache sem mudar a arquitetura?",
            "Explain how this software stores the data and why you chose the database.",
        ):
            with self.subTest(text=text):
                self.assertFalse(planner.should_plan(text, current), "Answer the question instead of regenerating a dossier")

    def test_saas_description_starts_a_plan_without_special_dossier_wording(self):
        current = project()
        text = ("Quero criar um SaaS web para salões de beleza. Cada salão terá sua conta e profissionais. "
                "Os clientes reservam horários e recebem lembretes. Vou cobrar uma assinatura via Pix.")
        self.assertTrue(planner.should_plan(text, current), "SaaS is a software creation request")


if __name__ == "__main__":
    unittest.main()
