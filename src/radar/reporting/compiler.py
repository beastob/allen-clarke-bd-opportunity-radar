"""Report compiler coordinating Markdown and HTML deliverable generation."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from radar.pipeline.models import BDOpportunity
from radar.reporting.html_generator import HTMLReportGenerator
from radar.reporting.markdown_generator import MarkdownReportGenerator


class ReportCompiler:
    """Coordinates generation and persistence of Fortnightly Opportunity Radar deliverables."""

    def __init__(
        self,
        output_dir: str = "reports",
        markdown_deliverable_path: str = "sample_bd_output.md",
        markdown_generator: Optional[MarkdownReportGenerator] = None,
        html_generator: Optional[HTMLReportGenerator] = None,
    ):
        """Initializes the report compiler with destination paths and generators."""
        self.output_dir = Path(output_dir)
        self.markdown_deliverable_path = Path(markdown_deliverable_path)
        self.markdown_generator = markdown_generator or MarkdownReportGenerator()
        self.html_generator = html_generator or HTMLReportGenerator()

    def compile_and_save(
        self,
        opportunities: List[BDOpportunity],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compiles scored opportunities into Markdown and HTML deliverables and writes them to disk.

        Args:
            opportunities: List of scored BDOpportunity instances.
            metadata: Optional dictionary of metadata (period, jurisdiction, etc.).

        Returns:
            Dictionary containing paths to generated deliverables and compilation stats.
        """
        metadata = metadata or {}

        # 1. Generate Report Contents
        md_content = self.markdown_generator.generate_report(
            opportunities=opportunities,
            metadata=metadata,
        )

        html_content = self.html_generator.generate_email_digest(
            opportunities=opportunities,
            metadata=metadata,
        )

        # 2. Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.markdown_deliverable_path.parent:
            self.markdown_deliverable_path.parent.mkdir(parents=True, exist_ok=True)

        # 3. Write Deliverable Artifacts
        # Root executive candidate deliverable: sample_bd_output.md
        self.markdown_deliverable_path.write_text(md_content, encoding="utf-8")

        # HTML Email Digest: reports/latest_bd_radar.html
        html_path = self.output_dir / "latest_bd_radar.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Markdown copy in reports directory: reports/latest_bd_radar.md
        reports_md_path = self.output_dir / "latest_bd_radar.md"
        reports_md_path.write_text(md_content, encoding="utf-8")

        return {
            "status": "success",
            "markdown_deliverable": str(self.markdown_deliverable_path.resolve()),
            "html_digest": str(html_path.resolve()),
            "reports_markdown": str(reports_md_path.resolve()),
            "total_opportunities": len(opportunities),
            "markdown_content": md_content,
            "html_content": html_content,
        }
