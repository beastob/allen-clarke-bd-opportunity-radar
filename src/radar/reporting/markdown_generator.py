"""Markdown Report Generator for Allen + Clarke Fortnightly Opportunity Radar."""

from typing import Any, Dict, List, Optional, Union
from radar.pipeline.models import BDOpportunity
from radar.reporting.models import ReportMetadata


class MarkdownReportGenerator:
    """Compiles scored opportunities into an executive markdown report strictly answering all 6 questions."""

    def generate_report(
        self,
        opportunities: List[BDOpportunity],
        title: Optional[str] = None,
        metadata: Optional[Union[Dict[str, Any], ReportMetadata]] = None,
    ) -> str:
        """Generates a comprehensive executive Markdown report.

        Args:
            opportunities: List of prioritized BDOpportunity instances.
            title: Optional custom report title.
            metadata: Optional dictionary or ReportMetadata instance.
        """
        meta = ReportMetadata.from_dict(metadata)
        report_title = title or "Allen + Clarke BD Opportunity Radar: Fortnightly Intelligence Briefing"
        scanned_count = meta.scanned_count if meta.scanned_count > 0 else len(opportunities)

        lines: List[str] = [
            f"# {report_title}",
            "",
            f"**Reporting Period**: {meta.period}  ",
            f"**Jurisdictions Covered**: {meta.jurisdiction} ({meta.jurisdiction_label})  ",
            f"**Total Policy Items Processed**: {scanned_count}  ",
            f"**Qualified Opportunities**: {len(opportunities)}  ",
            f"**Generated**: {meta.generated_at}  ",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
        ]

        if not opportunities:
            lines.extend([
                "No high-scoring opportunities identified in this scanning cycle.",
                "",
                "> [!NOTE]",
                "> All ingested items were either filtered as ceremonial/administrative noise or scored below actionable thresholds.",
                "",
            ])
            return "\n".join(lines)

        lines.extend([
            f"This fortnightly intelligence scan identified **{len(opportunities)} actionable business development opportunities** across {meta.jurisdiction_label} public sector jurisdictions. Each opportunity has been evaluated across our 0–100 scoring matrix (Strategic Fit /35, Urgency /35, Budget Likelihood /30) and rigorously structured against our 6 mandatory consulting evaluation questions with explicit separation of verified statutory facts from strategic consulting interpretations.",
            "",
            "### Opportunity Priority Matrix",
            "",
            "| Rank | Priority Score | Opportunity Title | Jurisdiction | Target Agency | Primary Service Line | Fit (/35) | Urgency (/35) | Budget (/30) |",
            "| :---: | :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: |",
        ])

        for idx, opp in enumerate(opportunities, start=1):
            fit = opp.score.strategic_fit_score
            urgency = opp.score.urgency_score
            budget = opp.score.budget_score
            total = opp.score.total_score
            lines.append(
                f"| **#{idx}** | **{total}/100** | [{opp.title}](#opportunity-{idx}-{opp.id}) | `{opp.jurisdiction}` | {opp.target_client_name} | {opp.service_line_name} | {fit} | {urgency} | {budget} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Prioritised Opportunity Deep Dives",
            "",
        ])

        for idx, opp in enumerate(opportunities, start=1):
            total = opp.score.total_score
            fit = opp.score.strategic_fit_score
            urgency = opp.score.urgency_score
            budget = opp.score.budget_score

            lines.extend([
                f"<a id=\"opportunity-{idx}-{opp.id}\"></a>",
                f"### #{idx}. [{total}/100] [{opp.jurisdiction}] {opp.title}",
                "",
                f"- **Opportunity ID**: `{opp.id}`",
                f"- **Target Client**: **{opp.target_client_name}** ({opp.jurisdiction})",
                f"- **Primary Service Line**: **{opp.service_line_name}**",
                f"- **Total Priority Score**: **{total}/100** (Strategic Fit: {fit}/35, Statutory Urgency: {urgency}/35, Budget Likelihood: {budget}/30)",
                f"- **Published / Gazette Date**: {opp.published_date}",
                f"- **Source Reference**: [{opp.url}]({opp.url})",
                "",
                "#### Q1: What has changed or is changing?",
                f"{opp.change_summary}",
                "",
                "#### Q2: Verified Facts vs Strategic Interpretation",
                "",
                "> **Verified Statutory Facts**  ",
                f"> {opp.verified_facts}",
                ">",
                "> **Strategic Consulting Interpretation**  ",
                f"> {opp.strategic_interpretation}",
                "",
                "#### Q3: Affected Public Sector Organisations & Sectors",
                f"- **Primary Target Agency**: {opp.target_client_name}",
                f"- **Directly Affected Sectors**: {', '.join(opp.affected_sectors) if opp.affected_sectors else 'Cross-government'}",
                "",
                "#### Q4: Operational Obligations & Timelines",
                "- **Operational Obligations for Affected Agencies**:",
            ])

            for obl in opp.operational_obligations:
                lines.append(f"  - {obl}")

            lines.append("- **Statutory & Compliance Deadlines**:")
            for dline in opp.compliance_deadlines:
                lines.append(f"  - {dline}")

            lines.extend([
                "",
                "#### Q5: Allen + Clarke Service Line Fit",
                f"- **Recommended Practice**: **{opp.service_line_name}**",
                f"- **Capability Alignment & Offering**: {opp.service_offering_summary}",
                "",
                "#### Q6: BD Action Plan & Outreach Strategy",
                f"- **Target Contact Persona**: `{opp.target_contact_persona}`",
                "- **Conversation Starter & Entry Angle**:",
                f"  > \"{opp.conversation_starter}\"",
                "- **Key Value Propositions & Pitch Angles**:",
            ])

            for angle in opp.key_pitch_angles:
                lines.append(f"  - {angle}")

            lines.extend([
                "",
                "---",
                "",
            ])

        lines.extend([
            "## About Allen + Clarke Opportunity Radar",
            "",
            "The Allen + Clarke BD Opportunity Radar is an automated intelligence pipeline monitoring public policy feeds across New Zealand (Beehive, NZ Parliament, NZ Gazette) and Australia (Federal Register of Legislation, Ministerial Releases, PM&C). It isolates actionable consulting opportunities, demarks statutory facts from consulting interpretations, and scores opportunities against A+C core capabilities.",
            "",
            "_Confidential — For internal Allen + Clarke Business Development & Practice Leadership use only._",
        ])

        return "\n".join(lines)
