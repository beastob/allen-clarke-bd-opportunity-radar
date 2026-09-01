import pytest
from unittest.mock import MagicMock, patch
import httpx
from radar.pipeline.models import BDOpportunity, OpportunityScore
from radar.pipeline.validator import LinkValidationResult, LinkValidator


@pytest.fixture
def validator():
    return LinkValidator()


def test_validate_url_syntax_and_domain(validator):
    # Valid NZ government link
    res_nz = validator.validate_url("https://www.beehive.govt.nz/release/rma-reform-2026")
    assert res_nz.is_valid_format is True
    assert res_nz.is_gov_domain is True

    # Valid AU government link
    res_au = validator.validate_url("https://ministers.pmc.gov.au/albanese/2026/aged-care-act")
    assert res_au.is_valid_format is True
    assert res_au.is_gov_domain is True

    # Non-government domain
    res_non_gov = validator.validate_url("https://random-commercial-blog.com/news")
    assert res_non_gov.is_valid_format is True
    assert res_non_gov.is_gov_domain is False

    # Invalid URL format
    res_invalid = validator.validate_url("not-a-valid-url")
    assert res_invalid.is_valid_format is False
    assert res_invalid.is_gov_domain is False


def test_validate_reachability_with_mock_http(validator):
    # Mock successful HTTP 200 HEAD response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.is_success = True

    with patch.object(httpx.Client, "head", return_value=mock_resp):
        res = validator.check_reachability("https://www.beehive.govt.nz/release/sample")
        assert res.is_reachable is True
        assert res.http_status == 200

    # Mock 404 Not Found response
    mock_404 = MagicMock()
    mock_404.status_code = 404
    mock_404.is_success = False

    with patch.object(httpx.Client, "head", return_value=mock_404):
        res = validator.check_reachability("https://www.beehive.govt.nz/release/broken-link")
        assert res.is_reachable is False
        assert res.http_status == 404

    # Mock network timeout / exception
    with patch.object(httpx.Client, "head", side_effect=httpx.TimeoutException("Connection timed out")):
        res = validator.check_reachability("https://timeout-domain.govt.nz")
        assert res.is_reachable is False
        assert "timed out" in (res.error_message or "").lower()


def test_validate_opportunities_post_prioritisation(validator):
    opp1 = BDOpportunity(
        id="opp-valid-1",
        title="Valid Policy Opp",
        jurisdiction="NZ",
        published_date="2026-03-01",
        url="https://www.beehive.govt.nz/release/rma",
        change_summary="Summary",
        verified_facts="Facts",
        strategic_interpretation="Interpretation",
        target_client_name="MfE",
        primary_service_line_id="policy_regulatory",
        service_line_name="Policy & Regulatory Design",
        service_offering_summary="Advisory",
        target_contact_persona="Director",
        conversation_starter="Starter",
        score=OpportunityScore(strategic_fit_score=30, urgency_score=30, budget_score=25),
    )

    opp_invalid = BDOpportunity(
        id="opp-invalid-url",
        title="Invalid Policy Opp",
        jurisdiction="AU",
        published_date="2026-03-01",
        url="invalid-url-string",
        change_summary="Summary",
        verified_facts="Facts",
        strategic_interpretation="Interpretation",
        target_client_name="DoHAC",
        primary_service_line_id="policy_regulatory",
        service_line_name="Policy & Regulatory Design",
        service_offering_summary="Advisory",
        target_contact_persona="Director",
        conversation_starter="Starter",
        score=OpportunityScore(strategic_fit_score=10, urgency_score=10, budget_score=10),
    )

    # Filter invalid formatted links when strict_syntax=True
    validated = validator.validate_opportunities([opp1, opp_invalid], strict_syntax=True)
    assert len(validated) == 1
    assert validated[0].id == "opp-valid-1"
