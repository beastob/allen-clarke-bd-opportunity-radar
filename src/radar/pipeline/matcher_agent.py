"""A+C Service Matching Agent (Agent 3).

Evaluates policy developments against Allen + Clarke's service line taxonomy and
historical client relationships to define tailored consulting offerings.
"""

import re
from typing import Any, List, Optional
from radar.models import Client, ScanRecord, ServiceLine
from radar.pipeline.models import ImpactAnalysis, ServiceMatch


class ServiceMatcherAgent:
    """Agent 3: A+C Service Matching Agent."""

    def __init__(self, llm: Optional[Any] = None):
        """Initializes the service matcher agent with optional LangChain LLM."""
        self.llm = llm

    def match_services(
        self,
        scan: ScanRecord,
        impact: ImpactAnalysis,
        service_lines: List[ServiceLine],
        clients: List[Client],
    ) -> ServiceMatch:
        """Matches a policy development to A+C practice taxonomy and client profile."""
        if self.llm is not None:
            try:
                return self._match_with_llm(scan, impact, service_lines, clients)
            except Exception:
                return self._match_with_heuristics(scan, impact, service_lines, clients)

        return self._match_with_heuristics(scan, impact, service_lines, clients)

    def _match_with_heuristics(
        self,
        scan: ScanRecord,
        impact: ImpactAnalysis,
        service_lines: List[ServiceLine],
        clients: List[Client],
    ) -> ServiceMatch:
        """Deterministic keyword and taxonomy scoring to match service lines and client accounts."""
        text_corpus = (
            f"{scan.title} {scan.summary} {scan.raw_content} "
            f"{impact.verified_facts} {impact.strategic_interpretation} "
            f"{' '.join(impact.operational_obligations)} {' '.join(impact.affected_sectors)}"
        ).lower()

        # 1. Match Service Lines
        sl_scores = {}
        for sl in service_lines:
            score = 0
            # Name and description match
            if sl.name.lower() in text_corpus:
                score += 5
            # Keyword matches
            for kw in sl.keywords:
                pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                matches = re.findall(pattern, text_corpus)
                score += len(matches) * 2

            sl_scores[sl.id] = score

        # Rank service lines
        ranked_sls = sorted(sl_scores.items(), key=lambda x: x[1], reverse=True)
        primary_sl_id = ranked_sls[0][0] if ranked_sls and ranked_sls[0][1] > 0 else (service_lines[0].id if service_lines else "policy_regulatory")
        secondary_sl_ids = [sl_id for sl_id, score in ranked_sls[1:3] if score > 0]

        primary_sl = next((sl for sl in service_lines if sl.id == primary_sl_id), None)
        primary_sl_name = primary_sl.name if primary_sl else "Policy & Regulatory Design"

        # 2. Match Target Client
        matched_client: Optional[Client] = None
        best_client_score = 0

        for client in clients:
            if client.jurisdiction not in (scan.jurisdiction, "ALL"):
                continue

            c_score = 0
            client_name_lower = client.name.lower()

            # Check direct name matches in affected agencies or text
            if any(client_name_lower in a.lower() or a.lower() in client_name_lower for a in impact.affected_agencies):
                c_score += 15
            elif client_name_lower in text_corpus:
                c_score += 8

            # Check division matches
            for div in client.key_divisions:
                if div.lower() in text_corpus:
                    c_score += 4

            # Sector alignment
            if any(client.sector.lower() in sec.lower() or sec.lower() in client.sector.lower() for sec in impact.affected_sectors):
                c_score += 3

            if c_score > best_client_score:
                best_client_score = c_score
                matched_client = client

        if matched_client and best_client_score >= 5:
            target_client_id = matched_client.id
            target_client_name = matched_client.name
            client_notes = f" (Tier: {matched_client.tier}, Sector: {matched_client.sector})"
            past_eng_ref = f" Prior engagements include {', '.join(matched_client.past_engagements[:2])}." if matched_client.past_engagements else ""
        else:
            target_client_id = None
            target_client_name = impact.affected_agencies[0] if impact.affected_agencies else "Public Sector Lead Agency"
            client_notes = ""
            past_eng_ref = ""

        # 3. Formulate Service Offering Summary
        obligations_str = impact.operational_obligations[0] if impact.operational_obligations else "policy implementation support"
        service_offering = f"{primary_sl_name} advisory support tailored for {target_client_name}, focusing on {obligations_str.lower()}."

        # 4. Formulate Fit Rationale
        fit_rationale = (
            f"Allen + Clarke has demonstrated deep institutional capability in {primary_sl_name}{client_notes}."
            f"{past_eng_ref} Our cross-jurisdictional track record across {scan.jurisdiction} public sector frameworks ensures rapid ramp-up and rigorous delivery."
        )

        return ServiceMatch(
            primary_service_line_id=primary_sl_id,
            secondary_service_line_ids=secondary_sl_ids,
            target_client_id=target_client_id,
            target_client_name=target_client_name,
            service_offering_summary=service_offering,
            fit_rationale=fit_rationale,
        )

    def _match_with_llm(
        self,
        scan: ScanRecord,
        impact: ImpactAnalysis,
        service_lines: List[ServiceLine],
        clients: List[Client],
    ) -> ServiceMatch:
        """LangChain LLM-based service matching."""
        from radar.pipeline.prompts import MATCHER_SYSTEM_PROMPT
        from langchain_core.prompts import ChatPromptTemplate

        sl_context = "\n".join([f"- ID: {s.id}, Name: {s.name}, Description: {s.description}" for s in service_lines])
        client_context = "\n".join([f"- ID: {c.id}, Name: {c.name}, Jurisdiction: {c.jurisdiction}, Sector: {c.sector}" for c in clients])

        prompt = ChatPromptTemplate.from_messages([
            ("system", MATCHER_SYSTEM_PROMPT),
            ("human", "Service Lines:\n{sl_context}\n\nClients:\n{client_context}\n\nScan:\nTitle: {title}\nJurisdiction: {jurisdiction}\nImpact Facts: {facts}\nInterpretation: {interpretation}\nAgencies: {agencies}\nObligations: {obligations}"),
        ])

        structured_llm = self.llm.with_structured_output(ServiceMatch)
        chain = prompt | structured_llm
        return chain.invoke({
            "sl_context": sl_context,
            "client_context": client_context,
            "title": scan.title,
            "jurisdiction": scan.jurisdiction,
            "facts": impact.verified_facts,
            "interpretation": impact.strategic_interpretation,
            "agencies": ", ".join(impact.affected_agencies),
            "obligations": "; ".join(impact.operational_obligations),
        })
