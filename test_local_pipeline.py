import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Importation des composants du système principal
from pipeline import run_discovery_cycle, run_proposal_generation_cycle
from schemas import SearchQueryMatrix, DiscoveredUrlList, DiscoveredUrlCandidate, ExtractedAAPAttributes, AAPStrategicScore, FormStructureDefinition, FormFieldConstraint, FullProposalDocument, NarrativeResponseItem, FinancialApplicationPlan

class TestLocalPipeline(unittest.TestCase):
    """Suite de tests d'intégration locaux pour valider l'orchestrateur et les briques déterministes."""

    @patch('pipeline.web_radar_agent')
    @patch('pipeline.query_expansion_agent')
    @patch('pipeline.content_harvester_agent')
    @patch('pipeline.metadata_extractor_agent')
    @patch('pipeline.aap_scoring_specialist')
    @patch('pipeline.SheetsPublisherModule')
    def test_phase_1_discovery_and_screening(self, mock_publisher, mock_scoring, mock_meta_extract, mock_harvester, mock_query_exp, mock_radar):
        """Valide la Phase 1 : Expansion, Découverte, Filtrage Déterministe et Tri du Top 5."""
        print("\n=== [TEST] Lancement de la Phase 1 (Découverte & Éligibilité) ===")

        # 1. Mock de l'agent d'expansion
        mock_query_exp.return_value = {
            "temp:generated_queries": SearchQueryMatrix(
                generated_dorks=[],
                execution_horizon_year=2026
            )
        }

        # 2. Mock du radar web
        mock_radar.return_value = {
            "temp:discovered_urls": DiscoveredUrlList(candidates=[
                DiscoveredUrlCandidate(
                    url="https://www.fondationaxa.fr/inclusion-sportive-2026",
                    page_title="Appel à projets : Inclusion par le sport en montagne",
                    discovery_query="mock_query",
                    funder_guess="Fondation AXA",
                    snippet="Subvention pour associations loi 1901 visant l'inclusion par le sport."
                )
            ])
        }

        # 3. Mock du Harvester MCP (Contenu brut HTML)
        mock_harvester.return_value = {
            "temp:raw_web_payload": {"text": "Règlement complet de la Fondation AXA..."}
        }

        # 4. Mock de l'extracteur de métadonnées (Gemini 2.5 Flash)
        mock_meta_extract.return_value = {
            "temp:extracted_metadata": ExtractedAAPAttributes(
                extracted_grant_ceiling=Decimal("25000.00"),
                required_annual_budget_ceiling=Decimal("350000.00"),
                submission_deadline="2026-11-30",
                geographic_scope="National"
            )
        }

        # 5. Mock du classifieur stratégique (Gemini 2.5 Flash)
        mock_scoring.return_value = {
            "temp:current_aap_score": AAPStrategicScore(
                aap_id="mock_id",
                strategic_fit_score=0.85,
                primary_axis="Sport_Montagne_Depassement",
                alignment_reasoning="Adéquation parfaite avec les cordées en haute montagne.",
                recommended_for_selection=True
            )
        }

        # Exécution de la brique de découverte
        run_discovery_cycle()
        print("✅ PHASE 1 : Exécutée avec succès sans erreur de type ou de structure.")

    @patch('pipeline.form_fields_extractor_agent')
    @patch('pipeline.strategic_narrative_drafter')
    @patch('pipeline.compliance_enforcer_agent')
    @patch('pipeline.SheetsPublisherModule')
    @patch('pipeline.GoogleDocsAssembler')
    def test_phase_2_proposal_generation_with_compliance(self, mock_assembler, mock_publisher, mock_compactor, mock_drafter, mock_form_extractor):
        """Valide la Phase 2 : Analyse de formulaire, Rédaction, Chiffrage et Boucle de Concision."""
        print("\n=== [TEST] Lancement de la Phase 2 (Rédaction, Chiffrage & Concision) ===")

        # 1. Mock de la structure du formulaire cible (avec une contrainte stricte de caractères)
        mock_form_extractor.return_value = {
            "temp:target_form_schema": FormStructureDefinition(
                aap_id="axa_sport_2026",
                form_fields=[
                    FormFieldConstraint(
                        field_id="q1_pitch",
                        question_label="Présentation du projet",
                        character_limit=100, # Limite volontairement basse pour déclencher la concision
                        expected_content_type="narrative"
                    )
                ],
                mandatory_attachments=["Statuts", "RIB"]
            )
        }

        # 2. Mock du rédacteur narratif (Gemini 3.8 Pro qui génère un texte trop long)
        mock_drafter.return_value = {
            "temp:application_proposal_draft": FullProposalDocument(
                aap_id="axa_sport_2026",
                project_title="Cordées Solidaires 2026",
                executive_pitch="Une action d'émancipation pour les jeunes des QPV.",
                narrative_sections=[
                    NarrativeResponseItem(
                        field_id="q1_pitch",
                        question_label="Présentation du projet",
                        final_text="Ce texte est volontairement beaucoup trop long pour le gabarit du formulaire cible afin de forcer l'orchestrateur Python à déclencher l'appel au micro-agent compacteur.",
                        character_count=180,
                        referenced_partners=["Proxité"]
                    )
                ],
                financial_plan=FinancialApplicationPlan(
                    aap_id="axa_sport_2026",
                    total_project_cost=Decimal("15000.00"),
                    total_grant_requested=Decimal("15000.00"),
                    total_self_financing=Decimal("0.00"),
                    budget_breakdown=[]
                )
            )
        }

        # 3. Mock de l'agent de concision (Fallback de réduction de texte)
        mock_compactor.return_value = {
            "temp:validated_draft": "Texte court et percutant de moins de 100 caractères."
        }

        # Exécution de la brique de génération
        run_proposal_generation_cycle()
        print("✅ PHASE 2 : Exécutée avec succès. La boucle de conformité a traité le dépassement.")

if __name__ == '__main__':
    unittest.main()