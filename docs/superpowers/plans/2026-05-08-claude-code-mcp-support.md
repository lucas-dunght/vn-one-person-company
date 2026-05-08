# Claude Code MCP Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `vn-os install-mcp` để đăng ký MCP server vào cả Claude Desktop và Claude Code global config (`~/.claude.json`) qua flag `--target [desktop|claude-code|both]`.

**Architecture:** Reuse hàm `install()` hiện có trong `install_mcp.py` (đã nhận `config_path` param). Thêm `get_claude_code_config_path()` + `install_for_target()` orchestrator. Update CLI thêm `--target` flag. Không thay đổi MCP server.

**Tech Stack:** Python 3.11+, click, pytest, pathlib

---

## File Map

| File | Thay đổi |
|------|----------|
| `core/install_mcp.py` | Thêm `get_claude_code_config_path()` + `install_for_target()` |
| `core/cli.py` | Thêm `--target` option vào `install-mcp` command |
| `adapters/claude-code/install.sh` | Update prerequisites + gọi `--target claude-code` |
| `tests/unit/test_install_mcp.py` | Thêm tests cho `get_claude_code_config_path()` + `install_for_target()` |

---

### Task 1: Thêm `get_claude_code_config_path()` + `install_for_target()` vào `install_mcp.py`

**Files:**
- Modify: `core/install_mcp.py`
- Test: `tests/unit/test_install_mcp.py`

- [ ] **Step 1: Viết failing tests**

Append vào cuối `tests/unit/test_install_mcp.py`:

```python
from core.install_mcp import get_claude_code_config_path, install_for_target


def test_get_claude_code_config_path_returns_dot_claude_json():
    p = get_claude_code_config_path()
    assert p.name == ".claude.json"
    assert p.parent == Path.home()


def test_install_for_target_desktop_only(tmp_path, monkeypatch):
    desktop_cfg = tmp_path / "claude_desktop_config.json"
    cc_cfg = tmp_path / "dot_claude.json"
    monkeypatch.setattr("core.install_mcp.get_config_path", lambda: desktop_cfg)
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    results = install_for_target("desktop", vault_path=None)

    assert results["desktop"]["ok"] is True
    assert desktop_cfg.exists()
    assert not cc_cfg.exists()


def test_install_for_target_claude_code_only(tmp_path, monkeypatch):
    desktop_cfg = tmp_path / "claude_desktop_config.json"
    cc_cfg = tmp_path / "dot_claude.json"
    monkeypatch.setattr("core.install_mcp.get_config_path", lambda: desktop_cfg)
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    results = install_for_target("claude-code", vault_path=None)

    assert results["claude-code"]["ok"] is True
    assert cc_cfg.exists()
    assert not desktop_cfg.exists()


def test_install_for_target_both(tmp_path, monkeypatch):
    desktop_cfg = tmp_path / "claude_desktop_config.json"
    cc_cfg = tmp_path / "dot_claude.json"
    monkeypatch.setattr("core.install_mcp.get_config_path", lambda: desktop_cfg)
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    results = install_for_target("both", vault_path=None)

    assert results["desktop"]["ok"] is True
    assert results["claude-code"]["ok"] is True
    assert desktop_cfg.exists()
    assert cc_cfg.exists()


def test_install_for_target_claude_code_preserves_existing_keys(tmp_path, monkeypatch):
    """Merge vào ~/.claude.json không xoá key khác (vd: theme, model)."""
    cc_cfg = tmp_path / "dot_claude.json"
    cc_cfg.write_text(json.dumps({"theme": "dark", "mcpServers": {}}), encoding="utf-8")
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    install_for_target("claude-code", vault_path=None)

    config = json.loads(cc_cfg.read_text(encoding="utf-8"))
    assert config["theme"] == "dark"
    assert "vn-business-os" in config["mcpServers"]


def test_install_for_target_invalid_target_raises():
    with pytest.raises(ValueError, match="target must be"):
        install_for_target("invalid", vault_path=None)
```

- [ ] **Step 2: Chạy tests để verify fail**

```bash
python -m pytest tests/unit/test_install_mcp.py::test_get_claude_code_config_path_returns_dot_claude_json tests/unit/test_install_mcp.py::test_install_for_target_both -v
```

Expected: `FAILED` với `ImportError: cannot import name 'get_claude_code_config_path'`

