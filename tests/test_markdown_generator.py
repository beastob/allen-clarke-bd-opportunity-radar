import pytest
from radar.reporting.markdown_generator import MarkdownReportGenerator
from radar.reporting.models import ReportMetadata


def test_markdown_generator_structure_and_six_questions(sample_opportunity_nz, sample_opportunity_au):
    generator = MarkdownReportGenerator()
    report = generator.generate_report(
        opportunities=[sample_opportunity_nz, sample_opportunity_au],
        metadata=ReportMetadata(
            period="Fortnight Ending 15 March 2026",
            jurisdiction="ALL",
            scanned_count=12,
        ),
    )

    # 1. Report Title & Header
    assert "# Allen + Clarke BD Opportunity Radar" in report
    assert "Fortnight Ending 15 March 2026" in report
    assert "Executive Summary" in report

    # 2. Executive Summary Table
    assert "NZ Resource Management System Reform Guidelines" in report
    assert "Australian Aged Care Quality & Safety Commission Governance Review" in report
    assert "88/100" in report or "88" in report
    assert "89/100" in report or "89" in report

    # 3. Mandatory 6 Questions are strictly answered for every opportunity
    for opp in [sample_opportunity_nz, sample_opportunity_au]:
        # Header for the opportunity
        assert opp.title in report
        assert opp.jurisdiction in report

        # Q1: What changed
        assert "Q1: What has changed or is changing?" in report or "Q1: What Changed" in report
        assert opp.change_summary in report

        # Q2: Verified Facts vs Strategic Interpretation
        assert "Q2: Verified Facts vs Strategic Interpretation" in report or "Q2: Verified Statutory Facts vs Strategic Consulting Interpretation" in report
        assert "Verified Statutory Facts" in report
        assert "Strategic Consulting Interpretation" in report
        assert opp.verified_facts in report
        assert opp.strategic_interpretation in report

        # Q3: Affected organisations
        assert "Q3: Affected Public Sector Organisations" in report or "Q3: Which public sector organisations" in report
        assert opp.target_client_name in report

        # Q4: Operational obligations & compliance
        assert "Q4: Operational Obligations & Timelines" in report or "Q4: What will affected organisations need to do" in report
        for obl in opp.operational_obligations:
            assert obl in report

        # Q5: A+C Service Line
        assert "Q5: Allen + Clarke Service Line Fit" in report or "Q5: Which Allen + Clarke service line fits" in report
        assert opp.service_line_name in report

        # Q6: Action Plan & Who to approach
        assert "Q6: BD Action Plan & Outreach Strategy" in report or "Q6: Who to approach and with what" in report
        assert opp.target_contact_persona in report
        assert opp.conversation_starter in report
        for angle in opp.key_pitch_angles:
            assert angle in report


def test_markdown_generator_handles_empty_list():
    generator = MarkdownReportGenerator()
    report = generator.generate_report(opportunities=[])
    assert "# Allen + Clarke BD Opportunity Radar" in report
    assert "No high-scoring opportunities identified" in report or "No opportunities found" in report
