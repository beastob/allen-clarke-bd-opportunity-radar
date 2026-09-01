"""Link verification and QA validator for Opportunity Radar (Option 2: Post-Prioritisation Gate)."""

import logging
import re
from typing import List, Optional
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel
from radar.pipeline.models import BDOpportunity

logger = logging.getLogger(__name__)

# Trusted government domain suffixes across NZ and AU
TRUSTED_GOV_DOMAINS: List[str] = [
    ".govt.nz",
    ".parliament.nz",
    ".gov.au",
    ".aph.gov.au",
    ".legislation.gov.au",
    ".fedcourt.gov.au",
    ".hcourt.gov.au",
]


class LinkValidationResult(BaseModel):
    """Structured result of link validation."""

    url: str
    is_valid_format: bool
    is_gov_domain: bool
    is_reachable: Optional[bool] = None
    http_status: Optional[int] = None
    error_message: Optional[str] = None


class LinkValidator:
    """Post-Prioritisation QA Validator ensuring source links are structurally sound, authoritative, and reachable."""

    def __init__(
        self,
        trusted_domains: Optional[List[str]] = None,
        timeout: float = 3.0,
    ):
        self.trusted_domains = trusted_domains or TRUSTED_GOV_DOMAINS
        self.timeout = timeout

    def validate_url(self, url: str) -> LinkValidationResult:
        """Validates URL syntax and verifies if domain belongs to official government registries."""
        if not url or not isinstance(url, str):
            return LinkValidationResult(
                url=str(url),
                is_valid_format=False,
                is_gov_domain=False,
                error_message="URL is empty or not a string",
            )

        try:
            parsed = urlparse(url)
            is_valid_format = bool(parsed.scheme in ("http", "https") and parsed.netloc)
            hostname = (parsed.hostname or "").lower()

            is_gov_domain = False
            if is_valid_format:
                for domain_suffix in self.trusted_domains:
                    if hostname == domain_suffix.lstrip(".") or hostname.endswith(domain_suffix):
                        is_gov_domain = True
                        break

            return LinkValidationResult(
                url=url,
                is_valid_format=is_valid_format,
                is_gov_domain=is_gov_domain,
            )
        except Exception as e:
            return LinkValidationResult(
                url=url,
                is_valid_format=False,
                is_gov_domain=False,
                error_message=str(e),
            )

    def check_reachability(self, url: str, timeout: Optional[float] = None) -> LinkValidationResult:
        """Performs an HTTP check to verify link reachability status (200 OK)."""
        base_val = self.validate_url(url)
        if not base_val.is_valid_format:
            base_val.is_reachable = False
            return base_val

        to = timeout or self.timeout
        try:
            with httpx.Client(follow_redirects=True, timeout=to) as client:
                resp = client.head(url)
                # If HEAD is disallowed (405/403), fallback to GET with byte range
                if resp.status_code in (403, 405):
                    resp = client.get(url, headers={"Range": "bytes=0-100"})

                base_val.http_status = resp.status_code
                base_val.is_reachable = resp.is_success or resp.status_code == 200
                if not base_val.is_reachable:
                    base_val.error_message = f"HTTP {resp.status_code}"
                return base_val

        except httpx.TimeoutException as te:
            base_val.is_reachable = False
            base_val.error_message = f"Connection timed out after {to}s: {te}"
            return base_val
        except Exception as e:
            base_val.is_reachable = False
            base_val.error_message = str(e)
            return base_val

    def validate_opportunities(
        self,
        opportunities: List[BDOpportunity],
        strict_syntax: bool = True,
        verify_http: bool = False,
        timeout: Optional[float] = None,
    ) -> List[BDOpportunity]:
        """Post-prioritisation QA filter on shortlisted opportunities."""
        valid_opps: List[BDOpportunity] = []

        for opp in opportunities:
            if verify_http:
                val = self.check_reachability(opp.url, timeout=timeout)
                if not val.is_reachable:
                    logger.warning(f"Dropping opportunity '{opp.title}' due to unreachable source URL: {opp.url} ({val.error_message})")
                    continue
            elif strict_syntax:
                val = self.validate_url(opp.url)
                if not val.is_valid_format:
                    logger.warning(f"Dropping opportunity '{opp.title}' due to invalid source URL syntax: {opp.url}")
                    continue

            valid_opps.append(opp)

        return valid_opps
