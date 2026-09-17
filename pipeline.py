import os
import hashlib
from decimal import Decimal
from datetime import date

from config import logger
from crawl_frontier import CrawlFrontierManager
from sheets_publisher import SheetsPublisherModule
from docs_assembler import GoogleDocsAssembler
from schemas import AAPRawMetadata
from tools import DocumentParserModule, deterministic_nogo_filter, calculate_itemized_budget
from agents import (
    query_expansion_agent, web_radar_agent, content_harvester_agent,
    metadata_extractor_agent, aap_scoring_specialist,
    form_fields_extractor_agent, strategic_narrative_drafter,
    compliance_enforcer_agent
)

# --- Orchestrateur de la Phase 1 (Découverte & Screening) ---

def run_discovery_cycle(dry_run: bool = False):
    """
    Exécute les étapes 1 à 9 de la matrice DAA.
    Inclut les barrières déterministes et le radar hybride.
    """
    frontier = CrawlFrontierManager()
    publisher = SheetsPublisherModule()
    parser = DocumentParserModule()
    scored_aaps = []
    
    logger.info("Démarrage de l'expansion sémantique...")
    
    # On exécute manuellement les agents au lieu d'utiliser le SequentialAgent
    expansion_res = query_expansion_agent.run()
    generated_queries = expansion_res.get("temp:generated_queries")
    
    discovery_result = web_radar_agent.run(queries=generated_queries.model_dump() if generated_queries else None)
    
    discovered_payload = discovery_result.get("temp:discovered_urls")
    discovered_urls = discovered_payload.candidates if discovered_payload else []
    logger.info(f"{len(discovered_urls)} URLs découvertes par le radar.")

    fresh_candidates = frontier.filter_fresh_urls(discovered_urls)
    logger.info(f"{len(fresh_candidates)} nouvelles opportunités identifiées.")

    for candidate in fresh_candidates:
        try:
            logger.info(f"Analyse profonde : {candidate.url}")
            # 4. Extraction via MCP
            harvester_res = content_harvester_agent.run(url=candidate.url)
            raw_payload = harvester_res.get("temp:raw_web_payload", {})
            
            # 5. Parsing (Step 5 - DocumentParserModule)
            full_text = parser.parse(raw_payload)

            # 5b. Extraction de métadonnées par IA
            meta_ext_res = metadata_extractor_agent.run(text=full_text)
            ext_attr = meta_ext_res.get("temp:extracted_metadata")

            # Construction de l'objet Metadata final
            metadata = AAPRawMetadata(
                id=hashlib.sha256(candidate.url.encode()).hexdigest(),
                source_url=candidate.url,
                title=candidate.page_title,
                funder_name=candidate.funder_guess or "Inconnu",
                extracted_grant_ceiling=ext_attr.extracted_grant_ceiling if ext_attr else None,
                required_annual_budget_ceiling=ext_attr.required_annual_budget_ceiling if ext_attr else None,
                submission_deadline=ext_attr.submission_deadline or f"{date.today().year}-12-31",
                geographic_scope=ext_attr.geographic_scope or "National",
                raw_guidelines_text=full_text
            )

            # 6. Filtrage No-Go déterministe
            if not deterministic_nogo_filter(metadata):
                logger.info(f"Skipped: Hors critères financiers pour {metadata.title}")
                continue

            # 7. Scoring d'alignement stratégique
            scoring_res = aap_scoring_specialist.run(aap_metadata=metadata.model_dump())
            score = scoring_res.get("temp:current_aap_score")
            
            if score:
                # 8. Calcul du score composite (0.6 Fit + 0.4 Budget)
                # S_budget est normalisé sur une base de 20 000€ (montant cible moyen)
                grant_ceiling = metadata.extracted_grant_ceiling or Decimal("0")
                s_budget = float(min(Decimal("1.0"), grant_ceiling / Decimal("20000.0")))
                
                composite_score = (0.6 * score.strategic_fit_score) + (0.4 * s_budget)
                score.strategic_fit_score = composite_score # Mise à jour pour le tri
                
                scored_aaps.append({"metadata": metadata, "score": score})
                # Marquer comme traité dans Redis uniquement après scoring réussi
                frontier.mark_as_processed(candidate.url, metadata.id)

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {candidate.url}: {e}")

    # 8. Tri par score (Étape déterministe)
    top_5 = sorted(scored_aaps, key=lambda x: x['score'].strategic_fit_score, reverse=True)[:5]

    # 9. Publication Google Sheets (HITL #1)
    if top_5:
        if dry_run:
            logger.info(f"[DRY-RUN] Top 5 identifié : {[x['metadata'].title for x in top_5]}")
        else:
            publisher.sync_top_opportunities(top_5)
            logger.info("Phase 1 terminée. HITL #1 activé sur Google Sheets.")

