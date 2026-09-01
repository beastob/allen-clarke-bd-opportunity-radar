"""FastMCP Server for Allen + Clarke Business Development Opportunity Radar.

Exposes BD tools over stdio and SSE transport for AI desktop tools (Claude Desktop, Cursor, etc.).
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from radar.briefing.pitch_generator import PitchGenerator
from radar.db.database import DatabaseManager
from radar.ingestion.engine import IngestionEngine
from radar.pipeline.llm import get_llm, get_llm_status
from radar.pipeline.orchestrator import OpportunityPipeline

logger = logging.getLogger(__name__)


def create_mcp_server(
    db_manager: Optional[DatabaseManager] = None,
    db_path: str = "radar.db",
    llm: Optional[Any] = None,
) -> FastMCP:
    """Creates and configures the FastMCP server with all BD tools."""
    db = db_manager or DatabaseManager(db_path=db_path)
    pitch_generator = PitchGenerator()
    active_llm = llm if llm is not None else get_llm()

    mcp = FastMCP(
        "Allen-Clarke-BD-Opportunity-Radar",
        instructions=(
            "FastMCP server providing Business Development intelligence and workflow automation "
            "for Allen + Clarke across New Zealand and Australian public sector opportunities."
        ),
    )

    @mcp.tool()
    def get_system_status() -> Dict[str, Any]:
        """Returns the real-time operational status of the Radar, including LLM provider, OpenRouter configuration, and database stats."""
        llm_diag = get_llm_status()
        service_lines_count = len(db.get_service_lines())
        clients_count = len(db.get_clients())
        scans_count = len(db.get_scans(limit=1000))
        opps_count = len(db.get_opportunities(limit=1000))

        return {
            "status": "online",
            "llm_configuration": llm_diag,
            "knowledge_base": {
                "db_path": db.db_path,
                "service_lines_count": service_lines_count,
                "clients_count": clients_count,
                "scans_count": scans_count,
                "opportunities_count": opps_count,
            },
        }

    @mcp.tool()
    def trigger_policy_scan(
        jurisdiction: str = "ALL",
        use_fixtures: bool = False,
        max_items: int = 10,
    ) -> Dict[str, Any]:
        """Executes an on-demand scan across NZ and AU policy feeds and returns ranked opportunities.

        Args:
            jurisdiction: Target jurisdiction ('NZ', 'AU', or 'ALL'). Defaults to 'ALL'.
            use_fixtures: When True, uses curated policy fixtures instead of live web feeds.
            max_items: Maximum number of prioritized opportunities to return (default 10).
        """
        clean_jurisdiction = jurisdiction.strip().upper() if jurisdiction else "ALL"
        if clean_jurisdiction not in ("NZ", "AU", "ALL"):
            return {
                "status": "error",
                "error": f"Invalid jurisdiction '{jurisdiction}'. Must be one of: 'NZ', 'AU', 'ALL'.",
            }

        if max_items <= 0:
            return {
                "status": "error",
                "error": "max_items must be a positive integer greater than 0.",
            }

        try:
            # 1. Ingest policy feeds
            ingestion_engine = IngestionEngine(db_manager=db)
            ingest_result = ingestion_engine.run_scan(
                jurisdiction=clean_jurisdiction,
                use_fixtures=use_fixtures,
            )

            # 2. Execute multi-agent reasoning pipeline
            pipeline = OpportunityPipeline(db_manager=db, llm=active_llm)
            pipeline_result = pipeline.run(
                jurisdiction=clean_jurisdiction,
                max_items=max_items,
            )

            formatted_opps = [
                {
                    "id": opp.id,
                    "title": opp.title,
                    "jurisdiction": opp.jurisdiction,
                    "target_client_name": opp.target_client_name,
                    "primary_service_line_name": opp.service_line_name,
                    "total_score": opp.score.total_score,
                    "score_breakdown": {
                        "strategic_fit": opp.score.strategic_fit_score,
                        "urgency": opp.score.urgency_score,
                        "budget": opp.score.budget_score,
                    },
                    "verified_facts": opp.verified_facts,
                    "strategic_interpretation": opp.strategic_interpretation,
                    "target_contact_persona": opp.target_contact_persona,
                    "conversation_starter": opp.conversation_starter,
                    "key_pitch_angles": opp.key_pitch_angles,
                    "six_questions": opp.six_questions,
                }
                for opp in pipeline_result.opportunities
            ]

            return {
                "status": "success",
                "jurisdiction": clean_jurisdiction,
                "total_fetched": ingest_result.total_fetched,
                "new_items_ingested": ingest_result.new_items,
                "duplicates_skipped": ingest_result.duplicates_skipped,
                "processed_count": pipeline_result.processed_count,
                "filtered_noise_count": pipeline_result.filtered_noise_count,
                "total_opportunities": len(formatted_opps),
                "opportunities": formatted_opps,
            }

        except Exception as e:
            logger.exception("Failed to execute trigger_policy_scan")
            return {
                "status": "error",
                "error": f"Failed to execute policy scan: {str(e)}",
            }

    @mcp.tool()
    def query_opportunities(
        client: Optional[str] = None,
        sector: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        min_score: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Searches the SQLite knowledge base for ranked opportunities filtered by client, sector, or score.

        Args:
            client: Client name or ID to filter by (e.g. 'Ministry of Health' or 'nz-healthnz').
            sector: Sector to filter by (e.g. 'Health', 'Environment', 'Social Services').
            jurisdiction: Jurisdiction ('NZ', 'AU', or 'ALL').
            min_score: Minimum total priority score (0-100). Defaults to 0.
            limit: Maximum number of opportunities to retrieve (default 20).
        """
        if min_score < 0 or min_score > 100:
            return {
                "status": "error",
                "error": f"min_score must be between 0 and 100 (received {min_score}).",
            }

        if limit <= 0:
            return {
                "status": "error",
                "error": f"limit must be a positive integer (received {limit}).",
            }

        clean_jurisdiction = None
        if jurisdiction:
            clean_jurisdiction = jurisdiction.strip().upper()
            if clean_jurisdiction not in ("NZ", "AU", "ALL"):
                return {
                    "status": "error",
                    "error": f"Invalid jurisdiction '{jurisdiction}'. Must be one of: 'NZ', 'AU', 'ALL'.",
                }

        try:
            opps = db.query_opportunities(
                client=client.strip() if client else None,
                sector=sector.strip() if sector else None,
                jurisdiction=clean_jurisdiction,
                min_score=min_score,
                limit=limit,
            )

            return {
                "status": "success",
                "count": len(opps),
                "opportunities": opps,
            }

        except Exception as e:
            logger.exception("Failed to execute query_opportunities")
            return {
                "status": "error",
                "error": f"Failed to query opportunities: {str(e)}",
            }

    @mcp.tool()
    def generate_pitch_brief(
        opportunity_id: str,
        contact_name: Optional[str] = None,
        custom_angle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates a personalized 1-page client outreach email draft and talking points for an opportunity.

        Args:
            opportunity_id: The ID of the target opportunity (e.g. 'opp-nz-health-001').
            contact_name: Optional name of the client decision maker (e.g. 'Dr. Sarah Jenkins').
            custom_angle: Optional custom BD entry angle or focal point to emphasize.
        """
        cleaned_id = opportunity_id.strip() if opportunity_id else ""
        if not cleaned_id:
            return {
                "status": "error",
                "error": "opportunity_id must not be empty.",
            }

        try:
            opp = db.get_opportunity_by_id(cleaned_id)
            if not opp:
                return {
                    "status": "error",
                    "error": f"Opportunity not found for ID '{cleaned_id}'.",
                }

            client = db.get_client_by_id(opp.target_client_id) if opp.target_client_id else None
            service_line = db.get_service_line_by_id(opp.primary_service_line_id) if opp.primary_service_line_id else None

            brief = pitch_generator.generate_brief(
                opportunity=opp,
                client=client,
                service_line=service_line,
                contact_name=contact_name.strip() if contact_name else None,
                custom_angle=custom_angle.strip() if custom_angle else None,
            )

            return {
                "status": "success",
                "pitch_brief": brief,
            }

        except Exception as e:
            logger.exception("Failed to generate pitch brief")
            return {
                "status": "error",
                "error": f"Failed to generate pitch brief: {str(e)}",
            }

    @mcp.tool()
    def add_client_context(
        client_id: str,
        relationship_notes: str,
        append: bool = True,
    ) -> Dict[str, Any]:
        """Ingests meeting notes and relationship updates into the client registry.

        Args:
            client_id: Client identifier or name (e.g. 'nz-healthnz' or 'Health New Zealand').
            relationship_notes: Meeting notes, relationship context, or strategic updates.
            append: If True, appends notes with timestamp; if False, replaces existing notes.
        """
        cleaned_id = client_id.strip() if client_id else ""
        cleaned_notes = relationship_notes.strip() if relationship_notes else ""

        if not cleaned_id:
            return {
                "status": "error",
                "error": "client_id must not be empty.",
            }

        if not cleaned_notes:
            return {
                "status": "error",
                "error": "relationship_notes must not be empty.",
            }

        try:
            client = db.update_client_relationship_notes(
                client_id=cleaned_id,
                relationship_notes=cleaned_notes,
                append=append,
            )

            if not client:
                return {
                    "status": "error",
                    "error": f"Client not found for ID or name '{cleaned_id}'.",
                }

            return {
                "status": "success",
                "client_id": client.id,
                "client_name": client.name,
                "jurisdiction": client.jurisdiction,
                "sector": client.sector,
                "relationship_notes": client.relationship_notes,
                "updated_at": client.updated_at,
            }

        except Exception as e:
            logger.exception("Failed to update client context")
            return {
                "status": "error",
                "error": f"Failed to add client context: {str(e)}",
            }

    return mcp


# Default server instance using standard radar.db
mcp = create_mcp_server()


def main():
    """CLI entrypoint supporting stdio and SSE transport."""
    parser = argparse.ArgumentParser(description="Allen + Clarke BD Opportunity Radar FastMCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (stdio or sse). Defaults to stdio.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host address for SSE server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for SSE server.")
    parser.add_argument("--db-path", default="radar.db", help="Path to SQLite radar database.")

    args = parser.parse_args()

    server = create_mcp_server(db_path=args.db_path)

    if args.transport == "sse":
        server.settings.host = args.host
        server.settings.port = args.port
        print(f"Starting FastMCP SSE server on http://{args.host}:{args.port}/sse ...", file=sys.stderr)
        server.run(transport="sse")
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
