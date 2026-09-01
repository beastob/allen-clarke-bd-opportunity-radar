"""Main CLI entrypoint for running the FastMCP server or Opportunity Radar scanner."""

import sys


def entrypoint():
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        from radar.cli import main as cli_main
        sys.exit(cli_main(sys.argv[2:]))
    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        from radar.server import main as server_main
        sys.exit(server_main())
    else:
        # Default to server for FastMCP / MCP compatibility
        from radar.server import main as server_main
        server_main()


if __name__ == "__main__":
    entrypoint()
