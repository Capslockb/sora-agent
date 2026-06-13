# ---- Subcommand handlers (lazy import to keep startup fast) ----

def _handle_voip(args) -> int:
    from sora_cli.voip import main as voip_main
    return voip_main(args)


def _handle_providers(args) -> int:
    from sora_cli.providers import main as providers_main
    return providers_main(args)


def _handle_chat(args) -> int:
    from sora_cli.cli import main as cli_main
    return cli_main(args)


def _handle_setup(args) -> int:
    from sora_cli.setup import main as setup_main
    return setup_main(args)


def _handle_voice(args) -> int:
    from sora_cli.voice import main as voice_main
    return voice_main(args)


def _handle_mcp(args) -> int:
    from sora_cli.mcp import main as mcp_main
    return mcp_main(args)


def _handle_status(args) -> int:
    from sora_cli.status import main as status_main
    return status_main(args)


def _handle_cron(args) -> int:
    from sora_cli.cron import main as cron_main
    return cron_main(args)


def _handle_doctor(args) -> int:
    from sora_cli.doctor import main as doctor_main
    return doctor_main(args)


def _handle_benchmark(args) -> int:
    from sora_cli.benchmark import main as benchmark_main
    return benchmark_main(args)


def _handle_logs(args) -> int:
    from sora_cli.logs import main as logs_main
    return logs_main(args)


def _handle_config(args) -> int:
    from sora_cli.config_cmd import main as config_main
    return config_main(args)


def _handle_plugins(args) -> int:
    from sora_cli.plugins import main as plugins_main
    return plugins_main(args)


def _handle_skills(args) -> int:
    from sora_cli.skills import main as skills_main
    return skills_main(args)


def _handle_update(args) -> int:
    from sora_cli.update import main as update_main
    return update_main(args)


def _handle_uninstall(args) -> int:
    from sora_cli.uninstall import main as uninstall_main
    return uninstall_main(args)


def _handle_acp(args) -> int:
    from sora_cli.acp import main as acp_main
    return acp_main(args)


def _handle_tui(args) -> int:
    from sora_cli.tui import main as tui_main
    return tui_main(args)