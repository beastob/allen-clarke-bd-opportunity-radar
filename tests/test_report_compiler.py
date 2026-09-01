from pathlib import Path
import pytest
from radar.reporting.compiler import ReportCompiler
from radar.reporting.models import ReportMetadata


def test_report_compiler_creates_artifacts_and_files(tmp_path, sample_opp):
    reports_dir = tmp_path / "reports"
    md_path = tmp_path / "sample_bd_output.md"

    compiler = ReportCompiler(
        output_dir=str(reports_dir),
        markdown_deliverable_path=str(md_path),
    )

    result = compiler.compile_and_save(
        opportunities=[sample_opp],
        metadata=ReportMetadata(jurisdiction="NZ", period="Fortnight Ending 15 March 2026"),
    )

    # 1. Output files exist
    assert md_path.exists()
    html_file = reports_dir / "latest_bd_radar.html"
    radar_md_file = reports_dir / "latest_bd_radar.md"
    assert html_file.exists()
    assert radar_md_file.exists()

    # 2. File contents are populated
    md_content = md_path.read_text(encoding="utf-8")
    assert "NZ Resource Management System Reform Guidelines" in md_content
    assert "Verified Statutory Facts" in md_content

    html_content = html_file.read_text(encoding="utf-8")
    assert "NZ Resource Management System Reform Guidelines" in html_content
    assert "<!DOCTYPE html>" in html_content

    # 3. Result dictionary returns paths
    assert "markdown_deliverable" in result
    assert "html_digest" in result
    assert "reports_markdown" in result
    assert result["total_opportunities"] == 1
