"""CLI demo runner and pipeline orchestrator for Allen + Clarke BD Opportunity Radar."""

import argparse
from datetime import datetime, timezone
import logging
import sys
from typing import Any, Dict, List, Optional
from radar.db.database import DatabaseManager
from radar.db.seed import seed_database
from radar.ingestion.engine import IngestionEngine
from radar.pipeline.orchestrator import OpportunityPipeline
from radar.reporting.compiler import ReportCompiler
from radar.reporting.models import ReportMetadata

logger = logging.getLogger("radar.cli")


def configure_utf8_streams():
    """Configures stdout and stderr for UTF-8 encoding on Windows consoles."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# Ensure UTF-8 on load
configure_utf8_streams()


def build_parser() -> argparse.ArgumentParser:
    """Builds and configures the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_scan.py",
        description="Allen + Clarke Business Development Opportunity Radar CLI Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scan.py --offline
  python run_scan.py --jurisdiction NZ --max-items 5
  python run_scan.py --jurisdiction AU --offline --output-dir reports
        """,
    )

    parser.add_argument(
        "-j", "--jurisdiction",
        choices=["NZ", "AU", "ALL"],
        default="ALL",
        help="Target jurisdiction to scan ('NZ', 'AU', or 'ALL'). Defaults to 'ALL'.",
    )
    parser.add_argument(
        "-m", "--max-items",
        type=int,
        default=10,
        help="Maximum number of top-scoring opportunities to include in deliverables (default: 10, max: 10).",
    )

    # Boolean flag supporting --offline and --no-offline
    if hasattr(argparse, "BooleanOptionalAction"):
        parser.add_argument(
            "--offline",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run in offline mode using curated government feed fixtures (default: True).",
        )
    else:
        parser.add_argument(
            "--offline",
            dest="offline",
            action="store_true",
            default=True,
            help="Run in offline mode using curated fixtures.",
        )
        parser.add_argument(
            "--no-offline",
            dest="offline",
            action="store_false",
            help="Run live web feed scraping mode.",
        )

    parser.add_argument(
        "--provider",
        choices=["openrouter", "openai", "heuristics", "auto"],
        default="auto",
        help="LLM provider for multi-agent reasoning ('openrouter', 'openai', 'heuristics', or 'auto'). Defaults to 'auto'.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model identifier (e.g. 'anthropic/claude-3.5-sonnet', 'openai/gpt-4o-mini', 'google/gemini-2.5-flash').",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="LLM provider API key (defaults to OPENROUTER_API_KEY or OPENAI_API_KEY environment variables).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="LLM sampling temperature (default: 0.1).",
    )
    parser.add_argument(
        "--db-path",
        default="radar.db",
        help="Path to SQLite knowledge base database (default: 'radar.db').",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to save generated HTML and Markdown reports (default: 'reports').",
    )
    parser.add_argument(
        "--markdown-output",
        default="sample_bd_output.md",
        help="Path for candidate executive markdown report (default: 'sample_bd_output.md').",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        default=False,
        help="Force re-seeding the knowledge base with A+C service lines and client registry.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress console banners and table output.",
    )

    return parser


def run_scan(
    jurisdiction: str = "ALL",
    max_items: int = 10,
    offline: bool = True,
    provider: Optional[str] = "auto",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    db_path: str = "radar.db",
    output_dir: str = "reports",
    markdown_output: str = "sample_bd_output.md",
    seed: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> Dict[str, Any]:
    """Executes the full Opportunity Radar pipeline from ingestion to deliverable compilation."""
    configure_utf8_streams()

    # Ensure max_items is capped at 10
    capped_max_items = min(max(1, max_items), 10)

    # 1. Initialize Knowledge Base & DB
    db = DatabaseManager(db_path=db_path)
    db.initialize()

    # Seed if requested or if service_lines table is empty
    service_lines = db.get_service_lines()
    if seed or not service_lines:
        seed_database(db=db, force=seed)

    # Initialize LLM Provider (OpenRouter / OpenAI / Heuristics)
    from radar.pipeline.llm import get_llm
    selected_provider = None if provider == "auto" else provider
    llm = get_llm(
        provider=selected_provider,
        model=model,
        api_key=api_key,
        temperature=temperature,
    )

    if llm is not None:
        model_name = getattr(llm, "model_name", None) or getattr(llm, "model", "LLM")
        reasoning_desc = f"Active LLM ({model_name})"
    else:
        reasoning_desc = "Deterministic Heuristics Engine (Fast Offline)"

    if not quiet:
        print("=" * 80)
        print("   ALLEN + CLARKE BUSINESS DEVELOPMENT OPPORTUNITY RADAR")
        print("   Fortnightly Policy Ingestion & Multi-Agent Opportunity Reasoning")
        print("=" * 80)
        print(f" Jurisdictions : {jurisdiction}")
        print(f" Mode          : {'Offline Curated Fixtures' if offline else 'Live Web Feeds'}")
        print(f" Reasoning     : {reasoning_desc}")
        print(f" Max Items     : {capped_max_items}")
        print(f" Database      : {db_path}")
        print(f" Output Dir    : {output_dir}")
        print("-" * 80)

    # 2. Stage 1: Government Feed Ingestion
    if not quiet:
        print("\n[1/3] Ingesting government policy feeds and checking SHA-256 hashes...")
    ingestion_engine = IngestionEngine(db_manager=db)
    ingest_res = ingestion_engine.run_scan(
        jurisdiction=jurisdiction,
        use_fixtures=offline,
    )

    if not quiet:
        print(f"      [+] Total items fetched: {ingest_res.total_fetched}")
        print(f"      [+] New items ingested: {ingest_res.new_items}")
        print(f"      [+] Duplicates skipped: {ingest_res.duplicates_skipped}")

    # 3. Stage 2: 4-Agent Reasoning Pipeline
    if not quiet:
        print(f"\n[2/3] Executing 4-Agent LangChain Opportunity Reasoning Pipeline ({reasoning_desc})...")
        print("      - Agent 1: Ingestion Noise Filter")
        print("      - Agent 2: Impact & Sector Analysis (Fact vs. Interpretation)")
        print("      - Agent 3: A+C Service Line & Client Registry Matching")
        print("      - Agent 4: Prioritisation Scoring (0-100) & BD Action Plan")

    pipeline = OpportunityPipeline(
        db_manager=db,
        llm=llm if llm is not None else "heuristics",
    )
    pipeline_res = pipeline.run(
        jurisdiction=jurisdiction,
        max_items=capped_max_items,
    )

    if not quiet:
        print(f"      [+] Items processed: {pipeline_res.processed_count}")
        print(f"      [+] Noise filtered: {pipeline_res.filtered_noise_count}")
        print(f"      [+] Opportunities qualified & saved: {len(pipeline_res.opportunities)}")

    # 4. Stage 3: Deliverable & Report Compilation
    if not quiet:
        print("\n[3/3] Compiling Executive Markdown Report & HTML Email Digest...")

    period_str = datetime.now(timezone.utc).strftime("Fortnight Ending %d %B %Y")
    report_metadata = ReportMetadata(
        period=period_str,
        jurisdiction=jurisdiction,
        scanned_count=ingest_res.total_fetched,
        new_items_count=ingest_res.new_items,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    compiler = ReportCompiler(
        output_dir=output_dir,
        markdown_deliverable_path=markdown_output,
    )

    compile_res = compiler.compile_and_save(
        opportunities=pipeline_res.opportunities,
        metadata=report_metadata,
    )

    if not quiet:
        print(f"      [+] Executive Markdown Report: {compile_res['markdown_deliverable']}")
        print(f"      [+] HTML Email Digest:        {compile_res['html_digest']}")
        print(f"      [+] Reports Markdown Copy:     {compile_res['reports_markdown']}")

        print("\n" + "=" * 80)
        print("   TOP PRIORITISED BUSINESS DEVELOPMENT OPPORTUNITIES")
        print("=" * 80)

        if not pipeline_res.opportunities:
            print(" No qualified opportunities identified in this cycle.")
        else:
            header_fmt = "{:<5} {:<8} {:<4} {:<28} {:<26}"
            row_fmt = "{:<5} {:<8} {:<4} {:<28} {:<26}"
            print(header_fmt.format("Rank", "Score", "Jur", "Target Agency", "Service Line"))
            print("-" * 80)
            for idx, opp in enumerate(pipeline_res.opportunities, start=1):
                agency = opp.target_client_name[:26] + ".." if len(opp.target_client_name) > 28 else opp.target_client_name
                svc = opp.service_line_name[:24] + ".." if len(opp.service_line_name) > 26 else opp.service_line_name
                print(row_fmt.format(f"#{idx}", f"{opp.score.total_score}/100", opp.jurisdiction, agency, svc))
                print(f"      Title : {opp.title}")
                print(f"      Persona: {opp.target_contact_persona}")
                print(f"      Opener : \"{opp.conversation_starter[:70]}...\"")
                print("-" * 80)

        print("\nScan completed successfully.")
        print("=" * 80)

    return {
        "status": "success",
        "jurisdiction": jurisdiction,
        "total_fetched": ingest_res.total_fetched,
        "new_items_ingested": ingest_res.new_items,
        "duplicates_skipped": ingest_res.duplicates_skipped,
        "processed_count": pipeline_res.processed_count,
        "filtered_noise_count": pipeline_res.filtered_noise_count,
        "opportunities": pipeline_res.opportunities,
        "deliverables": compile_res,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    configure_utf8_streams()
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    try:
        run_scan(
            jurisdiction=args.jurisdiction,
            max_items=args.max_items,
            offline=args.offline,
            provider=args.provider,
            model=args.model,
            api_key=args.api_key,
            temperature=args.temperature,
            db_path=args.db_path,
            output_dir=args.output_dir,
            markdown_output=args.markdown_output,
            seed=args.seed,
            verbose=args.verbose,
            quiet=args.quiet,
        )
        return 0
    except Exception as e:
        logger.exception("Scan execution failed")
        print(f"\n[ERROR] Scan execution failed: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
