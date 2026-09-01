"""Allen + Clarke Business Development Opportunity Radar."""

from radar.briefing.pitch_generator import PitchGenerator
from radar.db.database import DatabaseManager
from radar.pipeline.orchestrator import OpportunityPipeline
from radar.server import create_mcp_server, mcp

__version__ = "0.1.0"

__all__ = [
    "DatabaseManager",
    "OpportunityPipeline",
    "PitchGenerator",
    "create_mcp_server",
    "mcp",
]