- [ ] **Step 3: Implement trong `core/install_mcp.py`**

Thêm 2 functions sau `get_server_command()` (trước `install()`):

```python
def get_claude_code_config_path() -> Path:
    """Return ~/.claude.json — global Claude Code MCP config (cross-platform)."""
    return Path.home() / ".claude.json"


def install_for_target(
    target: str = "both",
    vault_path: Optional[Path] = None,
) -> dict:
    """Install MCP server cho target: 'desktop', 'claude-code', hoặc 'both'.

    Returns dict với key là target name, value là install() result.
    Raises ValueError nếu target không hợp lệ.
    """
    valid = {"desktop", "claude-code", "both"}
    if target not in valid:
        raise ValueError(f"target must be one of {valid}, got {target!r}")

    results: dict = {}
    if target in ("desktop", "both"):
        results["desktop"] = install(
            config_path=get_config_path(),
            vault_path=vault_path,
        )
    if target in ("claude-code", "both"):
        results["claude-code"] = install(
            config_path=get_claude_code_config_path(),
            vault_path=vault_path,
        )
    return results
```

- [ ] **Step 4: Chạy tests để verify pass**

```bash
python -m pytest tests/unit/test_install_mcp.py -v
```

Expected: tất cả pass (bao gồm cả tests cũ).

- [ ] **Step 5: Commit**

```bash
git add core/install_mcp.py tests/unit/test_install_mcp.py
git commit -m "feat(install-mcp): add Claude Code config path + install_for_target()"
```

---

### Task 2: Update CLI — thêm `--target` flag

**Files:**
- Modify: `core/cli.py:168-198`

- [ ] **Step 1: Viết failing test**

Tạo `tests/unit/test_cli_install_mcp.py`:

```python
"""Test CLI install-mcp --target flag."""
from click.testing import CliRunner
from core.cli import main
import json


def test_install_mcp_default_target_is_both(tmp_path, monkeypatch):
    desktop_cfg = tmp_path / "desktop.json"
    cc_cfg = tmp_path / "cc.json"
    monkeypatch.setattr("core.install_mcp.get_config_path", lambda: desktop_cfg)
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    runner = CliRunner()
    result = runner.invoke(main, ["install-mcp"])

    assert result.exit_code == 0
    assert desktop_cfg.exists()
    assert cc_cfg.exists()


def test_install_mcp_target_claude_code(tmp_path, monkeypatch):
    desktop_cfg = tmp_path / "desktop.json"
    cc_cfg = tmp_path / "cc.json"
    monkeypatch.setattr("core.install_mcp.get_config_path", lambda: desktop_cfg)
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    runner = CliRunner()
    result = runner.invoke(main, ["install-mcp", "--target", "claude-code"])

    assert result.exit_code == 0
    assert cc_cfg.exists()
    assert not desktop_cfg.exists()
    assert "Claude Code" in result.output


def test_install_mcp_target_desktop(tmp_path, monkeypatch):
    desktop_cfg = tmp_path / "desktop.json"
    cc_cfg = tmp_path / "cc.json"
    monkeypatch.setattr("core.install_mcp.get_config_path", lambda: desktop_cfg)
    monkeypatch.setattr("core.install_mcp.get_claude_code_config_path", lambda: cc_cfg)

    runner = CliRunner()
    result = runner.invoke(main, ["install-mcp", "--target", "desktop"])

    assert result.exit_code == 0
    assert desktop_cfg.exists()
    assert not cc_cfg.exists()
    assert "Claude Desktop" in result.output
```

- [ ] **Step 2: Chạy test để verify fail**

```bash
python -m pytest tests/unit/test_cli_install_mcp.py -v
```

Expected: `FAILED` — `--target` option chưa có.

- [ ] **Step 3: Update `core/cli.py` — thay `install_mcp_cmd`**

Thay toàn bộ function `install_mcp_cmd` (dòng 168-198):

