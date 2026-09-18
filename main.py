import logging
import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from google.adk.runners import Runner
from google.adk.sessions import FirestoreSessionService

import config
from agent import root_agent as root_pipeline_agent, PipelineOrchestrator

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GravirPourGrandir.Main")

app = FastAPI(
    title="Moteur AAP — Gravir Pour Grandir",
    version="2.1.0-PROD",
    description="API d'orchestration agentique sur Google Cloud & Vertex AI Agent Engine",
)

# Initialisation du service de session ADK en mémoire
session_service = FirestoreSessionService()
runner = Runner(
    agent=root_pipeline_agent,
    app_name="gravir_pour_grandir_aap",
    session_service=session_service,
)

# Instance globale de l'orchestrateur pour gérer les transitions de phases
orchestrator = PipelineOrchestrator(session_service=session_service)

class WorkflowTriggerRequest(BaseModel):
    user_id: str = "operator_prod"
    session_id: str = "weekly_scan_session"
    initial_trigger_message: str = "Lancer le ratissage et l'analyse hebdomadaire des appels à projets 2026."

class ResumeWorkflowRequest(BaseModel):
    user_id: str = "operator_prod"
    session_id: str = "weekly_scan_session"
    approved_aap_id: str = Field(..., description="ID de l'AAP validé manuellement (Tag GO)")
    requested_grant: float = Field(..., ge=2000.0, description="Montant de la subvention sollicitée")


@app.get("/")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "moteur-aap-gpg",
        "version": "2.1.0-PROD",
    }


@app.post("/run")
@app.post("/api/v1/trigger-workflow")
async def trigger_discovery_pipeline(
    payload: WorkflowTriggerRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Déclenche l'exécution asynchrone de la Phase 1 (Ratissage & Scoring)."""
    try:
        session = await session_service.get_session(
            app_name="gravir_pour_grandir_aap",
            user_id=payload.user_id,
            session_id=payload.session_id,
        )
        if not session:
            session = await session_service.create_session(
                app_name="gravir_pour_grandir_aap",
                user_id=payload.user_id,
                session_id=payload.session_id,
            )

        logger.info(
            f"🚀 Lancement du workflow ADK pour la session : {payload.session_id}"
        )
        
        background_tasks.add_task(
            run_workflow_task, 
            payload.user_id, 
            payload.session_id, 
            payload.initial_trigger_message
        )

        return {
            "status": "initiated",
            "session_id": payload.session_id,
            "message": "Pipeline d'acquisition web et scoring lancé en arrière-plan.",
        }
    except Exception as e:
        logger.error(f"❌ Erreur lors du déclenchement du pipeline : {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_workflow_task(user_id: str, session_id: str, message: str):
    """Tâche de fond isolée pour l'exécution du workflow."""
    try:
        async for _ in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            pass
        logger.info(f"✅ Workflow terminé avec succès pour {session_id}")
    except Exception as e:
        logger.error(f"❌ Erreur critique dans l'exécution de l'agent : {e}", exc_info=True)

@app.post("/api/v1/resume-workflow")
def resume_workflow_phase_2(payload: ResumeWorkflowRequest) -> Dict[str, Any]:
    """
    Point d'arrêt HITL #1 : Déclenche la Phase 2 (Rédaction & G-Docs) 
    après arbitrage humain sur Google Sheets.
    """
    try:
        logger.info(
            f"📥 Signal HITL reçu pour l'AAP: {payload.approved_aap_id} (Session: {payload.session_id})"
        )

        # 1. Validation de l'arbitrage (Barrière synchrone)
        if not await orchestrator.execute_hitl_checkpoint_1(
            payload.user_id, 
            payload.session_id, 
            payload.approved_aap_id
        ):
            raise HTTPException(
                status_code=400, 
                detail="L'ID AAP fourni n'a pas été trouvé dans le screening de cette session ou est invalide."
            )

        # 2. Exécution de la Phase 2 (Chiffrage déterministe et préparation rédaction)
        result = await orchestrator.run_phase_2_proposal_generation(
            user_id=payload.user_id,
            session_id=payload.session_id,
            aap_id=payload.approved_aap_id,
            requested_grant=payload.requested_grant
        )

        return {
            "status": "success",
            "phase": 2,
            "data": result
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur lors de la reprise du workflow : {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
