from pathlib import Path
import pytest
from radar.cli import build_parser, run_scan, main


def test_cli_arg_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.jurisdiction == "ALL"
    assert args.max_items == 10
    assert args.offline is True
    assert args.output_dir == "reports"
    assert args.markdown_output == "sample_bd_output.md"


def test_cli_arg_parser_custom():
    parser = build_parser()
    args = parser.parse_args([
        "--jurisdiction", "NZ",
        "--max-items", "5",
        "--no-offline",
        "--output-dir", "custom_reports",
        "--markdown-output", "custom_output.md",
        "--seed",
    ])
    assert args.jurisdiction == "NZ"
    assert args.max_items == 5
    assert args.offline is False
    assert args.output_dir == "custom_reports"
    assert args.markdown_output == "custom_output.md"
    assert args.seed is True


def test_run_scan_end_to_end_offline_execution(tmp_path):
    db_path = tmp_path / "test_radar.db"
    reports_dir = tmp_path / "reports"
    md_output = tmp_path / "sample_bd_output.md"

    result = run_scan(
        jurisdiction="ALL",
        max_items=5,
        offline=True,
        db_path=str(db_path),
        output_dir=str(reports_dir),
        markdown_output=str(md_output),
        seed=True,
        quiet=True,
    )

    assert result["status"] == "success"
    assert result["total_fetched"] > 0
    assert result["new_items_ingested"] > 0
    assert len(result["opportunities"]) <= 5
    assert len(result["opportunities"]) > 0

    # Verify deliverable files exist
    assert md_output.exists()
    assert (reports_dir / "latest_bd_radar.html").exists()
    assert (reports_dir / "latest_bd_radar.md").exists()

    # Verify fact vs interpretation separation in output
    md_content = md_output.read_text(encoding="utf-8")
    assert "Verified Statutory Facts" in md_content
    assert "Strategic Consulting Interpretation" in md_content


def test_run_scan_jurisdiction_filter_nz(tmp_path):
    db_path = tmp_path / "test_nz_radar.db"
    reports_dir = tmp_path / "reports"
    md_output = tmp_path / "sample_bd_output.md"

    result = run_scan(
        jurisdiction="NZ",
        max_items=5,
        offline=True,
        db_path=str(db_path),
        output_dir=str(reports_dir),
        markdown_output=str(md_output),
        seed=True,
        quiet=True,
    )

    assert result["status"] == "success"
    for opp in result["opportunities"]:
        assert opp.jurisdiction == "NZ"


def test_cli_main_entrypoint(tmp_path, monkeypatch):
    db_path = tmp_path / "cli_radar.db"
    reports_dir = tmp_path / "cli_reports"
    md_output = tmp_path / "cli_output.md"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_scan.py",
            "--jurisdiction", "AU",
            "--max-items", "3",
            "--offline",
            "--db-path", str(db_path),
            "--output-dir", str(reports_dir),
            "--markdown-output", str(md_output),
            "--seed",
        ],
    )

    exit_code = main()
    assert exit_code == 0
    assert md_output.exists()
    assert (reports_dir / "latest_bd_radar.html").exists()
