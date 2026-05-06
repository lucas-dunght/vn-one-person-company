from core.agents.pack_loader import PackLoader


def test_load_pack_yaml(tmp_path):
    pack_dir = tmp_path / "fnb"
    pack_dir.mkdir()
    (pack_dir / "pack.yaml").write_text("""
name: F&B Pack
code: fnb
version: 1.0.0
description: For restaurants
adds_departments: [13-kitchen]
extends_departments:
  - target: 05-operations
    add_agents: [inventory-manager-fnb]
brain_template: brain-template/
compliance_refs: ["VSATTP NĐ 15/2018"]
""", encoding="utf-8")

    loader = PackLoader(tmp_path)
    pack = loader.load("fnb")
    assert pack.code == "fnb"
    assert "13-kitchen" in pack.adds_departments
    assert pack.extends_departments[0].target == "05-operations"
