"""
S0RA Benchmark CLI — Performance benchmarks for S0RA components.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

from sora_constants import get_default_sora_root
from sora_logging import setup_logging

setup_logging("cli")


BENCHMARKS = [
    ("CLI Startup", "sora --version", 100, "ms"),
    ("Config Load", "python -c \"from sora_cli.config import load_config; load_config()\"", 50, "ms"),
    ("Plugin Discovery", "sora plugins list >/dev/null", 200, "ms"),
    ("MCP Server Start", "timeout 5 sora mcp start --transport stdio >/dev/null 2>&1 || true", 500, "ms"),
    ("Voice Status Check", "sora voice status", 200, "ms"),
    ("Status Command", "sora status", 200, "ms"),
    ("Doctor Check", "sora doctor --quiet", 1000, "ms"),
]


def run_benchmark(cmd: str, target_ms: int) -> Tuple[float, bool]:
    """Run a single benchmark command and return (actual_ms, passed)."""
    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=10,
            cwd=str(get_default_sora_root()),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, result.returncode == 0
    except subprocess.TimeoutExpired:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, False
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, False


def run_all_benchmarks(json_output: bool = False) -> List[Dict]:
    """Run all benchmarks and return results."""
    results = []
    
    print("S0RA Benchmark Suite")
    print("=" * 60)
    print(f"{'Benchmark':<30} {'Target':>10} {'Actual':>10} {'Status'}")
    print("-" * 60)
    
    for name, cmd, target_ms, unit in BENCHMARKS:
        # Warmup run
        run_benchmark(cmd, target_ms)
        
        # Actual runs (3x)
        times = []
        success_count = 0
        for _ in range(3):
            elapsed_ms, success = run_benchmark(cmd, target_ms)
            if success:
                times.append(elapsed_ms)
            if success:
                success_count += 1
        
        if times:
            avg_ms = sum(times) / len(times)
            status = "✓ PASS" if avg_ms <= target_ms else "⚠ SLOW"
        else:
            avg_ms = 0
            status = "✗ FAIL"
        
        print(f"{name:<30} {f'{target_ms}{unit}':>10} {f'{avg_ms:.1f}{unit}':>10} {status}")
        
        results.append({
            "name": name,
            "target_ms": target_ms,
            "actual_ms": round(avg_ms, 1) if times else None,
            "success_rate": f"{success_count}/3",
            "status": "pass" if avg_ms <= target_ms and times else "fail" if not times else "slow",
        })
    
    print("-" * 60)
    passed = sum(1 for r in results if r["status"] == "pass")
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    
    if json_output:
        print(json.dumps(results, indent=2))
    
    return results


def main(args) -> int:
    """Main entry point for benchmark command."""
    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quick", action="store_true", help="Run quick subset")
    parsed = parser.parse_args(args)
    
    results = run_all_benchmarks(json_output=parsed.json)
    
    # Exit with error code if any failed
    failed = any(r["status"] == "fail" for r in results)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
