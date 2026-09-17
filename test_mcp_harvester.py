import sys
from mcp_harvester import MockMcpFormHarvester
from schemas import FormStructureDefinition


def test_mcp_form_harvesting():
    harvester = MockMcpFormHarvester()
    raw_schema = harvester.extract_target_form_schema(
        portal_url="https://fondation.axa.fr/depot-2026", aap_id="hash_1"
    )

    form_def = FormStructureDefinition(**raw_schema)

    assert form_def.aap_id == "hash_1"
    assert len(form_def.form_fields) == 3
    assert form_def.form_fields[0].character_limit == 1000
    assert len(form_def.mandatory_attachments) == 3
    print("✅ TEST HARVESTING FORMULAIRE MCP RÉUSSI.")


if __name__ == "__main__":
    try:
        test_mcp_form_harvesting()
    except Exception as e:
        print(f"❌ ÉCHEC DU TEST : {e}")
        sys.exit(1)
