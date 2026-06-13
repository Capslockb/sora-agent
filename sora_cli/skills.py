"""
S0RA Skills CLI — Skill management.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from sora_constants import get_skills_dir, get_optional_skills_dir, get_sora_home
from sora_cli.config import load_config, save_config
from sora_logging import setup_logging
from sora_cli.cli_output import print_error, print_success, print_info, print_warning

setup_logging("cli")


def list_skills(args) -> int:
    skills_dir = get_skills_dir()
    optional_dir = get_optional_skills_dir()

    print("Installed Skills:")
    print("=" * 60)

    # User skills
    if skills_dir.exists():
        user_skills = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
        if user_skills:
            print("\nUser Skills:")
            for skill in sorted(user_skills):
                print(f"  {skill}")
        else:
            print("\nUser Skills: none")
    else:
        print("\nUser Skills: none (directory doesn't exist)")

    # Optional/bundled skills
    if optional_dir.exists():
        optional_skills = [d.name for d in optional_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
        if optional_skills:
            print("\nBundled (Optional) Skills:")
            for skill in sorted(optional_skills):
                print(f"  {skill}")
        else:
            print("\nBundled Skills: none")
    else:
        print("\nBundled Skills: not found (not in source repo)")

    return 0


def search_skills(args) -> int:
    query = args.query if hasattr(args, 'query') and args.query else ""
    if not query:
        query = input("Search query: ").strip()
    if not query:
        return 0

    print_info(f"Searching for skills matching: {query}")
    # Would search skill registry or GitHub
    print_warning("Skill search not yet implemented — would query skill registry")
    return 0


def browse_skills(args) -> int:
    print_warning("Skill browsing not yet implemented")
    return 0


def inspect_skill(args) -> int:
    skill_name = args.skill_name if hasattr(args, 'skill_name') and args.skill_name else ""
    if not skill_name:
        print_error("Usage: sora skills inspect <name>")
        return 1

    skills_dir = get_skills_dir()
    optional_dir = get_optional_skills_dir()

    for base in [skills_dir, optional_dir]:
        skill_dir = base / skill_name
        if skill_dir.exists():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                print(skill_md.read_text())
                return 0
            else:
                print_error(f"Skill directory exists but no SKILL.md: {skill_dir}")
                return 1

    print_error(f"Skill not found: {skill_name}")
    return 1


def install_skill(args) -> int:
    skill_name = args.skill_name if hasattr(args, 'skill_name') and args.skill_name else ""
    if not skill_name:
        print_error("Usage: sora skills install <name|github_repo>")
        return 1

    skills_dir = get_skills_dir()
    skills_dir.mkdir(parents=True, exist_ok=True)

    # If it's a GitHub repo
    if "/" in skill_name and not skill_name.startswith("."):
        repo = skill_name
        repo_name = repo.split("/")[-1].replace(".git", "")
        target = skills_dir / repo_name

        if target.exists():
            print_error(f"Skill already exists: {target}")
            return 1

        print_info(f"Cloning {repo}...")
        try:
            subprocess.run(["git", "clone", f"https://github.com/{repo}.git", str(target)], check=True)
        except subprocess.CalledProcessError:
            print_error("Failed to clone repository")
            return 1

        # Check for SKILL.md
        if not (target / "SKILL.md").exists():
            print_warning("No SKILL.md found — may not be a valid skill")

        print_success(f"Installed skill: {repo_name}")
        return 0
    else:
        # Try to find in optional skills
        optional_dir = get_optional_skills_dir()
        source = optional_dir / skill_name
        if source.exists():
            target = skills_dir / skill_name
            if target.exists():
                print_error(f"Skill already installed: {skill_name}")
                return 1
            shutil.copytree(source, target)
            print_success(f"Installed bundled skill: {skill_name}")
            return 0
        else:
            print_error(f"Skill not found: {skill_name} (not in bundled skills, try GitHub repo)")
            return 1


def audit_skills(args) -> int:
    print_warning("Skill audit not yet implemented")
    return 0


def update_skills(args) -> int:
    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        print_info("No user skills to update")
        return 0

    updated = 0
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / ".git").exists():
            print_info(f"Updating {skill_dir.name}...")
            try:
                subprocess.run(["git", "-C", str(skill_dir), "pull"], check=True, capture_output=True)
                print_success(f"  Updated {skill_dir.name}")
                updated += 1
            except subprocess.CalledProcessError:
                print_warning(f"  Failed to update {skill_dir.name}")

    if updated == 0:
        print_info("No skills updated")
    return 0


def main(args) -> int:
    if args.skills_command is None:
        print("Usage: sora skills <search|browse|inspect|install|audit|list|update>")
        return 1

    # Handle commands that need additional arguments
    handlers = {
        "list": list_skills,
        "search": search_skills,
        "browse": browse_skills,
        "inspect": inspect_skill,
        "install": install_skill,
        "audit": audit_skills,
        "update": update_skills,
    }

    handler = handlers.get(args.skills_command)
    if handler:
        return handler(args)
    else:
        print_error(f"Unknown skills command: {args.skills_command}")
        return 1