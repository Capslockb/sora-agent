"""
S0RA Cron CLI — Manage scheduled tasks.
"""

import json
import os
import sys
from pathlib import Path

from sora_cli.config import load_config, load_sora_dotenv
from sora_constants import get_sora_home, get_cron_dir
from sora_logging import setup_logging

load_sora_dotenv()
setup_logging("cli")

# Import Hermes cron implementation (reuse the logic)
try:
    from hermes_cli.cron import (
        CronJob,
        CronScheduler,
        load_cron_jobs,
        save_cron_jobs,
        run_cron_job,
    )
except ImportError:
    # Fallback implementation
    CronJob = dict
    CronScheduler = None

    def load_cron_jobs():
        cron_dir = get_cron_dir()
        jobs = {}
        for job_file in cron_dir.glob("*.json"):
            try:
                import json
                with open(job_file) as f:
                    job = json.load(f)
                    jobs[job["id"]] = job
            except Exception:
                pass
        return jobs

    def save_cron_jobs(jobs):
        cron_dir = get_cron_dir()
        cron_dir.mkdir(parents=True, exist_ok=True)
        for job_id, job in jobs.items():
            with open(cron_dir / f"{job_id}.json", "w") as f:
                json.dump(job, f, indent=2)

    def run_cron_job(job):
        print(f"Running job {job['id']}: {job['prompt'][:50]}...")
        # Would actually execute the job
        return {"status": "success", "job_id": job["id"]}


def main(args) -> int:
    if args.cron_command is None:
        print("Usage: sora cron <list|add|create|edit|pause|resume|run|remove|status>")
        return 1

    jobs = load_cron_jobs()

    if args.cron_command == "list":
        if not jobs:
            print("No cron jobs configured.")
            return 0
        print(f"{'ID':<36} {'Status':<10} {'Schedule':<20} {'Prompt'}")
        print("-" * 100)
        for job in jobs.values():
            status = "enabled" if job.get("enabled", True) else "paused"
            schedule = job.get("schedule", "unknown")
            prompt = job.get("prompt", "")[:60]
            print(f"{job['id']:<36} {status:<10} {schedule:<20} {prompt}")
        return 0

    elif args.cron_command == "status":
        # Check if cron scheduler is running
        try:
            import subprocess
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "sora-cron"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print("SORA cron scheduler: active")
            else:
                print("SORA cron scheduler: inactive")
        except Exception:
            print("SORA cron scheduler: unknown (systemctl not available)")
        return 0

    elif args.cron_command in ("add", "create"):
        print("Interactive cron job creation not yet implemented.")
        print("Use: sora cron add (not yet available)")
        return 1

    elif args.cron_command == "run":
        # Would need job_id argument
        print("Usage: sora cron run <job_id> (not yet implemented)")
        return 1

    elif args.cron_command in ("pause", "resume", "remove", "edit"):
        print(f"sora cron {args.cron_command} not yet implemented")
        return 1

    else:
        print(f"Unknown cron command: {args.cron_command}")
        return 1