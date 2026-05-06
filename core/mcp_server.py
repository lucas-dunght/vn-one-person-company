"""MCP server wrapping vn-business-os FlowController as MCP tools.

Khi chạy trong Claude Desktop / Code, mọi LLM call route qua MCP sampling
(MCPSamplingProvider) — dùng subscription của user, không cần ANTHROPIC_API_KEY.

Run:
    python -m core.mcp_server          # stdio transport
    vn-os-mcp                          # via console_script (after install)

Tools registered (7):
    vn_run         — Stage 1: brief → router → gap → clarify (PAUSE)
    vn_resume      — Stage 2: resume after CEO answers clarification
    vn_meeting     — Stage 3: research + meeting → 07-decision-report.md (Stop 1)
    vn_approve     — Stage 4: CEO approves → 08-execution-plan.md (Stop 2)
    vn_execute     — Stage 5: render .docx/.xlsx into 03-Outputs/
    vn_status      — inspect vault (Brain summary + tasks)
    vn_onboard     — run onboard wizard creating new vault scaffold
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from core.brain.reader import BrainReader
from core.llm.providers import MCPSamplingProvider
from core.obsidian.vault import ObsidianVault
from core.orchestrator.flow_controller import FlowController


mcp = FastMCP("vn-business-os")


def _make_fc(vault_root: str, ctx: Context) -> FlowController:
    """Build FlowController bound to current MCP request session.

    `ctx.session` is the ServerSession exposing async `create_message(...)` —
    MCPSamplingProvider routes complete() through it (sampling protocol).
    """
    session = ctx.session
    llm = MCPSamplingProvider(session)
    return FlowController(vault_root=Path(vault_root), llm=llm)


def _vault_root_from_task(task_folder: Path) -> Path:
    """Task folders live at <vault>/02-Tasks/<slug>/ — climb 2 levels."""
    return task_folder.parent.parent


@mcp.tool()
def vn_run(brief: str, vault: str, ctx: Context) -> dict:
    """Stage 1: brief → router → gap → clarification (PAUSE).

    Returns task_folder path + stage. If stage == PAUSE_CLARIFICATION,
    CEO needs to answer questions in 03-clarification.md before vn_resume.
    """
    fc = _make_fc(vault, ctx)
    result = fc.run(brief)
    return {
        "stage": result.stage.value,
        "task_folder": str(result.task_folder),
        "message": result.message,
    }


@mcp.tool()
def vn_resume(task_folder: str, ctx: Context) -> dict:
    """Stage 2: resume after CEO answers 03-clarification.md.

    Validates all questions answered, writes 03-clarification-answered.md.
    """
    folder = Path(task_folder)
    fc = _make_fc(str(_vault_root_from_task(folder)), ctx)
    result = fc.resume_after_clarification(folder)
    return {
        "stage": result.stage.value,
        "task_folder": str(result.task_folder),
        "message": result.message,
    }


@mcp.tool()
def vn_meeting(
    task_folder: str,
    ctx: Context,
    departments: list[str] | None = None,
) -> dict:
    """Stage 3: research + meeting (Pro/Con + Perspective) + synthesizer.

    Auto-extracts departments from 01-routing.md if not provided.
    Output: 07-decision-report.md (Stop 1).
    """
    folder = Path(task_folder)
    fc = _make_fc(str(_vault_root_from_task(folder)), ctx)

    if not departments:
        routing_path = folder / "01-routing.md"
        if not routing_path.exists():
            return {
                "stage": "ERROR",
                "task_folder": str(folder),
                "message": "01-routing.md not found — run vn_run first",
            }
        m = re.search(r"\*\*Departments:\*\*\s*(.+)", routing_path.read_text(encoding="utf-8"))
        if not m:
            return {
                "stage": "ERROR",
                "task_folder": str(folder),
                "message": "Cannot parse Departments from 01-routing.md",
            }
        departments = [d.strip() for d in m.group(1).split(",") if d.strip()]

    result = fc.run_meeting(folder, departments=departments)
    return {
        "stage": result.stage.value,
        "task_folder": str(result.task_folder),
        "message": result.message,
    }


@mcp.tool()
def vn_approve(task_folder: str, ctx: Context) -> dict:
    """Stage 4: CEO approves decision report → 08-execution-plan.md (Stop 2)."""
    folder = Path(task_folder)
    fc = _make_fc(str(_vault_root_from_task(folder)), ctx)
    result = fc.approve_decision(folder)
    return {
        "stage": result.stage.value,
        "task_folder": str(result.task_folder),
        "message": result.message,
    }


@mcp.tool()
def vn_execute(task_folder: str, ctx: Context) -> dict:
    """Stage 5: render outputs (.docx/.xlsx) into vault/03-Outputs/<task>/."""
    folder = Path(task_folder)
    fc = _make_fc(str(_vault_root_from_task(folder)), ctx)
    result = fc.execute(folder)
    return {
        "stage": result.stage.value,
        "task_folder": str(result.task_folder),
        "message": result.message,
    }


@mcp.tool()
def vn_status(vault: str) -> dict:
    """Inspect vault — Brain summary + active depts + active tasks. No LLM."""
    vault_path = Path(vault)
    try:
        brain = BrainReader(vault_path).load()
    except FileNotFoundError as e:
        return {"error": str(e), "vault": vault}

    vault_obj = ObsidianVault(vault_path)
    tasks = vault_obj.list_tasks()

    return {
        "vault": str(vault_path),
        "icp": brain.strategy.icp[:200],
        "vision": brain.strategy.vision[:200],
        "products": len(brain.products),
        "active_departments": brain.headcount.active_departments,
        "state": brain.state,
        "active_tasks": [t.name for t in tasks],
    }


@mcp.tool()
def vn_onboard(vault: str, non_interactive: bool = True) -> dict:
    """Run onboard wizard creating new vault scaffold.

    With non_interactive=True (default for MCP), skips prompts:
    creates default vault scaffold + git init.
    """
    repo = Path(__file__).parent.parent
    cmd = [sys.executable, str(repo / "scripts" / "onboard.py"), "--vault", vault]
    if non_interactive:
        cmd.append("--non-interactive")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "vault": vault,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> None:
    """Entry point — run MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
