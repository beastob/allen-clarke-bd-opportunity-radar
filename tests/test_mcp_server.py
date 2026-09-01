import pytest
from radar.db.database import DatabaseManager
from radar.db.seed import seed_database
from radar.models import OpportunityRecord
from radar.server import create_mcp_server


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_mcp_radar.db"
    db = DatabaseManager(str(db_file))
    db.initialize()
    seed_database(db)
    return db


@pytest.fixture
def mcp_server(temp_db):
    return create_mcp_server(db_manager=temp_db)


@pytest.mark.asyncio
async def test_server_initialization(mcp_server):
    assert mcp_server.name == "Allen-Clarke-BD-Opportunity-Radar"
    tools = await mcp_server.list_tools()
    tool_names = {t.name for t in tools}

    assert "trigger_policy_scan" in tool_names
    assert "query_opportunities" in tool_names
    assert "generate_pitch_brief" in tool_names
    assert "add_client_context" in tool_names


@pytest.mark.asyncio
async def test_trigger_policy_scan_tool(mcp_server, temp_db):
    result_content, raw_structured = await mcp_server.call_tool(
        "trigger_policy_scan",
        {"jurisdiction": "NZ", "use_fixtures": True, "max_items": 5},
    )
    structured = raw_structured.get("result", raw_structured)

    assert structured is not None
    assert structured.get("status") == "success"
    assert "opportunities" in structured
    assert structured.get("total_opportunities") > 0
    assert all(o["jurisdiction"] == "NZ" for o in structured["opportunities"])

    # Check DB was populated
    db_opps = temp_db.get_opportunities(jurisdiction="NZ")
    assert len(db_opps) > 0


@pytest.mark.asyncio
async def test_trigger_policy_scan_invalid_jurisdiction(mcp_server):
    result_content, raw_structured = await mcp_server.call_tool(
        "trigger_policy_scan",
        {"jurisdiction": "USA"},
    )
    structured = raw_structured.get("result", raw_structured)
    assert structured.get("status") == "error"
    assert "Invalid jurisdiction" in structured.get("error", "")


@pytest.mark.asyncio
async def test_query_opportunities_tool(mcp_server, temp_db):
    # Seed an opportunity
    opp = OpportunityRecord(
        id="opp-mcp-query-1",
        title="NZ Environment Resource Management Transition",
        jurisdiction="NZ",
        target_client_id="nz-mfe",
        primary_service_line_id="policy-regulation",
        strategic_fit_score=30,
        urgency_score=25,
        budget_score=25,
        total_score=80,
        verified_facts="RMA replacement bill passed select committee stage.",
        strategic_interpretation="MfE requires external capacity for transition guidelines.",
    )
    temp_db.save_opportunity(opp)

    # Query with client filter
    result_content, raw_structured = await mcp_server.call_tool(
        "query_opportunities",
        {"client": "Ministry for the Environment", "min_score": 70},
    )
    structured = raw_structured.get("result", raw_structured)

    assert structured.get("status") == "success"
    assert structured.get("count") == 1
    assert structured["opportunities"][0]["id"] == "opp-mcp-query-1"
    assert structured["opportunities"][0]["client_name"] == "Ministry for the Environment (Manatū Mō Te Taiao)"
    assert structured["opportunities"][0]["service_line_name"] == "Policy + Regulation"


@pytest.mark.asyncio
async def test_query_opportunities_invalid_inputs(mcp_server):
    # Negative min score
    result_content, raw_structured = await mcp_server.call_tool(
        "query_opportunities",
        {"min_score": -10},
    )
    structured = raw_structured.get("result", raw_structured)
    assert structured.get("status") == "error"
    assert "min_score" in structured.get("error", "").lower()

    # Invalid jurisdiction
    result_content, raw_structured = await mcp_server.call_tool(
        "query_opportunities",
        {"jurisdiction": "UK"},
    )
    structured = raw_structured.get("result", raw_structured)
    assert structured.get("status") == "error"
    assert "jurisdiction" in structured.get("error", "").lower()


@pytest.mark.asyncio
async def test_generate_pitch_brief_tool(mcp_server, temp_db):
    opp = OpportunityRecord(
        id="opp-pitch-test-1",
        title="Health Systems Review",
        jurisdiction="NZ",
        target_client_id="nz-healthnz",
        primary_service_line_id="policy-regulation",
        verified_facts="Health system review launched by Minister.",
        strategic_interpretation="Hospital network restructuring advice needed.",
        strategic_fit_score=30,
        urgency_score=30,
        budget_score=20,
        total_score=80,
        conversation_starter="We noted the launch of the health system review...",
        target_contact_persona="Chief Executive",
    )
    temp_db.save_opportunity(opp)

    result_content, raw_structured = await mcp_server.call_tool(
        "generate_pitch_brief",
        {
            "opportunity_id": "opp-pitch-test-1",
            "contact_name": "Dr. Sarah Jenkins",
            "custom_angle": "Focus on acute hospital capacity and winter pressures.",
        },
    )
    structured = raw_structured.get("result", raw_structured)

    assert structured.get("status") == "success"
    brief = structured.get("pitch_brief")
    assert brief is not None
    assert brief["opportunity_id"] == "opp-pitch-test-1"
    assert "email_draft" in brief
    assert "Dr. Sarah Jenkins" in brief["email_draft"]["recipient"]
    assert "Health Systems Review" in brief["email_draft"]["subject"]
    assert "pitch_brief_markdown" in brief
    assert len(brief["talking_points"]) > 0


@pytest.mark.asyncio
async def test_generate_pitch_brief_not_found(mcp_server):
    result_content, raw_structured = await mcp_server.call_tool(
        "generate_pitch_brief",
        {"opportunity_id": "nonexistent-opp-999"},
    )
    structured = raw_structured.get("result", raw_structured)
    assert structured.get("status") == "error"
    assert "Opportunity not found" in structured.get("error", "")


@pytest.mark.asyncio
async def test_add_client_context_tool(mcp_server, temp_db):
    result_content, raw_structured = await mcp_server.call_tool(
        "add_client_context",
        {
            "client_id": "nz-healthnz",
            "relationship_notes": "Met with Director of Commissioning regarding Q3 advisory needs.",
            "append": True,
        },
    )
    structured = raw_structured.get("result", raw_structured)

    assert structured.get("status") == "success"
    assert structured.get("client_id") == "nz-healthnz"
    assert "Met with Director of Commissioning" in structured.get("relationship_notes", "")

    # Check DB
    updated_client = temp_db.get_client_by_id("nz-healthnz")
    assert "Met with Director of Commissioning" in updated_client.relationship_notes


@pytest.mark.asyncio
async def test_add_client_context_client_not_found(mcp_server):
    result_content, raw_structured = await mcp_server.call_tool(
        "add_client_context",
        {
            "client_id": "unknown-nonexistent-agency",
            "relationship_notes": "Some notes",
        },
    )
    structured = raw_structured.get("result", raw_structured)
    assert structured.get("status") == "error"
    assert "Client not found" in structured.get("error", "")


@pytest.mark.asyncio
async def test_add_client_context_empty_notes(mcp_server):
    result_content, raw_structured = await mcp_server.call_tool(
        "add_client_context",
        {
            "client_id": "nz-healthnz",
            "relationship_notes": "   ",
        },
    )
    structured = raw_structured.get("result", raw_structured)
    assert structured.get("status") == "error"
    assert "relationship_notes" in structured.get("error", "").lower()
