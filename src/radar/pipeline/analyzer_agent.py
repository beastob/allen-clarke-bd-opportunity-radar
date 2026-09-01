"""Impact & Sector Analyzer Agent (Agent 2).

Extracts affected public sector agencies, compliance deadlines, and operational obligations,
strictly enforcing the separation between Verified Facts and Strategic Interpretations.
"""

import re
from typing import Any, List, Optional
from radar.models import ScanRecord
from radar.pipeline.models import ImpactAnalysis

# Common sector keyword mappings
SECTOR_MAP = {
    "Environment & Climate": [r"\benvironment\b", r"\bclimate\b", r"\brma\b", r"\bresource management\b", r"\bconservation\b", r"\bwater\b", r"\bemissions?\b", r"\bbiodiversity\b"],
    "Health": [r"\bhealth\b", r"\bhospitals?\b", r"\bmedical\b", r"\baged care\b", r"\bdisabilit(y|ies)\b", r"\bmental health\b"],
    "Local Government": [r"\blocal government\b", r"\bcouncils?\b", r"\bterritorial\b", r"\bregional council\b", r"\bmunicipal\b"],
    "Justice & Corrections": [r"\bjustice\b", r"\bcourts?\b", r"\bpolic(e|ing)\b", r"\bcorrections?\b", r"\bprisons?\b", r"\blegal\b", r"\blaw enforcement\b"],
    "Social Development": [r"\bsocial development\b", r"\bwelfare\b", r"\bhousing\b", r"\bchildren\b", r"\byouth\b", r"\bvulnerable\b", r"\boranga tamariki\b"],
    "Education": [r"\beducation\b", r"\bschools?\b", r"\buniversit(y|ies)\b", r"\bcurriculum\b", r"\bteachers?\b", r"\btertiary\b"],
    "Transport & Infrastructure": [r"\btransport\b", r"\broads?\b", r"\brail\b", r"\binfrastructure\b", r"\btransit\b", r"\baviation\b"],
    "Kaupapa Māori & Pacific Affairs": [r"\bm[aā]ori\b", r"\biwi\b", r"\bhap[uū]\b", r"\btiriti\b", r"\btreaty\b", r"\bpacific\b", r"\bpasifika\b", r"\bindigenous\b", r"\bfirst nations\b"],
    "Public Service Governance & Finance": [r"\bpublic service\b", r"\bgovernance\b", r"\btreasury\b", r"\bfinance\b", r"\bmachinery of government\b", r"\bstate services\b"],
    "Primary Industries & Trade": [r"\bprimary industries\b", r"\bagriculture\b", r"\bfarming\b", r"\btrade\b", r"\bfisheries\b", r"\bforestry\b", r"\bbiosecurity\b"],
}

# Agency regex patterns
AGENCY_PATTERNS = [
    r"Ministry (?:for|of)(?: the)? [A-Z][a-z]+(?: [A-Z][a-z]+)*",
    r"Department (?:for|of)(?: the)? [A-Z][a-z]+(?: [A-Z][a-z]+)*(?: and [A-Z][a-z]+)*",
    r"National [A-Z][a-z]+ Authority",
    r"[A-Z][a-z]+ Commission(?:er)?",
    r"Te [A-Z][a-z]+(?: [A-Z][a-z]+)*",
    r"Waka Kotahi|Oranga Tamariki|Kāinga Ora|Health New Zealand|Te Whatu Ora|Te Aka Whai Ora",
    r"National Disability Insurance Agency|NDIA|Services Australia|APRA|ASIC|ACCC",
    r"(?:Regional|City|District|Local)?\s*Councils?",
    r"Territorial Authorit(?:y|ies)|Local Authorities",
]

# Date/deadline patterns
DEADLINE_PATTERNS = [
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\bQ[1-4]\s+\d{4}\b",
    r"\b(?:mid|late|early)\s+\d{4}\b",
    r"\b(?:1\s+July\s+202[4-9]|1\s+October\s+202[4-9]|1\s+November\s+202[4-9]|1\s+December\s+202[4-9]|1\s+January\s+202[4-9])\b",
]


