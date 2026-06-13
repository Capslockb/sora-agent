"""
ACP Adapter — Run Sora as an ACP server for editor integration.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from sora_cli.config import load_sora_dotenv

load_sora_dotenv(project_env=PROJECT_ROOT / ".env")


async def main() -> int:
    """Run ACP server."""
    print("S0RA ACP Server")
    print("Not yet implemented - will use stdio for editor integration")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))