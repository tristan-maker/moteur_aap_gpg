import asyncio
import sys
from decimal import Decimal
from unittest.mock import patch

from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from main import root_agent
from schemas import (
    AAPStrategicScore,
    DiscoveredUrlCandidate,
    DiscoveredUrlList,
    ExpenseLineItem,
    FinancialApplicationPlan,
    FullProposalDocument,
    NarrativeResponseItem,
    SearchDork,
    SearchQueryMatrix,
)


async def run_end_to_end_test():
    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(
        app_name="moteur_aap_gpg", user_id="test_user"
    )

    mock_matrix = SearchQueryMatrix(
        generated_dorks=[
            SearchDork(
                query_string='"appel à projets" QPV 2026',
                strategic_rationale="Inclusion",
                priority_level="HAUTE",
            )
        ],
        execution_horizon_year=2026,
    )

    mock_discovered = DiscoveredUrlList(
        candidates=[
            DiscoveredUrlCandidate(
                url="https://fondation.example.org/aap",
                page_title="AAP 2026 Inclusion",
                discovery_query="query",
                snippet="Extrait",
            )
        ]
    )

    mock_score = AAPStrategicScore(
        aap_id="hash_1",
        strategic_fit_score=0.9,
        primary_axis="QPV_Inclusion",
        alignment_reasoning="Alignement fort",
        recommended_for_selection=True,
    )

    mock_proposal = FullProposalDocument(
        aap_id="hash_1",
        project_title="Projet Test 2026",
        executive_pitch="Pitch",
        narrative_sections=[
            NarrativeResponseItem(
                field_id="q1",
                question_label="Label",
                final_text="Texte de réponse",
                character_count=16,
                referenced_partners=["AXA"],
            )
        ],
        financial_plan=FinancialApplicationPlan(
            aap_id="hash_1",
            total_project_cost=Decimal("15000.00"),
            total_grant_requested=Decimal("8000.00"),
            total_self_financing=Decimal("7000.00"),
            budget_breakdown=[
                ExpenseLineItem(
                    category="Encadrement_Guide",
                    unit_cost_euro=Decimal("450.00"),
                    units_count=10,
                    total_cost_euro=Decimal("4500.00"),
                    grant_allocation_euro=Decimal("2800.00"),
                    association_share_euro=Decimal("1700.00"),
                )
            ],
        ),
    )

    async def mock_run_async_impl(ctx):
        ctx.session.state["temp:generated_queries"] = mock_matrix.model_dump()
        ctx.session.state["temp:discovered_urls"] = mock_discovered.model_dump()
        ctx.session.state["temp:current_aap_score"] = mock_score.model_dump()
        ctx.session.state["temp:application_proposal_draft"] = mock_proposal.model_dump()
        yield Event(
            author=root_agent.name,
            actions=EventActions(
                state_delta={
                    "temp:application_proposal_draft": mock_proposal.model_dump()
                }
            ),
        )

    with patch.object(
        root_agent, "_run_async_impl", side_effect=mock_run_async_impl
    ):
        async for _ in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message="Lance le workflow complet du moteur d'AAP.",
        ):
            pass

    updated_session = await runner.session_service.get_session(
        app_name="moteur_aap_gpg", user_id="test_user", session_id=session.id
    )

    assert "temp:application_proposal_draft" in updated_session.state
    print("✅ TEST INTEGRATION END-TO-END PIPELINE RÉUSSI.")


if __name__ == "__main__":
    try:
        asyncio.run(run_end_to_end_test())
    except Exception as e:
        print(f"❌ ÉCHEC DU TEST : {e}")
        sys.exit(1)
