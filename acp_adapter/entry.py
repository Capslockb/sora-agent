"""
S0RA ACP (Agent Client Protocol) Adapter Entry Point.

This module allows S0RA to run as an ACP stdio server for editor integration.
"""

import asyncio
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


async def run_acp_server(port: int = 0) -> None:
    """Run the ACP server."""
    if port == 0:
        # stdio mode
        logger.info("Starting S0RA ACP server (stdio mode)")
        # TODO: Implement ACP stdio server
        print("S0RA ACP server started (stdio mode)", file=sys.stderr)
        # Keep running
        await asyncio.Event().wait()
    else:
        # TCP mode
        logger.info(f"Starting S0RA ACP server on port {port}")
        # TODO: Implement ACP TCP server
        print(f"S0RA ACP server started on port {port}", file=sys.stderr)
        await asyncio.Event().wait()


def main(args=None) -> int:
    """Main entry point for sora-acp command."""
    import argparse
    
    parser = argparse.ArgumentParser(prog="sora-acp", description="Run S0RA as ACP server")
    parser.add_argument("--port", type=int, default=0, help="Port for ACP server (0 = stdio)")
    parsed = parser.parse_args(args)
    
    try:
        asyncio.run(run_acp_server(parsed.port))
        return 0
    except KeyboardInterrupt:
        print("\nACP server stopped", file=sys.stderr)
        return 130
    except Exception as e:
        logger.error(f"ACP server error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())