"""NestWeaver command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from nestweaver import __version__
from nestweaver.autonomy import AutonomyOrchestrator, RoomWaypoint
from nestweaver.llm import OfflineEchoLLM, OllamaClient
from nestweaver.perception import PerceptionPipeline, SimulatedDepthCamera
from nestweaver.safety import SafetyInterlock

console = Console()


def _load_yaml(path: Path) -> dict:
    import yaml

    with path.open() as f:
        return yaml.safe_load(f) or {}


@click.group()
@click.version_option(__version__, prog_name="nestweaver")
def cli() -> None:
    """NestWeaver — privacy-first home companion robot SDK."""


@cli.command("doctor")
def doctor() -> None:
    """Check local environment (Python package, optional Ollama)."""
    table = Table(title="NestWeaver Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_row("nestweaver", f"ok ({__version__})")
    safety = SafetyInterlock()
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    table.add_row("safety interlocks", safety.status().state.name)
    ollama = OllamaClient()
    try:
        ok = ollama.health()
        table.add_row("ollama", "reachable" if ok else "not running")
    finally:
        ollama.close()
    console.print(table)


@cli.command("sim-demo")
@click.option("--scenario", type=click.Choice(["fetch", "tidy", "voice", "all"]), default="all")
def sim_demo(scenario: str) -> None:
    """Run an offline simulation demo (no hardware required)."""
    safety = SafetyInterlock()
    safety.heartbeat()
    safety.perception_tick()
    safety.control_tick()
    cam = SimulatedDepthCamera()
    perception = PerceptionPipeline(cam)
    llm = OfflineEchoLLM()
    bot = AutonomyOrchestrator(safety=safety, perception=perception, llm=llm)

    living = RoomWaypoint("living_room", 1.2, 0.4, 0.0)
    table = RoomWaypoint("coffee_table", 0.8, 0.1, 0.0)
    shelf = RoomWaypoint("toy_shelf", -0.5, 1.0, 1.57)

    if scenario in ("fetch", "all"):
        console.print("[bold]Navigate + fetch + deliver[/bold]")
        bot.navigate_to(living)
        bot.fetch_object("bottle")
        bot.deliver_to(table)
    if scenario in ("tidy", "all"):
        console.print("[bold]Tidy item[/bold]")
        bot.tidy_item("toy", shelf)
    if scenario in ("voice", "all"):
        console.print("[bold]Voice while moving[/bold]")
        reply = bot.voice_query_while_moving(
            "What's the weather plan for tidying?", living, context={"room": "living_room"}
        )
        console.print(reply)

    console.print("\n[green]Demo log:[/green]")
    for line in bot.state.log:
        console.print(f"  • {line}")


@cli.command("safety-status")
def safety_status() -> None:
    """Print current default safety status (fresh interlock instance)."""
    s = SafetyInterlock()
    s.heartbeat()
    s.perception_tick()
    s.control_tick()
    st = s.status()
    console.print_json(
        json.dumps(
            {
                "state": st.state.name,
                "motion_allowed": st.motion_allowed,
                "arm_allowed": st.arm_allowed,
                "reasons": st.reasons,
            }
        )
    )


@cli.command("chat")
@click.argument("message")
@click.option("--offline/--online", default=False, help="Use offline echo LLM")
def chat(message: str, offline: bool) -> None:
    """Send a prompt to local Ollama (or offline echo)."""
    if offline:
        console.print(OfflineEchoLLM().chat(message))
        return
    client = OllamaClient()
    try:
        if not client.health():
            console.print("[yellow]Ollama not reachable — falling back to offline echo.[/yellow]")
            console.print(OfflineEchoLLM().chat(message))
            return
        console.print(client.chat(message, context={"source": "cli"}))
    finally:
        client.close()


@cli.command("show-config")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def show_config(path: Path) -> None:
    """Pretty-print a YAML config file."""
    data = _load_yaml(path)
    console.print_json(json.dumps(data))


if __name__ == "__main__":
    cli()
