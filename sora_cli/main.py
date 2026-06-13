    # Check if built
    cli_js = tui_path / "dist" / "cli.js"
    if not cli_js.exists():
        print("TUI not built. Run 'sora tui --build' first.", file=sys.stderr)
        return 1

    # Launch TUI
    print("Launching S0RA TUI...")
    try:
        subprocess.run(["node", str(cli_js)], cwd=tui_path)
    except Exception as e2:
        print(f"Failed to launch TUI: {e2}", file=sys.stderr)
        return 1
    return 0


def _handle_dashboard(args) -> int:
    """Handle dashboard commands."""
    subcommand = getattr(args, "dashboard_command", None)

    if subcommand is None:
        print("Sora Web Dashboard")
        print()
        print("Usage: sora dashboard <subcommand> [options]")
        print()
        print("Subcommands:")
        print("  start    Start dashboard server (production)")
        print("  dev      Start dashboard in development mode")
        print("  build    Build dashboard for production")
        print()
        return 0

    # Find website package location (works for both dev and pipx install)
    import importlib.util
    website_path = None
    spec = importlib.util.find_spec("website")
    if spec and spec.origin:
        website_path = Path(spec.origin).parent

    # Fallback to PROJECT_ROOT for development
    if website_path is None or not website_path.exists():
        website_path = PROJECT_ROOT / "website"

    if subcommand == "build":
        import subprocess
        tui_path = website_path
        print("Building dashboard...")
        result = subprocess.run(["npm", "install"], cwd=tui_path, capture_output=False)
        if result.returncode != 0:
            print("npm install failed", file=sys.stderr)
            return 1
        result = subprocess.run(["npm", "run", "build"], cwd=tui_path, capture_output=False)
        if result.returncode != 0:
            print("Build failed", file=sys.stderr)
            return 1
        print("Build complete!")
        return 0

    elif subcommand == "dev":
        import subprocess
        tui_path = website_path
        port = args.port
        print(f"Starting dashboard dev server on port {port}...")
        try:
            subprocess.run(["npm", "run", "dev", "--", "--port", str(port)], cwd=tui_path)
        except KeyboardInterrupt:
            pass
        return 0

    elif subcommand == "start":
        import subprocess
        import threading
        import time
        import uvicorn
        from sora_api import app

        # Start API server in background
        api_config = uvicorn.Config(app, host=args.host, port=args.api_port, log_level="warning")
        api_server = uvicorn.Server(api_config)

        def run_api():
            asyncio.run(api_server.serve())

        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()

        # Wait a moment for API to start
        time.sleep(1)

        # Start dashboard preview server
        tui_path = website_path
        dist_path = tui_path / "dist"
        if not dist_path.exists():
            print("Dashboard not built. Run 'sora dashboard build' first.")
            return 1

        print(f"Starting dashboard on http://{args.host}:{args.port}")
        print(f"API server on http://{args.host}:{args.api_port}")
        try:
            subprocess.run(["npx", "serve", "-s", "dist", "-l", str(args.port)], cwd=tui_path)
        except KeyboardInterrupt:
            pass
        return 0

    return 1