def run_proposal_generation_cycle(dry_run: bool = False):
    """
    Exécute les étapes 10 à 15 du DAA.
    Déclenché après arbitrage humain (HITL #1).
    """
    publisher = SheetsPublisherModule()
    assembler = GoogleDocsAssembler()
    
    # 10. Récupération des choix humains
    approved_tasks = publisher.get_approved_aaps()
    
    for task in approved_tasks:
        logger.info(f"Démarrage rédaction pour : {task['title']}")
        
        # 11. Extraction dynamique du formulaire (MCP)
        form_res = form_fields_extractor_agent.run(portal_url=task['url'])
        form_struct = form_res.get("temp:target_form_schema")
        
        # 12. Ventilation Budgétaire Déterministe (Calcul pur Python)
        budget_data = calculate_itemized_budget(
            aap_id=hashlib.sha256(task['url'].encode()).hexdigest(),
            total_grant_requested=15000.00
        )
        
        # 13. Rédaction Narrative (Gemini 3.8 Pro)
        draft_res = strategic_narrative_drafter.run(
            aap_context=f"URL: {task['url']}, Titre: {task['title']}",
            target_grant=15000.00,
            form_fields=form_struct.model_dump() if form_struct else None,
            itemized_budget=budget_data
        )
        
        proposal = draft_res.get("temp:application_proposal_draft")
        
        if proposal:
            # 14. Contrôle de conformité des limites (Step 14)
            if form_struct:
                for section in proposal.narrative_sections:
                    # Recherche de la contrainte correspondante
                    constraint = next((f for f in form_struct.form_fields if f.field_id == section.field_id), None)
                    if constraint and constraint.character_limit and len(section.final_text) > constraint.character_limit:
                        excess_ratio = (len(section.final_text) - constraint.character_limit) / constraint.character_limit
                        
                        if excess_ratio <= 0.05:
                            # Défaillance mineure (<= 5%) : Troncature déterministe au dernier point fort
                            logger.info(f"Dépassement mineur (<=5%) pour {section.field_id}. Troncutage Python pur...")
                            truncated = section.final_text[:constraint.character_limit]
                            section.final_text = truncated.rpartition('.')[0] + '.'
                        else:
                            # Défaillance majeure (> 5%) : Micro-agent Flash de concision
                            logger.warning(f"Dépassement majeur (>5%) pour {section.field_id}. Lancement concision par agent...")
                            compactor_res = compliance_enforcer_agent.run(
                                text=section.final_text, 
                                limit=constraint.character_limit
                            )
                            section.final_text = compactor_res.get("temp:validated_draft")
                        
                        section.character_count = len(section.final_text)

            # 15. Assemblage Google Docs
            if dry_run:
                logger.info(f"[DRY-RUN] Dossier généré pour {proposal.project_title} (non publié)")
            else:
                doc_url = assembler.assemble(proposal)
                # Mise à jour du tableur pour HITL #2
                publisher.mark_as_drafted(task['row_index'], doc_url)
                logger.info(f"Dossier prêt : {doc_url}")

    logger.info("Cycle de rédaction terminé.")

if __name__ == "__main__":
    # Initialisation d'une fausse variable pour les outils MCP en mode test local
    if "H_COMPANY_API_KEY" not in os.environ:
        os.environ["H_COMPANY_API_KEY"] = "mock-key-pour-test-structurel"

    # Récupération du mode dry-run depuis l'environnement
    is_dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    print(f"--- DÉMARRAGE DU FLUX {'[DRY-RUN]' if is_dry_run else ''} ---")

    # Exécution de la phase de découverte et de screening
    run_discovery_cycle(dry_run=is_dry_run)
    
    # Exécution de la phase de rédaction et de chiffrage (après HITL #1)
    run_proposal_generation_cycle(dry_run=is_dry_run)
