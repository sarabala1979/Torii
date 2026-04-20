"""
⛩️ Torii CLI
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

app = typer.Typer(
    name="torii",
    help="⛩️  Torii — The MCP gateway for your APIs and tools.",
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_config(config: Path):
    from torii.config import ToriiConfig

    if not config.exists():
        rprint(f"[red]Error:[/red] Config file not found: {config}")
        raise typer.Exit(1)
    try:
        return ToriiConfig.load(config)
    except Exception as e:
        rprint(f"[red]Error:[/red] Failed to load config: {e}")
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# serve
# ─────────────────────────────────────────────

@app.command()
def serve(
    config: Path = typer.Option(Path("torii.config.yaml"), "--config", "-c", help="Config file path"),
    port: int = typer.Option(None, "--port", "-p", help="Override server port"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Start the Torii MCP gateway."""
    _setup_logging(verbose)
    cfg = _load_config(config)

    if port:
        cfg.server.port = port

    rprint(f"\n[bold yellow]⛩️  Torii[/bold yellow] — {cfg.server.name}")
    rprint(f"   Config:   [cyan]{config}[/cyan]")
    rprint(f"   Endpoint: [cyan]http://{cfg.server.host}:{cfg.server.port}/mcp[/cyan]")
    rprint(f"   APIs:     {len(cfg.apis)}")
    rprint(f"   MCP Servers: {len(cfg.mcp_servers)}")
    rprint(f"   Workflows: {len(cfg.workflows)}\n")

    asyncio.run(_serve(cfg))


async def _serve(cfg) -> None:
    from torii.mcp.gateway import ToriiGateway
    import mcp.server.stdio as stdio

    gateway = ToriiGateway(cfg)
    await gateway.startup()

    rprint("[green]✓[/green] Gateway ready — listening for MCP connections\n")

    try:
        async with stdio.stdio_server() as (read_stream, write_stream):
            await gateway.server.run(
                read_stream,
                write_stream,
                gateway.get_initialization_options(),
            )
    finally:
        await gateway.shutdown()


# ─────────────────────────────────────────────
# validate
# ─────────────────────────────────────────────

@app.command()
def validate(
    config: Path = typer.Option(Path("torii.config.yaml"), "--config", "-c", help="Config file path"),
) -> None:
    """Validate a torii.config.yaml file."""
    cfg = _load_config(config)

    rprint(f"\n[green]✓[/green] Config is valid: [cyan]{config}[/cyan]\n")

    table = Table(title="Configuration Summary", show_header=True)
    table.add_column("Section", style="bold")
    table.add_column("Count")
    table.add_column("Details")

    api_tools = sum(len(a.endpoints) for a in cfg.apis)
    table.add_row("APIs", str(len(cfg.apis)), f"{api_tools} total endpoints/tools")
    table.add_row("MCP Servers", str(len(cfg.mcp_servers)),
                  ", ".join(s.name for s in cfg.mcp_servers) or "—")
    table.add_row("Workflows", str(len(cfg.workflows)),
                  ", ".join(w.name for w in cfg.workflows) or "—")

    console.print(table)
    rprint()


# ─────────────────────────────────────────────
# tools
# ─────────────────────────────────────────────

tools_app = typer.Typer(help="Inspect registered MCP tools")
app.add_typer(tools_app, name="tools")


@tools_app.command("list")
def tools_list(
    config: Path = typer.Option(Path("torii.config.yaml"), "--config", "-c"),
) -> None:
    """List all tools that Torii will expose."""
    cfg = _load_config(config)

    table = Table(title="Registered Tools", show_header=True, show_lines=True)
    table.add_column("Tool Name", style="cyan")
    table.add_column("Source")
    table.add_column("Description")

    for api in cfg.apis:
        for ep in api.endpoints:
            table.add_row(ep.tool_name, f"[yellow]api[/yellow] {api.name}", ep.description or "—")

    for srv in cfg.mcp_servers:
        ns = f"{srv.namespace}." if srv.namespace else ""
        table.add_row(f"{ns}*", f"[blue]mcp[/blue] {srv.name}", "Tools loaded at runtime")

    for wf in cfg.workflows:
        wf_tool = f"workflow_{wf.name.replace('-', '_')}"
        table.add_row(wf_tool, "[magenta]workflow[/magenta]", wf.description or "—")

    console.print(table)


# ─────────────────────────────────────────────
# version
# ─────────────────────────────────────────────

@app.command()
def version() -> None:
    """Show Torii version."""
    from torii import __version__
    rprint(f"⛩️  Torii [bold]{__version__}[/bold]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
