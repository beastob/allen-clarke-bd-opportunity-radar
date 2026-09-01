#!/usr/bin/env python3
"""Allen + Clarke Business Development Opportunity Radar CLI Demo Runner.

Executes the complete pipeline: government feed ingestion -> 4-agent reasoning -> report compilation.
"""

import sys
from radar.cli import configure_utf8_streams, main

if __name__ == "__main__":
    configure_utf8_streams()
    sys.exit(main())
