import asyncio
import sys
from decimal import Decimal
from unittest.mock import patch

from compliance_enforcer import enforce_character_limits
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import types
from narrative_agent import strategic_narrative_drafter
from schemas import (
    ExpenseLineItem,
    FinancialApplicationPlan,
    FullProposalDocument,
    NarrativeResponseItem,
)


async def run_mock_narrative_test():
    mock_proposal = FullProposalDocument(
        aap_id="hash_1",
        project_title="Cordées d'Alpinisme et Mentorat QPV 2026",
        executive_pitch="Accompagnement de 10 jeunes QPV en haute montagne avec cadres AXA.",
        narrative_sections=[
            NarrativeResponseItem(
                field_id="q1_pitch",
                question_label="Présentation synthétique du projet",
                final_text="Gravir Pour Grandir propose un parcours d'émancipation par l'alpinisme et le mentorat. Ce texte dépasse volontairement la limite fixée pour tester la troncature automatique.",
                character_count=162,
                referenced_partners=["AXA Atout Cœur", "Proxité"],
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

    runner = InMemoryRunner(agent=strategic_narrative_drafter)
    session = await runner.session_service.create_session(
        app_name="moteur_aap_gpg", user_id="test_user"
    )

    async def mock_run_async_impl(ctx):
        ctx.session.state["temp:application_proposal_draft"] = mock_proposal.model_dump()
        yield Event(
            author=strategic_narrative_drafter.name,
            actions=EventActions(
                state_delta={
                    "temp:application_proposal_draft": mock_proposal.model_dump()
                }
            ),
        )

    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Rédige la proposition pour l'AAP sélectionné.")]
    )

    with patch.object(
        strategic_narrative_drafter,
        "_run_async_impl",
        side_effect=mock_run_async_impl,
    ):
        async for _ in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=user_content,
        ):
            pass

    field_limits = {"q1_pitch": 100}
    validated_proposal = enforce_character_limits(mock_proposal, field_limits)

    section = validated_proposal.narrative_sections[0]
    assert len(section.final_text) <= 100
    assert section.final_text.endswith(".")
    print("✅ TEST RÉDACTION STRATÉGIQUE & COMPLIANCE RÉUSSI.")


if __name__ == "__main__":
    try:
        asyncio.run(run_mock_narrative_test())
    except Exception as e:
        print(f"❌ ÉCHEC DU TEST : {e}")
        sys.exit(1)
