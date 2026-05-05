"""CLI entry: vn-os <command>."""
from __future__ import annotations
import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option("0.1.0")
def main():
    """VN Business OS — AI agent OS for Vietnamese SMEs."""


@main.command()
@click.option("--vault", type=click.Path(), default=".", help="Path to vault")
def status(vault):
    """In trạng thái vault hiện tại."""
    from pathlib import Path
    from core.brain.reader import BrainReader

    try:
        ctx = BrainReader(Path(vault)).load()
        console.print(f"[green]✓[/] Brain loaded")
        console.print(f"  ICP: {ctx.strategy.icp[:60]}")
        console.print(f"  Products: {len(ctx.products)}")
        console.print(f"  Active depts: {len(ctx.headcount.active_departments)}")
    except FileNotFoundError as e:
        console.print(f"[red]✗[/] {e}")


@main.command()
@click.option("--brief", required=True, help="Task brief (Vietnamese)")
@click.option("--vault", type=click.Path(), default=".")
def run(brief, vault):
    """Chạy task qua orchestrator."""
    console.print(f"[yellow]TODO Phase 3:[/] sẽ kết nối orchestrator")
    console.print(f"Brief: {brief}")


@main.command()
def onboard():
    """Wizard tạo vault mới."""
    console.print(f"[yellow]TODO Phase 6:[/] onboard wizard")


if __name__ == "__main__":
    main()
