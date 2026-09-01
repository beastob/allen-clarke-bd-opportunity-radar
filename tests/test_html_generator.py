import html as html_module
import pytest
from radar.reporting.html_generator import HTMLReportGenerator
from radar.reporting.models import ReportMetadata


def test_html_generator_valid_structure(sample_opportunity_nz, sample_opportunity_au):
    generator = HTMLReportGenerator()
    html_out = generator.generate_email_digest(
        opportunities=[sample_opportunity_nz, sample_opportunity_au],
        metadata=ReportMetadata(
            period="Fortnight Ending 15 March 2026",
            jurisdiction="ALL",
            scanned_count=14,
        ),
    )

    # 1. Valid HTML5 document tags
    assert "<!DOCTYPE html>" in html_out
    assert "<html" in html_out
    assert "</html>" in html_out
    assert "<head>" in html_out
    assert "<body>" in html_out

    # 2. Header and metadata
    assert "Allen + Clarke" in html_out
    assert "Opportunity Radar" in html_out
    assert "Fortnight Ending 15 March 2026" in html_out
    assert "2 Qualified Opportunities" in html_out or "2" in html_out

    # 3. Card elements for opportunities
    for opp in [sample_opportunity_nz, sample_opportunity_au]:
        assert html_module.escape(opp.title) in html_out
        assert opp.jurisdiction in html_out
        assert html_module.escape(opp.target_client_name) in html_out
        assert html_module.escape(opp.service_line_name) in html_out
        assert html_module.escape(opp.service_offering_summary) in html_out
        assert str(opp.score.total_score) in html_out

        # Score breakdown
        assert f"{opp.score.strategic_fit_score}/35" in html_out or f"Fit: {opp.score.strategic_fit_score}" in html_out
        assert f"{opp.score.urgency_score}/35" in html_out or f"Urgency: {opp.score.urgency_score}" in html_out
        assert f"{opp.score.budget_score}/30" in html_out or f"Budget: {opp.score.budget_score}" in html_out

        # Fact vs Interpretation demarcations
        assert "Verified Statutory Facts" in html_out or "Verified Facts" in html_out
        assert "Strategic Consulting Interpretation" in html_out or "Strategic Interpretation" in html_out
        assert html_module.escape(opp.verified_facts) in html_out
        assert html_module.escape(opp.strategic_interpretation) in html_out

        # Action plan & persona
        assert html_module.escape(opp.target_contact_persona) in html_out
        assert html_module.escape(opp.conversation_starter) in html_out


def test_html_generator_handles_empty_list():
    generator = HTMLReportGenerator()
    html_out = generator.generate_email_digest(opportunities=[])
    assert "<!DOCTYPE html>" in html_out
    assert "Allen + Clarke" in html_out
    assert "No high-scoring opportunities identified" in html_out or "0 Qualified Opportunities" in html_out
