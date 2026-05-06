"""Test install_mcp — uses tmp_path to avoid touching real Claude Desktop config."""
import json
from pathlib import Path
import pytest
from core.install_mcp import install, uninstall, get_config_path


def test_get_config_path_returns_platform_specific(monkeypatch):
    """Path should differ by OS."""
    import platform
    p = get_config_path()
    assert "claude_desktop_config.json" in str(p).lower()
    sys = platform.system()
    if sys == "Windows":
        assert "Claude" in str(p)
    elif sys == "Darwin":
        assert "Library" in str(p)
    else:
        assert ".config" in str(p)


def test_install_creates_config_when_missing(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    result = install(config_path=cfg)

    assert result["ok"] is True
    assert cfg.exists()

    config = json.loads(cfg.read_text(encoding="utf-8"))
    assert "mcpServers" in config
    assert "vn-business-os" in config["mcpServers"]
    assert "command" in config["mcpServers"]["vn-business-os"]


def test_install_preserves_existing_servers(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(json.dumps({
        "mcpServers": {
            "other-server": {"command": "node", "args": ["/path/to/other.js"]}
        }
    }), encoding="utf-8")

    install(config_path=cfg)

    config = json.loads(cfg.read_text(encoding="utf-8"))
    assert "other-server" in config["mcpServers"]
    assert "vn-business-os" in config["mcpServers"]


def test_install_creates_backup(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")

    result = install(config_path=cfg)
    backup_path = Path(result["backup"])
    assert backup_path.exists()
    assert backup_path.suffix == ".bak"


def test_install_idempotent(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    install(config_path=cfg)
    install(config_path=cfg)  # second run should not error

    config = json.loads(cfg.read_text(encoding="utf-8"))
    # Still only 1 vn-business-os entry (no duplicate)
    assert list(config["mcpServers"].keys()).count("vn-business-os") == 1


def test_install_handles_malformed_json(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text("{ malformed json", encoding="utf-8")

    result = install(config_path=cfg)
    assert result["ok"] is False
    assert "malformed" in result["error"].lower()


def test_uninstall_removes_entry(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    install(config_path=cfg)

    result = uninstall(config_path=cfg)
    assert result["removed"] is True

    config = json.loads(cfg.read_text(encoding="utf-8"))
    assert "vn-business-os" not in config.get("mcpServers", {})


def test_uninstall_no_config_is_safe(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    result = uninstall(config_path=cfg)
    assert result["ok"] is True
    assert result["removed"] is False
