import pytest
from radar.models import ScanRecord
from radar.pipeline.analyzer_agent import ImpactAnalyzerAgent
from radar.pipeline.models import ImpactAnalysis


@pytest.fixture
def analyzer_agent():
    return ImpactAnalyzerAgent()


def test_analyze_impact_nz_resource_management(analyzer_agent):
    scan = ScanRecord(
        id="scan-nz-rma",
        content_hash="hash-nz-rma",
        source_id="nz_beehive",
        source_name="Beehive Releases",
        jurisdiction="NZ",
        title="Minister Bishop introduces Natural and Built Environment Bill with Q4 2026 local council deadlines",
        url="https://beehive.govt.nz/release/rma-nbe-bill",
        published_date="2026-03-10",
        summary="The Government has introduced the Natural and Built Environment Bill. Regional councils and territorial authorities must produce draft regional spatial strategies by 1 November 2026.",
        raw_content="The Government has introduced the Natural and Built Environment Bill into Parliament. The Minister for RMA Reform announced that Ministry for the Environment (MfE) and all 67 local authorities face statutory compliance obligations. Regional councils must establish joint regional spatial planning committees by 1 November 2026.",
    )

    analysis = analyzer_agent.analyze_impact(scan)
    assert isinstance(analysis, ImpactAnalysis)

    # Fact vs. Interpretation separation
    assert len(analysis.verified_facts) > 20
    assert "Natural and Built Environment Bill" in analysis.verified_facts or "1 November 2026" in analysis.verified_facts
    assert len(analysis.strategic_interpretation) > 20

    # Sectors and agencies
    assert any("Environment" in s or "Local Government" in s for s in analysis.affected_sectors)
    assert any("Ministry for the Environment" in a or "Council" in a for a in analysis.affected_agencies)

    # Operational obligations and deadlines
    assert len(analysis.operational_obligations) >= 1
    assert any("2026" in d or "November" in d for d in analysis.compliance_deadlines)

    # Citations
    assert len(analysis.citations) >= 1


def test_analyze_impact_au_aged_care_review(analyzer_agent):
    scan = ScanRecord(
        id="scan-au-agedcare",
        content_hash="hash-au-agedcare",
        source_id="au_ministers",
        source_name="Australian Ministers",
        jurisdiction="AU",
        title="Health Minister Butler announces statutory independent evaluation of new Aged Care Act compliance",
        url="https://ministers.pmc.gov.au/aged-care-evaluation",
        published_date="2026-02-28",
        summary="The Department of Health and Aged Care is commissioning a nationwide evaluation of provider readiness under the revised Aged Care Quality Standards, effective 1 July 2026.",
        raw_content="Minister for Health and Aged Care Mark Butler today released the draft evaluation framework for the new Aged Care Act. Submissions and provider audit readiness frameworks are mandated by 1 July 2026.",
    )

    analysis = analyzer_agent.analyze_impact(scan)
    assert isinstance(analysis, ImpactAnalysis)
    assert "Department of Health and Aged Care" in " ".join(analysis.affected_agencies) or "Health" in " ".join(analysis.affected_sectors)
    assert any("July 2026" in d or "2026" in d for d in analysis.compliance_deadlines)
    assert len(analysis.citations) > 0
