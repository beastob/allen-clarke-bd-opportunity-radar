"""Ingestion & De-duplication Noise Filter Agent (Agent 1).

Evaluates incoming policy scan items, filters out ceremonial politics,
photo-ops, sports congratulations, and administrative churn, and verifies
novel policy/regulatory/evaluation consulting signals.
"""

import re
from typing import Any, List, Optional
from radar.models import ScanRecord
from radar.pipeline.models import FilterResult

# Keywords indicating genuine consulting, policy, legislative, or evaluation signals
ACTIONABLE_SIGNALS: List[str] = [
    r"\b(bill|act|legislation|statutory|regulation|regulatory|amendment|ordinance)\b",
    r"\b(reform|review|inquiry|royal commission|inquest|investigation|audit)\b",
    r"\b(policy|strategy|framework|operating model|governance|white paper)\b",
    r"\b(evaluation|monitoring|assessment|impact analysis|business case)\b",
    r"\b(compliance|mandate|standard|guidelines|transition|consultation)\b",
    r"\b(cabinet|crown entity|ministry|department|agency|regulator|ombudsman)\b",
    r"\b(procurement|commissioning|advisory|restructure|machinery of government)\b",
    r"\b(kaupapa m[aā]ori|treaty of waitangi|te tiriti|pacific|indigenous|first nations)\b",
]

# Keywords indicating ceremonial, political rhetoric, photo-ops, or irrelevant announcements
NOISE_SIGNALS: List[str] = [
    r"\b(congratulat(es|ions|ing)?|cheers|salutes|hails)\b",
    r"\b(ribbon[- ]cutting|opened the newly|unveiled a (commemorative )?plaque)\b",
    r"\b(playground|community park|sports field|tournament|championship|trophy|rugby|cricket|football)\b",
    r"\b(condolences?|sympathies|mourns|sadly passes)\b",
    r"\b(anniversary|birthday|celebration|festival|parade|luncheon|banquet)\b",
    r"\b(photo[- ]op|school visit|preschool visit|primary school visit|ribbon)\b",
    r"\b(medal|honour|award ceremony|hall of fame)\b",
]


class IngestionFilterAgent:
    """Agent 1: Ingestion & De-duplication Noise Filter."""

    def __init__(self, llm: Optional[Any] = None):
        """Initializes the filter agent with optional LangChain LLM."""
        self.llm = llm

    def filter_item(self, scan: ScanRecord) -> FilterResult:
        """Evaluates whether a scan record represents an actionable consulting opportunity."""
        if self.llm is not None:
            try:
                return self._filter_with_llm(scan)
            except Exception:
                # Fallback to deterministic heuristic logic on LLM error
                return self._filter_with_heuristics(scan)

        return self._filter_with_heuristics(scan)

    def _filter_with_heuristics(self, scan: ScanRecord) -> FilterResult:
        """Deterministic heuristic evaluation of policy signal vs ceremonial noise."""
        full_text = f"{scan.title} {scan.summary} {scan.raw_content}".lower()
        title_lower = scan.title.lower()

        # Check for strong noise triggers in title or summary
        for noise_pattern in NOISE_SIGNALS:
            if re.search(noise_pattern, title_lower):
                return FilterResult(
                    is_actionable=False,
                    rejection_reason=f"Ceremonial announcement or non-actionable administrative noise (matched {noise_pattern}).",
                    novelty_score=0.1,
                    actionable_summary=None,
                )

        # Check for actionable signals
        actionable_matches = 0
        for signal_pattern in ACTIONABLE_SIGNALS:
            matches = re.findall(signal_pattern, full_text)
            if matches:
                actionable_matches += len(matches)

        # Scoring heuristics
        if actionable_matches >= 2:
            # Actionable consulting signal
            summary = scan.summary if scan.summary and len(scan.summary) > 20 else scan.title
            novelty = min(1.0, 0.5 + (actionable_matches * 0.1))
            return FilterResult(
                is_actionable=True,
                rejection_reason=None,
                novelty_score=round(novelty, 2),
                actionable_summary=summary.strip(),
            )

        # Insufficient policy signal
        return FilterResult(
            is_actionable=False,
            rejection_reason="Item lacks substantive policy, regulatory, reform, or evaluation consulting implications.",
            novelty_score=0.2,
            actionable_summary=None,
        )

    def _filter_with_llm(self, scan: ScanRecord) -> FilterResult:
        """LangChain LLM-based filter."""
        from radar.pipeline.prompts import FILTER_SYSTEM_PROMPT
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", FILTER_SYSTEM_PROMPT),
            ("human", "Title: {title}\nSummary: {summary}\nContent: {content}"),
        ])

        structured_llm = self.llm.with_structured_output(FilterResult)
        chain = prompt | structured_llm
        return chain.invoke({
            "title": scan.title,
            "summary": scan.summary,
            "content": scan.raw_content[:2000],
        })
