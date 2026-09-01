import pytest
from radar.models import ScanRecord
from radar.pipeline.filter_agent import IngestionFilterAgent
from radar.pipeline.models import FilterResult


@pytest.fixture
def filter_agent():
    return IngestionFilterAgent()


def test_filter_actionable_legislation(filter_agent):
    scan = ScanRecord(
        id="scan-leg-1",
        content_hash="hash-leg-1",
        source_id="nz_beehive",
        source_name="Beehive Releases",
        jurisdiction="NZ",
        title="Government introduces Resource Management Replacement Bill with 2026 local council obligations",
        url="https://beehive.govt.nz/release/rma-bill",
        published_date="2026-03-01",
        summary="Ministers have announced comprehensive reform of resource management law requiring all 67 local authorities to implement spatial planning frameworks.",
        raw_content="Ministers have announced comprehensive reform of resource management law requiring all 67 local authorities to implement spatial planning frameworks by late 2026.",
    )

    result = filter_agent.filter_item(scan)
    assert isinstance(result, FilterResult)
    assert result.is_actionable is True
    assert result.rejection_reason is None
    assert result.novelty_score >= 0.7
    assert result.actionable_summary is not None
    assert len(result.actionable_summary) > 10


def test_filter_actionable_evaluation_inquiry(filter_agent):
    scan = ScanRecord(
        id="scan-inq-1",
        content_hash="hash-inq-1",
        source_id="au_ministers",
        source_name="Australian Ministerial Statements",
        jurisdiction="AU",
        title="Royal Commission recommendations prompt statutory review of Aged Care Quality Standards",
        url="https://ministers.pmc.gov.au/aged-care-review",
        published_date="2026-03-05",
        summary="The Department of Health and Aged Care is commissioning an independent program evaluation and regulatory compliance framework.",
        raw_content="The Department of Health and Aged Care is commissioning an independent program evaluation and regulatory compliance framework with public consultations closing in July.",
    )

    result = filter_agent.filter_item(scan)
    assert result.is_actionable is True
    assert result.rejection_reason is None


def test_filter_rejects_ceremonial_and_sports_noise(filter_agent):
    scan = ScanRecord(
        id="scan-ceremony-1",
        content_hash="hash-ceremony-1",
        source_id="nz_beehive",
        source_name="Beehive Releases",
        jurisdiction="NZ",
        title="Minister congratulates regional rugby team on championship victory",
        url="https://beehive.govt.nz/release/rugby-win",
        published_date="2026-03-02",
        summary="The Minister for Sport and Recreation attended the finals today and presented medals to the winning team in a spirited match.",
        raw_content="The Minister for Sport and Recreation attended the finals today and presented medals to the winning team in a spirited match.",
    )

    result = filter_agent.filter_item(scan)
    assert isinstance(result, FilterResult)
    assert result.is_actionable is False
    assert result.rejection_reason is not None
    assert "ceremonial" in result.rejection_reason.lower() or "sports" in result.rejection_reason.lower() or "not actionable" in result.rejection_reason.lower()


def test_filter_rejects_photo_op_and_ribbon_cutting(filter_agent):
    scan = ScanRecord(
        id="scan-photo-1",
        content_hash="hash-photo-1",
        source_id="au_ministers",
        source_name="Australian Ministers",
        jurisdiction="AU",
        title="Minister cuts ribbon on newly renovated community playground in suburban electorate",
        url="https://ministers.pmc.gov.au/playground",
        published_date="2026-03-03",
        summary="A sunny morning greeted local families as the Minister unveiled a commemorative plaque and congratulated the local community council.",
        raw_content="A sunny morning greeted local families as the Minister unveiled a commemorative plaque.",
    )

    result = filter_agent.filter_item(scan)
    assert result.is_actionable is False
    assert result.rejection_reason is not None
