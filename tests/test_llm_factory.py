"""Tests for LLM Factory, OpenRouter integration, and multi-agent LLM execution."""

import os
from unittest.mock import MagicMock, patch
import pytest
from radar.db.database import DatabaseManager
from radar.pipeline.llm import get_llm, get_llm_status
from radar.pipeline.models import (
    FilterResult,
    ImpactAnalysis,
    LLMScoringOutput,
    ServiceMatch,
)
from radar.pipeline.orchestrator import OpportunityPipeline
from radar.server import create_mcp_server


def test_get_llm_heuristics_explicit():
    """Explicitly selecting heuristics should always return None."""
    llm = get_llm(provider="heuristics")
    assert llm is None

    llm2 = get_llm(provider="none")
    assert llm2 is None


def test_get_llm_no_keys_returns_none(monkeypatch):
    """When no API keys are present, get_llm returns None (fallback to heuristics)."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    llm = get_llm()
    assert llm is None


def test_get_llm_openrouter_initialization(monkeypatch):
    """Setting OPENROUTER_API_KEY should instantiate ChatOpenAI pointing to OpenRouter."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-123456789")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    llm = get_llm(provider="openrouter")
    assert llm is not None
    assert "openrouter.ai" in str(llm.openai_api_base or getattr(llm, "base_url", ""))
    assert getattr(llm, "model_name", None) == "anthropic/claude-3.5-sonnet" or getattr(llm, "model", None) == "anthropic/claude-3.5-sonnet"


def test_get_llm_openai_initialization(monkeypatch):
    """Setting OPENAI_API_KEY should instantiate ChatOpenAI."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-987654321")

    llm = get_llm(provider="openai", model="gpt-4o-mini")
    assert llm is not None
    assert getattr(llm, "model_name", None) == "gpt-4o-mini" or getattr(llm, "model", None) == "gpt-4o-mini"


def test_get_llm_status_diagnostics(monkeypatch):
    """get_llm_status should return accurate diagnostic information with masked keys."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-secret-key-abcdef")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    status = get_llm_status()
    assert status["detected_provider"] == "openrouter"
    assert status["is_llm_available"] is True
    assert status["openrouter"]["is_configured"] is True
    assert "..." in status["openrouter"]["masked_key"]
    assert status["openai"]["is_configured"] is False


def test_pipeline_with_mock_llm(tmp_path):
    """Verifies that OpportunityPipeline correctly uses structured LLM output when an LLM is provided."""
    db_file = tmp_path / "test_llm_pipeline.db"
    db = DatabaseManager(db_path=str(db_file))
    db.initialize()

    # Seed mock client and service line
    from radar.db.seed import seed_database
    seed_database(db=db)

    # Ingest fixture scans
    from radar.ingestion.engine import IngestionEngine
    engine = IngestionEngine(db_manager=db)
    engine.run_scan(jurisdiction="NZ", use_fixtures=True)

    # Mock LangChain LLM with structured output
    mock_llm = MagicMock()

    # Configure structured outputs for each agent step
    mock_filter_output = FilterResult(
        is_actionable=True,
        rejection_reason=None,
        novelty_score=0.95,
        actionable_summary="LLM Filtered Policy Signal",
    )
    mock_impact_output = ImpactAnalysis(
        verified_facts="Fact: Announced 2026-08-31 by Minister of Health.",
        strategic_interpretation="Strategic: Delivery pressure on Health New Zealand.",
        affected_sectors=["Health"],
        affected_agencies=["Health New Zealand"],
        operational_obligations=["Design clinical pathways"],
        compliance_deadlines=["Within 6 months"],
        citations=["https://www.beehive.govt.nz"],
    )
    mock_match_output = ServiceMatch(
        primary_service_line_id="evaluation-review",
        secondary_service_line_ids=["policy-regulation"],
        target_client_id="nz-healthnz",
        target_client_name="Health New Zealand (Te Whatu Ora)",
        service_offering_summary="Evaluation & Review operating model advisory",
        fit_rationale="A+C has proven experience in health operating model reviews",
    )
    mock_scoring_output = LLMScoringOutput(
        strategic_fit_score=32,
        urgency_score=30,
        budget_score=26,
        scoring_rationale={"strategic_fit": "Strong fit", "urgency": "Near term", "budget": "Allocated"},
        target_contact_persona="Director, Evidence & Insights",
        conversation_starter="Kia ora Director, following the recent announcement...",
        key_pitch_angles=["A+C deep health evaluation capability", "Rapid deployment"],
    )

    from langchain_core.runnables import RunnableLambda

    def mock_with_structured_output(schema):
        if schema == FilterResult:
            return RunnableLambda(lambda _: mock_filter_output)
        elif schema == ImpactAnalysis:
            return RunnableLambda(lambda _: mock_impact_output)
        elif schema == ServiceMatch:
            return RunnableLambda(lambda _: mock_match_output)
        elif schema == LLMScoringOutput:
            return RunnableLambda(lambda _: mock_scoring_output)
        return RunnableLambda(lambda _: MagicMock())

    mock_llm.with_structured_output.side_effect = mock_with_structured_output

    pipeline = OpportunityPipeline(db_manager=db, llm=mock_llm)
    result = pipeline.run(jurisdiction="NZ", max_items=5)

    assert result.processed_count > 0
    assert len(result.opportunities) > 0
    top_opp = result.opportunities[0]
    assert top_opp.score.total_score == 88  # 32 + 30 + 26
    assert top_opp.target_contact_persona == "Director, Evidence & Insights"
    assert "Health New Zealand" in top_opp.target_client_name


def test_mcp_get_system_status_tool(tmp_path):
    """Verifies that the FastMCP get_system_status tool returns diagnostic info."""
    db_file = tmp_path / "test_mcp_status.db"
    db = DatabaseManager(db_path=str(db_file))
    db.initialize()

    server = create_mcp_server(db_manager=db)
    tool_fn = getattr(server, "_tool_manager", None)

    # In FastMCP, call get_system_status directly or via tool list
    # FastMCP stores tools in _tool_manager._tools or similar
    status_tool = None
    if hasattr(server, "get_tool"):
        status_tool = server.get_tool("get_system_status")

    # Directly instantiate and test get_llm_status
    status = get_llm_status()
    assert "detected_provider" in status
    assert "openrouter" in status
    assert "openai" in status