```python
@main.command(name="install-mcp")
@click.option(
    "--vault",
    type=click.Path(exists=True, file_okay=False),
    help="Vault path để load .env (TAVILY_API_KEY, ...) inject vào MCP env",
)
@click.option(
    "--target",
    type=click.Choice(["desktop", "claude-code", "both"], case_sensitive=False),
    default="both",
    show_default=True,
    help="Host để đăng ký MCP server",
)
def install_mcp_cmd(vault, target):
    """Install vn-business-os as MCP server (Claude Desktop + Claude Code).

    Mặc định đăng ký vào cả hai. Dùng --target để chọn riêng.

    Sau khi install, restart Claude Desktop / Claude Code để load server.
    """
    from core.install_mcp import install_for_target
    from pathlib import Path

    results = install_for_target(
        target=target,
        vault_path=Path(vault) if vault else None,
    )

    for host, result in results.items():
        label = "Claude Desktop" if host == "desktop" else "Claude Code"
        if not result["ok"]:
            console.print(f"[red]✗ {label}: {result.get('error', 'install failed')}[/]")
            continue
        console.print(f"[green]✓ {label}:[/] {result['config_path']}")
        if result.get("backup"):
            console.print(f"   Backup: {result['backup']}")
        if result.get("env_keys_injected"):
            console.print(f"   Env injected: {', '.join(result['env_keys_injected'])}")

    targets_installed = [k for k, v in results.items() if v.get("ok")]
    if targets_installed:
        parts = []
        if "desktop" in targets_installed:
            parts.append("Claude Desktop")
        if "claude-code" in targets_installed:
            parts.append("Claude Code")
        console.print(f"\n[bold]Bước tiếp:[/] Restart {' + '.join(parts)} để load MCP server.")
```

- [ ] **Step 4: Chạy tests để verify pass**

```bash
python -m pytest tests/unit/test_cli_install_mcp.py tests/unit/test_install_mcp.py -v
```

Expected: tất cả pass.

- [ ] **Step 5: Smoke test thủ công**

```bash
python -m core.cli install-mcp --help
```

Expected output có `--target [desktop|claude-code|both]`.

- [ ] **Step 6: Commit**

```bash
git add core/cli.py tests/unit/test_cli_install_mcp.py
git commit -m "feat(cli): add --target flag to install-mcp command"
```

---

### Task 3: Update `adapters/claude-code/install.sh`

**Files:**
- Modify: `adapters/claude-code/install.sh`

- [ ] **Step 1: Update script**

Thay toàn bộ nội dung `adapters/claude-code/install.sh`:

```bash
#!/usr/bin/env bash
# Install Claude Code skill + register MCP server in Claude Code global config.
set -euo pipefail

CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$CLAUDE_SKILLS_DIR/vn-business-os"

cp "$(dirname "$0")/skill.md" "$CLAUDE_SKILLS_DIR/vn-business-os/SKILL.md"
echo "✓ Skill installed to $CLAUDE_SKILLS_DIR/vn-business-os/"

# Register MCP server in Claude Code global config (~/.claude.json)
if command -v vn-os &>/dev/null; then
    vn-os install-mcp --target claude-code
    echo "✓ MCP server registered in ~/.claude.json"
else
    echo "⚠ vn-os not found. Run after installing package:"
    echo "    pip install -e ."
    echo "    vn-os install-mcp --target claude-code"
fi

echo ""
echo "Bước tiếp: restart Claude Code để load MCP server."
echo "Rồi gõ brief tiếng Việt trong Claude Code — skill tự kích hoạt."
```

- [ ] **Step 2: Verify script chạy được (dry)**

```bash
bash -n adapters/claude-code/install.sh
```

Expected: no syntax errors (exit 0).

- [ ] **Step 3: Commit**

```bash
git add adapters/claude-code/install.sh
git commit -m "feat(adapters): update claude-code install.sh to register MCP in Claude Code config"
```

---

### Task 4: Full test suite + final verify

- [ ] **Step 1: Chạy full test suite**

```bash
python -m pytest tests/ -q
```

Expected: tất cả pass (261+ tests, không có regression).

- [ ] **Step 2: Smoke test install lên máy thật**

```bash
python -m core.cli install-mcp --target claude-code
```

Expected:
```
✓ Claude Code: C:\Users\Admin\.claude.json
Bước tiếp: Restart Claude Code để load MCP server.
```

Verify `~/.claude.json` có entry:
```json
{
  "mcpServers": {
    "vn-business-os": {
      "command": "...",
      "args": []
    }
  }
}
```

- [ ] **Step 3: Commit nếu có thay đổi nhỏ từ smoke test**

```bash
git add -A && git commit -m "fix: adjust install-mcp output after smoke test"
```

_(Bỏ qua step này nếu không có thay đổi.)_
