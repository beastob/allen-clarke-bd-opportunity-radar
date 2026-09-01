"""Multi-Agent Opportunity Reasoning Pipeline Orchestrator.

Coordinates Ingestion Filtering, Impact & Sector Analysis, Service Matching,
Prioritisation & BD Action formulation, and Post-Prioritisation Link QA Validation.
"""

from typing import Any, List, Optional
from radar.db.database import DatabaseManager
from radar.models import JurisdictionType, ScanRecord
from radar.pipeline.analyzer_agent import ImpactAnalyzerAgent
from radar.pipeline.filter_agent import IngestionFilterAgent
from radar.pipeline.llm import get_llm
from radar.pipeline.matcher_agent import ServiceMatcherAgent
from radar.pipeline.models import BDOpportunity, PipelineResult
from radar.pipeline.scoring_agent import PrioritisationAgent
from radar.pipeline.validator import LinkValidator


class OpportunityPipeline:
    """End-to-end 4-Agent LangChain Opportunity Reasoning Pipeline with Link QA."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        llm: Optional[Any] = None,
        filter_agent: Optional[IngestionFilterAgent] = None,
        analyzer_agent: Optional[ImpactAnalyzerAgent] = None,
        matcher_agent: Optional[ServiceMatcherAgent] = None,
        scoring_agent: Optional[PrioritisationAgent] = None,
        link_validator: Optional[LinkValidator] = None,
    ):
        """Initializes the multi-agent pipeline with storage, agents, and QA validator."""
        self.db_manager = db_manager or DatabaseManager()
        if llm in ("heuristics", False):
            self.llm = None
        elif llm is not None:
            self.llm = llm
        else:
            self.llm = get_llm()

        self.filter_agent = filter_agent or IngestionFilterAgent(llm=self.llm)
        self.analyzer_agent = analyzer_agent or ImpactAnalyzerAgent(llm=self.llm)
        self.matcher_agent = matcher_agent or ServiceMatcherAgent(llm=self.llm)
        self.scoring_agent = scoring_agent or PrioritisationAgent(llm=self.llm)
        self.link_validator = link_validator or LinkValidator()

    def run(
        self,
        scans: Optional[List[ScanRecord]] = None,
        jurisdiction: Optional[str] = None,
        max_items: int = 10,
        verify_http_links: bool = False,
    ) -> PipelineResult:
        """Executes the 4-agent reasoning pipeline across policy scans.

        1. Ingestion Noise Filtering (Agent 1)
        2. Impact & Sector Analysis with Fact vs Interpretation (Agent 2)
        3. A+C Service Line & Client Matching (Agent 3)
        4. Prioritisation, BD Action Formulation & Max-10 Capping (Agent 4)
        5. Post-Prioritisation Link QA Gate (Option 2)
        """
        # Load scans from database if not explicitly provided
        if scans is None:
            scans = self.db_manager.get_scans(jurisdiction=jurisdiction, limit=100)
        elif jurisdiction and jurisdiction != "ALL":
            scans = [s for s in scans if s.jurisdiction == jurisdiction]

        if not scans:
            return PipelineResult(
                processed_count=0,
                filtered_noise_count=0,
                opportunities=[],
                saved_count=0,
            )

        # Load knowledge base context from SQLite
        service_lines = self.db_manager.get_service_lines()
        clients = self.db_manager.get_clients()

        candidate_opportunities: List[BDOpportunity] = []
        filtered_noise_count = 0
        processed_count = 0

        for scan in scans:
            processed_count += 1

            # Stage 1: Ingestion & Noise Filtering
            filter_res = self.filter_agent.filter_item(scan)
            if not filter_res.is_actionable:
                filtered_noise_count += 1
                scan.status = "filtered_noise"
                self.db_manager.save_scan(scan)
                continue

            # Stage 2: Impact & Sector Analysis (Strict Fact vs. Interpretation)
            impact = self.analyzer_agent.analyze_impact(scan)

            # Stage 3: A+C Service Line & Client Matching
            match = self.matcher_agent.match_services(scan, impact, service_lines, clients)

            # Stage 4: Prioritisation & BD Action formulation
            opp = self.scoring_agent.score_opportunity(scan, impact, match)
            candidate_opportunities.append(opp)

            # Update scan status
            scan.status = "processed"
            self.db_manager.save_scan(scan)

        # Apply strict ranking and top-N cap
        top_opportunities = self.scoring_agent.rank_and_cap(
            candidate_opportunities,
            max_items=max_items,
        )

        # Stage 5: Post-Prioritisation Link QA Validation Gate (Option 2)
        validated_opportunities = self.link_validator.validate_opportunities(
            top_opportunities,
            strict_syntax=True,
            verify_http=verify_http_links,
        )

        # Persist qualified opportunities to SQLite
        saved_count = 0
        for opp in validated_opportunities:
            self.db_manager.save_opportunity(opp.to_db_record())
            saved_count += 1

        return PipelineResult(
            processed_count=processed_count,
            filtered_noise_count=filtered_noise_count,
            opportunities=validated_opportunities,
            saved_count=saved_count,
        )