class ImpactAnalyzerAgent:
    """Agent 2: Impact & Sector Analyzer Agent."""

    def __init__(self, llm: Optional[Any] = None):
        """Initializes the analyzer agent with optional LangChain LLM."""
        self.llm = llm

    def analyze_impact(self, scan: ScanRecord) -> ImpactAnalysis:
        """Analyzes a policy scan, maintaining strict separation of facts and interpretations."""
        if self.llm is not None:
            try:
                return self._analyze_with_llm(scan)
            except Exception:
                return self._analyze_with_heuristics(scan)

        return self._analyze_with_heuristics(scan)

    def _analyze_with_heuristics(self, scan: ScanRecord) -> ImpactAnalysis:
        """Deterministic NLP extraction of facts, sectors, agencies, obligations, and interpretation."""
        combined_text = f"{scan.title}. {scan.summary} {scan.raw_content}"

        # 1. Identify Affected Sectors
        detected_sectors: List[str] = []
        for sector, patterns in SECTOR_MAP.items():
            for pat in patterns:
                if re.search(pat, combined_text, re.IGNORECASE):
                    detected_sectors.append(sector)
                    break
        if not detected_sectors:
            detected_sectors = ["Public Policy & Administration"]

        # 2. Extract Affected Agencies
        detected_agencies: List[str] = []
        for pat in AGENCY_PATTERNS:
            for match in re.finditer(pat, combined_text, re.IGNORECASE):
                agency_name = match.group(0).strip()
                # Clean trailing punctuation
                agency_name = re.sub(r"[,\.:;]+$", "", agency_name)
                if agency_name and len(agency_name) > 3 and agency_name not in detected_agencies:
                    detected_agencies.append(agency_name)

        if not detected_agencies:
            if scan.jurisdiction == "NZ":
                detected_agencies = ["Responsible NZ Government Department / Crown Entity"]
            else:
                detected_agencies = ["Responsible Commonwealth Department / State Agency"]

        # 3. Extract Compliance Deadlines
        deadlines: List[str] = []
        for pat in DEADLINE_PATTERNS:
            for match in re.finditer(pat, combined_text, re.IGNORECASE):
                d_str = match.group(0).strip()
                if d_str and d_str not in deadlines:
                    deadlines.append(d_str)

        if not deadlines:
            deadlines = ["Within upcoming 6-12 month regulatory window"]

        # 4. Operational Obligations
        obligations: List[str] = []
        if re.search(r"evaluation|review|audit", combined_text, re.IGNORECASE):
            obligations.append("Conduct statutory programme review and evidence-based performance evaluation.")
        if re.search(r"draft|guidelines|standards|framework|regulation", combined_text, re.IGNORECASE):
            obligations.append("Develop operational policy guidance, regulatory standards, and compliance frameworks.")
        if re.search(r"council|territorial|spatial|regional", combined_text, re.IGNORECASE):
            obligations.append("Coordinate cross-jurisdictional governance and local transition planning.")
        if re.search(r"m[aā]ori|iwi|pacific|treaty|consultation", combined_text, re.IGNORECASE):
            obligations.append("Design and execute culturally grounded iwi, Māori, and community consultation processes.")
        if not obligations:
            obligations.append("Implement revised administrative guidelines and internal operating processes.")

        # 5. Verified Facts (Strict dates, citations, source text)
        facts_parts = [
            f"Announcement Title: {scan.title}.",
            f"Source Authority: {scan.source_name} ({scan.jurisdiction}).",
            f"Published Date: {scan.published_date} (Source: {scan.url}).",
        ]
        if deadlines:
            facts_parts.append(f"Statutory / Implementation Milestones: {', '.join(deadlines)}.")
        if detected_agencies:
            facts_parts.append(f"Referenced Public Entities: {', '.join(detected_agencies[:3])}.")

        verified_facts = " ".join(facts_parts)

        # 6. Strategic Interpretation (Consulting capacity assessment, risk, and delivery needs)
        interpretation_parts = [
            f"The policy shift places immediate delivery pressure on {', '.join(detected_agencies[:2])}.",
            f"Given strict timeline commitments ({deadlines[0] if deadlines else 'imminent deadlines'}), internal teams likely face capacity bottlenecks.",
            f"External advisory support is strongly indicated for {' and '.join(obligations[:2]).lower()}.",
        ]
        strategic_interpretation = " ".join(interpretation_parts)

        # 7. Citations
        citations = [
            f"{scan.source_name} - {scan.title} ({scan.published_date})",
            scan.url,
        ]

        return ImpactAnalysis(
            verified_facts=verified_facts,
            strategic_interpretation=strategic_interpretation,
            affected_sectors=detected_sectors,
            affected_agencies=detected_agencies,
            operational_obligations=obligations,
            compliance_deadlines=deadlines,
            citations=citations,
        )

    def _analyze_with_llm(self, scan: ScanRecord) -> ImpactAnalysis:
        """LangChain LLM-based impact analysis."""
        from radar.pipeline.prompts import ANALYZER_SYSTEM_PROMPT
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYZER_SYSTEM_PROMPT),
            ("human", "Title: {title}\nJurisdiction: {jurisdiction}\nDate: {date}\nURL: {url}\nContent: {content}"),
        ])

        structured_llm = self.llm.with_structured_output(ImpactAnalysis)
        chain = prompt | structured_llm
        return chain.invoke({
            "title": scan.title,
            "jurisdiction": scan.jurisdiction,
            "date": scan.published_date,
            "url": scan.url,
            "content": scan.raw_content[:3000],
        })
