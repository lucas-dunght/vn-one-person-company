# Phase 5 — Departments + Industry Packs + BYOT + Doc Writer

**Goal:** Hoàn thiện 13 phòng core với agents thật + ship 3 industry pack (F&B / Retail / Tech-SaaS) + Template Resolver (RULE 6 BYOT) + Doc Writer (.docx/.xlsx).

**Dependency:** Phase 1, 2, 3, 4.

**Estimated tasks:** 12

---

### Task 1: Agent loader (parse .md với frontmatter)

**Files:**
- Create: `core/agents/agent_loader.py`
- Create: `tests/unit/test_agent_loader.py`

- [ ] **Step 1.1: Write failing test**

```python
# tests/unit/test_agent_loader.py
from pathlib import Path
import pytest
from core.agents.agent_loader import AgentLoader, AgentDefinition


def test_load_agent_from_md(tmp_path):
    agent_path = tmp_path / "ads-specialist.md"
    agent_path.write_text("""---
id: ads-specialist
name_vn: "Chuyên viên Quảng cáo"
department: 07-marketing
expertise: ["FB Ads", "Google Ads"]
required_tools: [vn_law_search]
temperature: 0.3
---
# Chuyên viên Quảng cáo

Bạn là chuyên viên quảng cáo digital VN.
""", encoding="utf-8")
    
    loader = AgentLoader()
    agent = loader.load(agent_path)
    
    assert agent.id == "ads-specialist"
    assert agent.name_vn == "Chuyên viên Quảng cáo"
    assert "FB Ads" in agent.expertise
    assert "vn_law_search" in agent.required_tools
    assert agent.temperature == 0.3
    assert "chuyên viên quảng cáo" in agent.system_prompt.lower()


def test_missing_required_field_raises(tmp_path):
    agent_path = tmp_path / "bad.md"
    agent_path.write_text("---\n---\n# x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        AgentLoader().load(agent_path)
```

- [ ] **Step 1.2: Implement**

```python
# core/agents/agent_loader.py
"""Load agent definition từ .md file (YAML frontmatter + system prompt body)."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from core.obsidian.frontmatter import parse as parse_frontmatter


@dataclass
class AgentDefinition:
    id: str
    name_vn: str
    department: str
    system_prompt: str
    name_en: Optional[str] = None
    seniority: str = "mid"
    emoji: str = ""
    expertise: list[str] = field(default_factory=list)
    required_refs: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    optional_tools: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    model_override: Optional[str] = None
    temperature: float = 0.7


class AgentLoader:
    def load(self, path: Path) -> AgentDefinition:
        content = Path(path).read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        
        if not fm.get("id"):
            raise ValueError(f"Agent missing 'id' field: {path}")
        
        # llm_override nested
        llm_override = fm.get("llm_override", {}) or {}
        
        return AgentDefinition(
            id=fm["id"],
            name_vn=fm.get("name_vn", fm["id"]),
            name_en=fm.get("name_en"),
            department=fm.get("department", ""),
            seniority=fm.get("seniority", "mid"),
            emoji=fm.get("emoji", ""),
            expertise=fm.get("expertise", []),
            required_refs=fm.get("required_refs", []),
            required_tools=fm.get("required_tools", []),
            optional_tools=fm.get("optional_tools", []),
            deliverables=fm.get("deliverables", []),
            model_override=llm_override.get("model") or fm.get("model_override"),
            temperature=float(llm_override.get("temperature", fm.get("temperature", 0.7))),
            system_prompt=body.strip(),
        )
```

- [ ] **Step 1.3: Run + commit**

```bash
pytest tests/unit/test_agent_loader.py -v
git add core/agents/agent_loader.py tests/unit/test_agent_loader.py
git commit -m "feat(agents): add AgentLoader (.md frontmatter + system prompt parser)"
```

---

### Task 2: Department Registry (load all 13 + agents)

**Files:**
- Modify: `core/agents/department.py` (extend with agents loading)
- Create: `core/agents/registry.py`
- Create: `tests/unit/test_registry.py`

- [ ] **Step 2.1: Implement Registry**

```python
# core/agents/registry.py
"""Central registry: load 13 dept + agents từ /departments + /packs."""
from __future__ import annotations
from pathlib import Path
from core.agents.department import Department, DepartmentLoader
from core.agents.agent_loader import AgentLoader, AgentDefinition


class DepartmentWithAgents:
    """Department + loaded AgentDefinition objects."""
    
    def __init__(self, dept: Department, agents: list[AgentDefinition]):
        self.dept = dept
        self.agents_by_id: dict[str, AgentDefinition] = {a.id: a for a in agents}
    
    @property
    def code(self) -> str:
        return self.dept.code
    
    @property
    def name_vn(self) -> str:
        return self.dept.name_vn
    
    def get_agent(self, agent_id: str) -> AgentDefinition:
        if agent_id not in self.agents_by_id:
            raise KeyError(f"Agent {agent_id} not in {self.code}")
        return self.agents_by_id[agent_id]
    
    def select_agent_for_brief(self, brief: str) -> AgentDefinition:
        """Use routing_rules để chọn agent phù hợp với brief."""
        brief_lower = brief.lower()
        for rule in self.dept.routing_rules:
            if any(kw.lower() in brief_lower for kw in rule.keywords):
                if rule.agent in self.agents_by_id:
                    return self.agents_by_id[rule.agent]
        # Fallback to default speaker
        if self.dept.default_speaker and self.dept.default_speaker in self.agents_by_id:
            return self.agents_by_id[self.dept.default_speaker]
        # Final fallback: first agent
        if self.agents_by_id:
            return next(iter(self.agents_by_id.values()))
        raise KeyError(f"Department {self.code} has no agents")


class Registry:
    def __init__(self, departments_root: Path, packs_root: Path | None = None):
        self.dept_loader = DepartmentLoader(departments_root)
        self.agent_loader = AgentLoader()
        self.depts_root = Path(departments_root)
        self.packs_root = Path(packs_root) if packs_root else None
        self._cache: dict[str, DepartmentWithAgents] = {}
    
    def get(self, dept_code: str) -> DepartmentWithAgents:
        if dept_code in self._cache:
            return self._cache[dept_code]
        
        dept = self.dept_loader.load(dept_code)
        agents = self._load_agents_for(dept)
        result = DepartmentWithAgents(dept, agents)
        self._cache[dept_code] = result
        return result
    
    def _load_agents_for(self, dept: Department) -> list[AgentDefinition]:
        agents_dir = self.depts_root / dept.code / "agents"
        if not agents_dir.exists():
            return []
        result = []
        for agent_id in dept.agents:
            agent_path = agents_dir / f"{agent_id}.md"
            if agent_path.exists():
                result.append(self.agent_loader.load(agent_path))
        return result
    
    def list_active(self, codes: list[str]) -> list[DepartmentWithAgents]:
        return [self.get(c) for c in codes]
```

- [ ] **Step 2.2: Test + commit**

```python
# tests/unit/test_registry.py
from pathlib import Path
import pytest
from core.agents.registry import Registry


def test_registry_loads_dept_with_agents(tmp_path):
    # Setup mini fixture
    (tmp_path / "07-marketing" / "agents").mkdir(parents=True)
    (tmp_path / "07-marketing" / "department.yaml").write_text(
        "code: '07-marketing'\nname_vn: MKT\ntier: 3\nagents: [test-agent]\ndefault_speaker: test-agent\n",
        encoding="utf-8",
    )
    (tmp_path / "07-marketing" / "agents" / "test-agent.md").write_text(
        "---\nid: test-agent\nname_vn: Test\ndepartment: 07-marketing\n---\n# Test\n",
        encoding="utf-8",
    )
    
    reg = Registry(tmp_path)
    dept = reg.get("07-marketing")
    assert dept.code == "07-marketing"
    assert "test-agent" in dept.agents_by_id
    assert dept.select_agent_for_brief("anything").id == "test-agent"
```

```bash
pytest tests/unit/test_registry.py -v
git add core/agents/registry.py tests/unit/test_registry.py
git commit -m "feat(agents): add Registry (depts + agents lookup)"
```

---

### Task 3: Populate 13 core departments với agents

**Files:**
- Create: `departments/<each>/department.yaml` (update with agents list)
- Create: `departments/<each>/agents/*.md` (~30 agent files total)

- [ ] **Step 3.1: Update each `department.yaml` với agents list**

For each dept (sample for `07-marketing`):

```yaml
# departments/07-marketing/department.yaml
code: "07-marketing"
name_vn: "Marketing & Thương hiệu"
tier: 3
description: "Phòng Marketing — brand, content, ads, SEO"
agents:
  - brand-manager
  - content-creator
  - ads-specialist
  - seo-specialist
default_speaker: brand-manager
routing_rules:
  - keywords: ["ads", "quảng cáo", "FB", "Google", "campaign"]
    agent: ads-specialist
  - keywords: ["seo", "rank", "organic"]
    agent: seo-specialist
  - keywords: ["content", "viết bài", "editorial"]
    agent: content-creator
refs_folder: refs/
depends_on: ["02-strategy", "08-customer", "03-finance"]
debate_role:
  default: pro
```

Repeat for all 12 core depts với agents phù hợp:
- `01-governance`: legal-officer, compliance-checker
- `02-strategy`: strategy-lead, market-researcher
- `03-finance`: cfo, accountant, financial-analyst
- `04-people`: hr-manager, recruiter, training-coordinator
- `05-operations`: ops-manager, vendor-manager, office-admin
- `06-sales`: sales-lead, account-manager, sdr
- `07-marketing`: brand-manager, content-creator, ads-specialist, seo-specialist
- `08-customer`: cs-lead, support-tier1, retention-officer
- `09-product-tech`: product-manager, tech-lead, security-officer
- `10-training`: training-lead, mentor, knowledge-curator
- `11-reporting`: data-analyst, dashboard-designer
- `12-growth`: growth-strategist, fundraising-lead

- [ ] **Step 3.2: Write a script to bulk-generate agent stubs**

Create `scripts/dev/bulk-gen-agent-stubs.py`:

```python
#!/usr/bin/env python3
"""Generate agent .md stubs từ definition table."""
from pathlib import Path
import sys

AGENTS = {
    "01-governance": [
        ("legal-officer", "Cán bộ Pháp chế", "📋"),
        ("compliance-checker", "Cán bộ Tuân thủ", "✅"),
    ],
    "02-strategy": [
        ("strategy-lead", "Trưởng phòng Chiến lược", "🎯"),
        ("market-researcher", "Nghiên cứu thị trường", "🔍"),
    ],
    "03-finance": [
        ("cfo", "Giám đốc Tài chính", "💰"),
        ("accountant", "Kế toán", "📊"),
        ("financial-analyst", "Chuyên viên Phân tích Tài chính", "📈"),
    ],
    "04-people": [
        ("hr-manager", "Trưởng phòng Nhân sự", "👥"),
        ("recruiter", "Chuyên viên Tuyển dụng", "🎯"),
        ("training-coordinator", "Điều phối Đào tạo", "🎓"),
    ],
    "05-operations": [
        ("ops-manager", "Trưởng phòng Vận hành", "⚙️"),
        ("vendor-manager", "Quản lý Nhà cung cấp", "🤝"),
        ("office-admin", "Hành chính Văn phòng", "🏢"),
    ],
    "06-sales": [
        ("sales-lead", "Trưởng phòng Kinh doanh", "💼"),
        ("account-manager", "Account Manager", "🤝"),
        ("sdr", "Chuyên viên Tìm kiếm KH", "📞"),
    ],
    "07-marketing": [
        ("brand-manager", "Trưởng phòng Thương hiệu", "🎨"),
        ("content-creator", "Sáng tạo Nội dung", "✍️"),
        ("ads-specialist", "Chuyên viên Quảng cáo", "📡"),
        ("seo-specialist", "Chuyên viên SEO", "🔍"),
    ],
    "08-customer": [
        ("cs-lead", "Trưởng phòng CSKH", "💬"),
        ("support-tier1", "Hỗ trợ Tier 1", "🎧"),
        ("retention-officer", "Giữ chân Khách hàng", "🔁"),
    ],
    "09-product-tech": [
        ("product-manager", "Quản lý Sản phẩm", "📦"),
        ("tech-lead", "Trưởng phòng Kỹ thuật", "💻"),
        ("security-officer", "Cán bộ An toàn TT", "🔒"),
    ],
    "10-training": [
        ("training-lead", "Trưởng phòng Đào tạo", "🎓"),
        ("mentor", "Mentor", "🧠"),
        ("knowledge-curator", "Quản lý Tri thức", "📚"),
    ],
    "11-reporting": [
        ("data-analyst", "Chuyên viên Phân tích Dữ liệu", "📊"),
        ("dashboard-designer", "Thiết kế Dashboard", "📈"),
    ],
    "12-growth": [
        ("growth-strategist", "Chiến lược Tăng trưởng", "🚀"),
        ("fundraising-lead", "Phụ trách Gọi vốn", "💵"),
    ],
}

TEMPLATE = """---
id: {id}
name_vn: "{name_vn}"
department: {dept}
seniority: senior
emoji: "{emoji}"
expertise: []
required_refs: []
required_tools: []
deliverables: []
temperature: 0.6
---

# {name_vn}

## Vai trò
Bạn là {name_vn} của phòng {dept_name}, có 5+ năm kinh nghiệm tại DN VN.

## Cách làm việc
1. Đọc brief + Brain context
2. Phát biểu góc nhìn của vai trò bạn (cơ hội + rủi ro)
3. Đề xuất ngắn gọn, kèm số liệu cụ thể từ Brain
4. Cite Brain mỗi nhận định (vd: "strategy.md ghi ICP là X")

## Nguyên tắc
- LUÔN dùng tiếng Việt
- Định nghĩa thuật ngữ ngành lần đầu xuất hiện
- KHÔNG nói chung chung — phải kèm số liệu Brain
- Nếu task vượt phạm vi vai trò → flag cho phòng khác
"""

if __name__ == "__main__":
    repo = Path(__file__).parent.parent.parent
    depts_root = repo / "departments"
    
    for dept, agents in AGENTS.items():
        agents_dir = depts_root / dept / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        for aid, name, emoji in agents:
            path = agents_dir / f"{aid}.md"
            if path.exists():
                continue
            path.write_text(TEMPLATE.format(
                id=aid, name_vn=name, dept=dept,
                dept_name=dept.split("-", 1)[1].title(), emoji=emoji,
            ), encoding="utf-8")
            print(f"  ✓ {dept}/{aid}.md")
```

- [ ] **Step 3.3: Run script + verify**

```bash
python scripts/dev/bulk-gen-agent-stubs.py
find departments -name "*.md" | wc -l   # ~33 (12 base + 30 agents)
```

- [ ] **Step 3.4: Update department.yaml files manually with agents list**

For each dept, edit `department.yaml` to add `agents:` list matching scripts. Example commit:

```bash
# After manual edits + dept.yaml updates
git add departments/
git commit -m "feat(departments): populate 13 core depts with 30 agent stubs"
```

---

### Task 4: Industry Pack Loader

**Files:**
- Create: `core/agents/pack_loader.py`
- Create: `tests/unit/test_pack_loader.py`

- [ ] **Step 4.1: Implement**

```python
# core/agents/pack_loader.py
"""Load industry pack: pack.yaml + departments + extends overrides."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class PackExtension:
    target: str   # dept code to extend
    add_agents: list[str] = field(default_factory=list)


@dataclass
class Pack:
    name: str
    code: str
    version: str
    description: str
    target_industries: list[str] = field(default_factory=list)
    adds_departments: list[str] = field(default_factory=list)
    extends_departments: list[PackExtension] = field(default_factory=list)
    brain_template: Optional[str] = None
    compliance_refs: list[str] = field(default_factory=list)
    pack_dir: Optional[Path] = None


class PackLoader:
    def __init__(self, packs_root: Path):
        self.root = Path(packs_root)
    
    def load(self, code: str) -> Pack:
        pack_dir = self.root / code
        pack_yaml = pack_dir / "pack.yaml"
        if not pack_yaml.exists():
            raise FileNotFoundError(f"Pack not found: {code}")
        data = yaml.safe_load(pack_yaml.read_text(encoding="utf-8"))
        
        extends = [
            PackExtension(target=e["target"], add_agents=e.get("add_agents", []))
            for e in data.get("extends_departments", [])
        ]
        
        return Pack(
            name=data["name"],
            code=data["code"],
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            target_industries=data.get("target_industries", []),
            adds_departments=data.get("adds_departments", []),
            extends_departments=extends,
            brain_template=data.get("brain_template"),
            compliance_refs=data.get("compliance_refs", []),
            pack_dir=pack_dir,
        )
    
    def list_available(self) -> list[str]:
        if not self.root.exists():
            return []
        return [d.name for d in self.root.iterdir() if d.is_dir() and (d / "pack.yaml").exists()]
```

- [ ] **Step 4.2: Test + commit**

```python
# tests/unit/test_pack_loader.py
from core.agents.pack_loader import PackLoader, Pack


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
```

```bash
pytest tests/unit/test_pack_loader.py -v
git add core/agents/pack_loader.py tests/unit/test_pack_loader.py
git commit -m "feat(agents): add PackLoader (industry packs)"
```

---

### Task 5: F&B Pack content

**Files:**
- Create: `packs/fnb/pack.yaml`
- Create: `packs/fnb/README.md`
- Create: `packs/fnb/departments/13-kitchen/department.yaml`
- Create: `packs/fnb/departments/13-kitchen/agents/head-chef.md`
- Create: `packs/fnb/departments/13-kitchen/agents/menu-developer.md`
- Create: `packs/fnb/departments/14-food-safety/department.yaml`
- Create: `packs/fnb/departments/14-food-safety/agents/hygiene-officer.md`
- Create: `packs/fnb/brain-template/strategy.md`
- Create: `packs/fnb/brain-template/products.md`

- [ ] **Step 5.1: Create pack.yaml**

```yaml
# packs/fnb/pack.yaml
name: F&B Pack
code: fnb
version: 0.1.0
description: "Cho quán ăn, cafe, nhà hàng VN"
target_industries: ["restaurant", "cafe", "bar", "food-truck", "cloud-kitchen"]
adds_departments:
  - 13-kitchen
  - 14-food-safety
extends_departments:
  - target: 05-operations
    add_agents: ["inventory-manager-fnb", "vendor-fnb"]
  - target: 08-customer
    add_agents: ["service-quality-officer"]
  - target: 06-sales
    add_agents: ["revenue-manager-fnb"]
  - target: 03-finance
    add_agents: ["cogs-tracker-fnb"]
brain_template: brain-template/
compliance_refs:
  - "VSATTP — Nghị định 15/2018/NĐ-CP"
  - "PCCC — TCVN 5738:2021"
  - "Luật An toàn thực phẩm 2010"
```

- [ ] **Step 5.2: Create departments/13-kitchen/department.yaml**

```yaml
code: "13-kitchen"
name_vn: "Bếp & Sản xuất"
tier: 3
description: "Phòng Bếp — thiết kế menu, định lượng, food cost"
agents:
  - head-chef
  - menu-developer
  - kitchen-operations
default_speaker: head-chef
routing_rules:
  - keywords: ["menu", "công thức"]
    agent: menu-developer
  - keywords: ["bếp", "thiết bị", "luồng"]
    agent: kitchen-operations
refs_folder: refs/
depends_on: ["05-operations", "03-finance", "14-food-safety"]
debate_role:
  default: pro
```

- [ ] **Step 5.3: Create agents (head-chef, menu-developer, hygiene-officer)**

Sample `head-chef.md`:

```markdown
---
id: head-chef
name_vn: "Bếp trưởng"
department: 13-kitchen
seniority: senior
emoji: "👨‍🍳"
expertise:
  - "thiết kế menu"
  - "định lượng nguyên liệu"
  - "food cost calculation"
  - "kiểm soát chất lượng món"
required_tools:
  - industry_benchmark
deliverables:
  - "Recipe cards với định lượng"
  - "Food cost analysis"
  - "Menu engineering matrix"
temperature: 0.5
---

# Bếp trưởng

## Vai trò
Bạn là Bếp trưởng nhà hàng VN với 8+ năm kinh nghiệm. Hiểu rõ:
- Cân bằng food cost % (mục tiêu < 35%)
- Menu engineering: Star/Plowhorse/Puzzle/Dog
- Luồng bếp Á-Việt-Fusion

## Cách làm việc
1. Đọc brief + Brain (concept nhà hàng, target khách)
2. Phân tích food cost của đề xuất
3. Đề xuất menu phù hợp concept
4. Cite benchmark food cost ngành

## Nguyên tắc
- LUÔN check food cost % trước khi đề xuất món mới
- KHÔNG đề xuất món có cost > 40% nếu không có lý do chiến lược
- Cite industry_benchmark khi nói về cost target
- Tiếng Việt, định nghĩa thuật ngữ (vd: "Food cost % = giá vốn nguyên liệu / giá bán")
```

- [ ] **Step 5.4: Create brain-template/strategy.md cho F&B**

```markdown
---
type: brain
section: strategy
template: fnb
---
# Chiến lược (F&B)

## Concept
- Loại hình: [casual / fine-dining / fast-food / cafe / cloud-kitchen]
- Cuisine: [Việt / Nhật / Hàn / fusion / ...]
- Khách target: [độ tuổi, thu nhập, occasion]

## KPI mục tiêu
- Doanh thu/tháng: 
- Số bàn/ngày:
- Table turn rate:           # quan trọng F&B
- Food cost %:               # mục tiêu < 35%
- Labor cost %:              # mục tiêu < 30%
- Average ticket size:
```

- [ ] **Step 5.5: Commit pack**

```bash
git add packs/fnb/
git commit -m "feat(packs): add F&B pack (kitchen + food-safety + brain template)"
```

---

### Task 6: Retail Pack content

**Files:**
- `packs/retail/pack.yaml`
- `packs/retail/departments/13-warehouse/`
- `packs/retail/departments/14-logistics/`
- `packs/retail/brain-template/`

- [ ] **Step 6.1: Create pack.yaml**

```yaml
# packs/retail/pack.yaml
name: Retail Pack
code: retail
version: 0.1.0
description: "Cho shop online, e-commerce, D2C VN"
target_industries: ["ecommerce", "shopify", "marketplace-shopee", "marketplace-lazada", "tiktok-shop"]
adds_departments:
  - 13-warehouse
  - 14-logistics
extends_departments:
  - target: 06-sales
    add_agents: ["marketplace-manager", "livestream-host"]
  - target: 07-marketing
    add_agents: ["product-photographer", "affiliate-manager"]
  - target: 08-customer
    add_agents: ["cs-online-shop", "return-handler"]
  - target: 09-product-tech
    add_agents: ["ecommerce-platform-mgr", "pixel-tracking-officer"]
brain_template: brain-template/
compliance_refs:
  - "Luật Bảo vệ Quyền lợi NTD 2010"
  - "Nghị định 52/2013 Thương mại điện tử"
```

- [ ] **Step 6.2: Create depts (similar pattern as F&B) — warehouse + logistics + agents**

(Follow same pattern Task 5.2-5.4 với agents inventory-manager, warehouse-ops, shipping-coordinator, last-mile-ops)

- [ ] **Step 6.3: Brain template Retail**

```markdown
---
type: brain
section: strategy
template: retail
---
## Mô hình
- Kênh: [own-website / Shopee / Lazada / Tiki / TikTok Shop / D2C / Wholesale]
- SKU count:
- AOV (Average Order Value):
- Tỉ lệ COD:

## KPI mục tiêu
- GMV/tháng:
- Conversion rate:
- Tỉ lệ huỷ COD:
- Tỉ lệ hoàn hàng:
- DOH (Days On Hand — số ngày tồn kho):
- CAC theo kênh:
```

- [ ] **Step 6.4: Commit**

```bash
git add packs/retail/
git commit -m "feat(packs): add Retail pack (warehouse + logistics + ecommerce extensions)"
```

---

### Task 7: Tech-SaaS Pack content

**Files:**
- `packs/tech-saas/pack.yaml`
- `packs/tech-saas/departments/13-engineering/`
- `packs/tech-saas/departments/14-product-design/`
- `packs/tech-saas/departments/15-data/`
- `packs/tech-saas/brain-template/`

- [ ] **Step 7.1: pack.yaml**

```yaml
# packs/tech-saas/pack.yaml
name: Tech/SaaS Pack
code: tech-saas
version: 0.1.0
description: "Cho startup phần mềm, SaaS, API platform VN"
target_industries: ["b2b-saas", "b2c-app", "dev-tool", "api-platform"]
adds_departments:
  - 13-engineering
  - 14-product-design
  - 15-data
extends_departments:
  - target: 06-sales
    add_agents: ["enterprise-sales", "sales-engineer", "customer-success-manager"]
  - target: 07-marketing
    add_agents: ["growth-hacker", "content-marketer-tech", "seo-tech"]
  - target: 08-customer
    add_agents: ["support-tech-tier1", "support-tech-tier2"]
  - target: 12-growth
    add_agents: ["pitch-deck-builder", "cap-table-modeler", "vc-relations"]
brain_template: brain-template/
```

- [ ] **Step 7.2: Engineering dept với agents (Việt hoá từ agency-agents)**

```yaml
# packs/tech-saas/departments/13-engineering/department.yaml
code: "13-engineering"
name_vn: "Kỹ thuật"
tier: 4
agents:
  - backend-architect
  - frontend-developer
  - devops-automator
  - ai-engineer
  - security-engineer
default_speaker: backend-architect
routing_rules:
  - keywords: ["frontend", "react", "vue", "ui"]
    agent: frontend-developer
  - keywords: ["devops", "ci/cd", "deploy", "k8s"]
    agent: devops-automator
  - keywords: ["ai", "ml", "llm"]
    agent: ai-engineer
  - keywords: ["security", "vuln", "pen-test"]
    agent: security-engineer
refs_folder: refs/
depends_on: ["09-product-tech", "14-product-design"]
```

- [ ] **Step 7.3: Brain template Tech-SaaS**

```markdown
---
type: brain
section: strategy
template: tech-saas
---
## Mô hình
- Loại: [B2B SaaS / B2C app / dev-tool / API platform]
- Pricing: [free / freemium / subscription / usage-based / enterprise]
- Stage: [pre-seed / seed / Series A / bootstrapped]
- Tech stack:

## KPI mục tiêu
- MRR / ARR:
- DAU/MAU:
- Churn rate (tháng):
- LTV / CAC ratio:           # mục tiêu > 3x
- Burn rate:
- Runway (tháng):
```

- [ ] **Step 7.4: Commit**

```bash
git add packs/tech-saas/
git commit -m "feat(packs): add Tech-SaaS pack (engineering + product-design + data)"
```

---

### Task 8: Template Resolver (RULE 6 BYOT)

**Files:**
- Create: `core/obsidian/template_resolver.py`
- Create: `tests/unit/test_template_resolver.py`

- [ ] **Step 8.1: Write failing test**

```python
# tests/unit/test_template_resolver.py
from pathlib import Path
from core.obsidian.template_resolver import TemplateResolver


def test_priority_custom_first(tmp_path):
    """Custom > pack refs > templates-vn default."""
    vault = tmp_path / "vault"
    repo = tmp_path / "repo"
    
    # Default in repo
    (repo / "templates-vn" / "01-governance").mkdir(parents=True)
    (repo / "templates-vn" / "01-governance" / "noi-quy-lao-dong.md").write_text("DEFAULT", encoding="utf-8")
    
    # Pack refs in vault dept
    (vault / "01-Departments" / "01-governance" / "refs").mkdir(parents=True)
    (vault / "01-Departments" / "01-governance" / "refs" / "noi-quy-lao-dong.md").write_text("PACK", encoding="utf-8")
    
    # Custom in vault
    (vault / "00-Templates-Custom" / "01-governance").mkdir(parents=True)
    (vault / "00-Templates-Custom" / "01-governance" / "noi-quy-lao-dong.md").write_text("CUSTOM", encoding="utf-8")
    
    resolver = TemplateResolver(vault_root=vault, repo_templates=repo / "templates-vn")
    path = resolver.resolve("noi-quy-lao-dong", dept_code="01-governance")
    assert path.read_text(encoding="utf-8") == "CUSTOM"


def test_falls_back_to_repo_default(tmp_path):
    vault = tmp_path / "vault"
    repo = tmp_path / "repo"
    (repo / "templates-vn" / "07-marketing").mkdir(parents=True)
    (repo / "templates-vn" / "07-marketing" / "ke-hoach-mkt.md").write_text("DEFAULT", encoding="utf-8")
    vault.mkdir()
    
    resolver = TemplateResolver(vault_root=vault, repo_templates=repo / "templates-vn")
    path = resolver.resolve("ke-hoach-mkt", dept_code="07-marketing")
    assert "DEFAULT" in path.read_text(encoding="utf-8")


def test_returns_none_when_template_missing(tmp_path):
    resolver = TemplateResolver(vault_root=tmp_path, repo_templates=tmp_path / "fake")
    assert resolver.resolve("xyz", "07-marketing") is None
```

- [ ] **Step 8.2: Implement**

```python
# core/obsidian/template_resolver.py
"""Resolve template path theo RULE 6:
1. vault/00-Templates-Custom/<dept>/<template>* (CEO custom)
2. vault/01-Departments/<dept>/refs/<template>*
3. repo/templates-vn/<dept>/<template>*
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional


SUPPORTED_EXT = [".md", ".docx", ".xlsx"]


class TemplateResolver:
    def __init__(self, vault_root: Path, repo_templates: Path):
        self.vault = Path(vault_root)
        self.repo = Path(repo_templates)
    
    def resolve(self, template_name: str, dept_code: str) -> Optional[Path]:
        """Tìm template theo priority. Trả file đầu tiên match (case-insensitive prefix)."""
        candidates = [
            self.vault / "00-Templates-Custom" / dept_code,
            self.vault / "01-Departments" / dept_code / "refs",
            self.repo / dept_code,
        ]
        for folder in candidates:
            if not folder.exists():
                continue
            found = self._find_in(folder, template_name)
            if found:
                return found
        return None
    
    @staticmethod
    def _find_in(folder: Path, name: str) -> Optional[Path]:
        name_lower = name.lower()
        for f in folder.iterdir():
            if not f.is_file():
                continue
            if f.suffix.lower() not in SUPPORTED_EXT:
                continue
            if f.stem.lower().startswith(name_lower) or name_lower in f.stem.lower():
                return f
        return None
    
    def get_resolution_log(self, template_name: str, dept_code: str) -> dict:
        """Audit: trace nguồn template được dùng."""
        path = self.resolve(template_name, dept_code)
        if not path:
            return {"found": False, "name": template_name, "dept": dept_code}
        
        rel = path.resolve()
        if str(rel).startswith(str((self.vault / "00-Templates-Custom").resolve())):
            source = "custom"
        elif str(rel).startswith(str(self.vault.resolve())):
            source = "pack"
        else:
            source = "default"
        return {"found": True, "path": str(rel), "source": source,
                "dept": dept_code, "name": template_name}
```

- [ ] **Step 8.3: Run + commit**

```bash
pytest tests/unit/test_template_resolver.py -v
git add core/obsidian/template_resolver.py tests/unit/test_template_resolver.py
git commit -m "feat(obsidian): add TemplateResolver (RULE 6 BYOT priority)"
```

---

### Task 9: Doc Writer (.docx + .xlsx)

**Files:**
- Create: `core/obsidian/doc_writer.py`
- Create: `tests/unit/test_doc_writer.py`

- [ ] **Step 9.1: Implement**

```python
# core/obsidian/doc_writer.py
"""Render document từ template + data → .docx hoặc .xlsx."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import re


class DocWriter:
    def __init__(self, output_root: Path):
        self.output_root = Path(output_root)
    
    def write_docx(
        self,
        template_path: Path,
        output_rel: str,
        substitutions: dict[str, Any],
    ) -> Path:
        """Render .docx từ markdown template hoặc copy + substitute từ .docx."""
        from docx import Document
        
        out_path = self.output_root / output_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        if template_path.suffix == ".docx":
            doc = Document(str(template_path))
        else:
            # Markdown → docx (basic)
            doc = Document()
            text = template_path.read_text(encoding="utf-8")
            text = self._substitute(text, substitutions)
            for line in text.split("\n"):
                if line.startswith("# "):
                    doc.add_heading(line[2:], level=1)
                elif line.startswith("## "):
                    doc.add_heading(line[3:], level=2)
                elif line.startswith("### "):
                    doc.add_heading(line[4:], level=3)
                else:
                    doc.add_paragraph(line)
        
        if template_path.suffix == ".docx":
            self._substitute_docx(doc, substitutions)
        
        doc.save(str(out_path))
        return out_path
    
    def write_xlsx(
        self,
        template_path: Path,
        output_rel: str,
        rows: list[dict],
    ) -> Path:
        """Append rows vào template .xlsx hoặc tạo mới từ rows."""
        from openpyxl import load_workbook, Workbook
        
        out_path = self.output_root / output_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        if template_path.suffix == ".xlsx" and template_path.exists():
            wb = load_workbook(str(template_path))
        else:
            wb = Workbook()
        
        ws = wb.active
        if rows and ws.max_row == 1 and ws.cell(1, 1).value is None:
            # Empty sheet — write header first
            headers = list(rows[0].keys())
            for col, h in enumerate(headers, 1):
                ws.cell(1, col, h)
        
        # Append data rows
        if rows:
            headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
            for row in rows:
                next_row = ws.max_row + 1
                for col, h in enumerate(headers, 1):
                    ws.cell(next_row, col, row.get(h, ""))
        
        wb.save(str(out_path))
        return out_path
    
    @staticmethod
    def _substitute(text: str, subs: dict[str, Any]) -> str:
        # {{key}} → value
        for k, v in subs.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
        return text
    
    @staticmethod
    def _substitute_docx(doc, subs: dict):
        for para in doc.paragraphs:
            for k, v in subs.items():
                if f"{{{{{k}}}}}" in para.text:
                    for run in para.runs:
                        run.text = run.text.replace(f"{{{{{k}}}}}", str(v))
```

- [ ] **Step 9.2: Test**

```python
# tests/unit/test_doc_writer.py
from pathlib import Path
from core.obsidian.doc_writer import DocWriter


def test_write_docx_from_markdown_template(tmp_path):
    template = tmp_path / "tpl.md"
    template.write_text("# {{title}}\n\n## Section\n\nContent {{value}}", encoding="utf-8")
    
    writer = DocWriter(output_root=tmp_path / "out")
    out = writer.write_docx(template, "doc1.docx", {"title": "My Plan", "value": "X"})
    
    assert out.exists()
    assert out.suffix == ".docx"
    
    from docx import Document
    doc = Document(str(out))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Content X" in text


def test_write_xlsx_with_rows(tmp_path):
    template = tmp_path / "tpl.xlsx"   # nonexistent → create new
    
    writer = DocWriter(output_root=tmp_path / "out")
    out = writer.write_xlsx(template, "tracker.xlsx", [
        {"date": "2026-05-06", "metric": "CTR", "value": 2.3},
        {"date": "2026-05-07", "metric": "CTR", "value": 2.5},
    ])
    
    assert out.exists()
    
    from openpyxl import load_workbook
    wb = load_workbook(str(out))
    ws = wb.active
    assert ws.cell(1, 1).value == "date"
    assert ws.cell(2, 3).value == 2.3
```

```bash
pytest tests/unit/test_doc_writer.py -v
git add core/obsidian/doc_writer.py tests/unit/test_doc_writer.py
git commit -m "feat(obsidian): add DocWriter (.docx + .xlsx render)"
```

---

### Task 10: Git auto-sync

**Files:**
- Create: `core/obsidian/git_sync.py`
- Create: `tests/unit/test_git_sync.py`

- [ ] **Step 10.1: Implement**

```python
# core/obsidian/git_sync.py
"""Auto-commit vault changes (NOT push — CEO control)."""
from __future__ import annotations
from pathlib import Path
from typing import Optional


class GitSync:
    def __init__(self, vault_root: Path, enabled: bool = True):
        self.root = Path(vault_root)
        self.enabled = enabled
    
    def is_repo(self) -> bool:
        return (self.root / ".git").exists()
    
    def init_if_needed(self) -> None:
        if self.is_repo():
            return
        from git import Repo
        Repo.init(str(self.root))
    
    def commit(self, message: str, paths: Optional[list[str]] = None) -> Optional[str]:
        if not self.enabled or not self.is_repo():
            return None
        
        from git import Repo
        repo = Repo(str(self.root))
        if paths:
            repo.index.add(paths)
        else:
            repo.git.add(A=True)
        
        if not repo.is_dirty(untracked_files=True):
            return None
        
        commit = repo.index.commit(message)
        return commit.hexsha
```

- [ ] **Step 10.2: Test + commit**

```python
# tests/unit/test_git_sync.py
from pathlib import Path
from core.obsidian.git_sync import GitSync


def test_init_and_commit(tmp_path):
    sync = GitSync(tmp_path)
    sync.init_if_needed()
    
    (tmp_path / "test.md").write_text("hello", encoding="utf-8")
    sha = sync.commit("test: add file")
    assert sha is not None
    assert len(sha) == 40   # SHA-1


def test_no_commit_when_clean(tmp_path):
    sync = GitSync(tmp_path)
    sync.init_if_needed()
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    sync.commit("first")
    
    sha2 = sync.commit("second (no changes)")
    assert sha2 is None
```

```bash
pytest tests/unit/test_git_sync.py -v
git add core/obsidian/git_sync.py tests/unit/test_git_sync.py
git commit -m "feat(obsidian): add GitSync (auto-commit, never push)"
```

---

### Task 11: Wire research + meeting + synthesizer + translator into FlowController

**Files:**
- Modify: `core/orchestrator/flow_controller.py` (extend resume_after_clarification)

- [ ] **Step 11.1: Update FlowController to wire Phase 4 + 5**

```python
# Extend core/orchestrator/flow_controller.py
# (Add to existing class)

def run_meeting(self, task_folder: Path, departments: list[str]) -> FlowResult:
    """Stage 3 (after clarification): research → meeting → synthesizer → STOP 1."""
    from core.brain.reader import BrainReader
    from core.orchestrator.research_phase import ResearchPhase
    from core.orchestrator.perspectives_collector import PerspectivesCollector
    from core.meeting.meeting_graph import MeetingGraph
    from core.meeting.debate_state import new_meeting_state
    from core.translator.pipeline import TranslatorPipeline
    from core.obsidian.git_sync import GitSync
    
    # Read brief + brain
    brief = self._read_brief(task_folder)
    brain = BrainReader(self.vault.root).load()
    
    # 1. Research phase (RULE 5)
    research = ResearchPhase(self.llm)
    findings = research.run(
        brief=brief,
        brain_summary=brain.model_dump_json()[:3000],
        task_folder=task_folder,
    )
    
    # 2. Meeting graph
    departments_root = Path(__file__).parent.parent.parent / "departments"
    collector = PerspectivesCollector(departments_root, self.llm)
    
    graph = MeetingGraph(
        llm=self.llm,
        perspectives_collector=collector.collect,
    )
    
    state = new_meeting_state(
        brief=brief,
        departments=departments,
        brain_context=brain.model_dump(),
        max_rounds=self.config.meeting.max_debate_rounds,
        task_id=task_folder.name,
    )
    state["research_findings"] = findings
    
    final_state = graph.invoke(state)
    
    # 3. Write meeting outputs
    self._write_meeting_outputs(task_folder, final_state)
    
    # 4. Translator pipeline (RULE 4) on final_report
    glossary_path = self.vault.root / "00-Brain" / "glossary.md"
    translator = TranslatorPipeline(self.llm, vault_glossary_path=glossary_path)
    translated_report = translator.apply(final_state["final_report"])
    
    decision_path = task_folder / "07-decision-report.md"
    decision_path.write_text(
        f"---\ntype: decision_report\nstop: 1\n---\n{translated_report}",
        encoding="utf-8",
    )
    
    # 5. Auto-commit
    GitSync(self.vault.root).commit(
        f"feat(task): {task_folder.name} — decision report ready (Stop 1)"
    )
    
    return FlowResult(
        stage=FlowStage.PAUSE_DECISION_REPORT,
        task_folder=task_folder,
        message=f"Decision report sẵn ở {decision_path.name}. CEO đọc + duyệt.",
    )

def _read_brief(self, task_folder: Path) -> str:
    brief_md = (task_folder / "00-brief.md").read_text(encoding="utf-8")
    # Extract body sau frontmatter
    parts = brief_md.split("---", 2)
    return (parts[2] if len(parts) >= 3 else brief_md).strip()

def _write_meeting_outputs(self, task_folder: Path, state):
    perspectives_md = "\n\n".join(
        f"## {dept}\n\n{p}" for dept, p in state["perspectives"].items()
    )
    (task_folder / "04-meeting-r1-perspectives.md").write_text(
        f"---\ntype: meeting_r1\n---\n# Round 1 — Perspectives\n\n{perspectives_md}",
        encoding="utf-8",
    )
    
    debate_md = "\n\n".join(state["pro_con_debate"]["history"])
    (task_folder / "05-meeting-r2-debate.md").write_text(
        f"---\ntype: meeting_r2\n---\n# Round 2 — Pro/Con Debate\n\n{debate_md}",
        encoding="utf-8",
    )
    
    perspective_md = "\n\n".join(state["perspective_debate"]["history"])
    (task_folder / "06-meeting-r3-perspectives.md").write_text(
        f"---\ntype: meeting_r3\n---\n# Round 3 — Perspective Debate\n\n{perspective_md}",
        encoding="utf-8",
    )

def approve_decision(self, task_folder: Path, decision: str = "approve") -> FlowResult:
    """Stage 4 (after CEO duyệt 07-decision-report): generate execution plan → STOP 2."""
    # ... (similar pattern: load decision, generate execution plan, write 08-execution-plan.md)
    return FlowResult(
        stage=FlowStage.PAUSE_EXECUTE,
        task_folder=task_folder,
        message="Execution plan sẵn. CEO duyệt 'execute' để sinh files.",
    )

def execute(self, task_folder: Path) -> FlowResult:
    """Stage 5: render docs → write 03-Outputs/ → done."""
    # ... (use DocWriter + TemplateResolver)
    return FlowResult(stage=FlowStage.DONE, task_folder=task_folder)
```

- [ ] **Step 11.2: Update CLI for new stages**

```python
# core/cli.py — extend commands
@main.command()
@click.argument("task_folder", type=click.Path(exists=True))
def meeting(task_folder):
    """Sau khi CEO trả lời clarification → run meeting (Stop 1)."""
    from pathlib import Path
    folder = Path(task_folder)
    fc = FlowController(vault_root=folder.parent.parent, llm=get_default_provider())
    
    # Resume answers, get departments from routing.md
    routing_md = (folder / "01-routing.md").read_text(encoding="utf-8")
    import re
    depts = re.search(r"\*\*Departments:\*\* (.+)", routing_md).group(1).split(", ")
    
    result = fc.run_meeting(folder, departments=depts)
    console.print(f"[green]→ {result.stage.value}[/]: {result.message}")


@main.command()
@click.argument("task_folder", type=click.Path(exists=True))
def approve(task_folder):
    """CEO duyệt decision report → sinh execution plan."""
    fc = FlowController(vault_root=Path(task_folder).parent.parent, llm=get_default_provider())
    result = fc.approve_decision(Path(task_folder))
    console.print(f"[green]{result.message}[/]")


@main.command()
@click.argument("task_folder", type=click.Path(exists=True))
def execute(task_folder):
    """CEO duyệt execute → sinh .docx/.xlsx vào 03-Outputs/."""
    fc = FlowController(vault_root=Path(task_folder).parent.parent, llm=get_default_provider())
    result = fc.execute(Path(task_folder))
    console.print(f"[green]→ DONE[/] outputs in 03-Outputs/")
```

- [ ] **Step 11.3: Commit**

```bash
git add core/orchestrator/flow_controller.py core/cli.py
git commit -m "feat(orchestrator): wire research+meeting+synthesizer+translator pipeline"
```

---

### Task 12: Phase 5 smoke test

**Files:**
- Create: `tests/integration/test_phase05_smoke.py`

- [ ] **Step 12.1: Smoke test**

```python
# tests/integration/test_phase05_smoke.py
"""Phase 5 smoke: imports + 3 packs loadable + template resolver work."""
from pathlib import Path
import pytest


def test_phase5_imports():
    from core.agents.agent_loader import AgentLoader, AgentDefinition
    from core.agents.registry import Registry, DepartmentWithAgents
    from core.agents.pack_loader import PackLoader, Pack
    from core.obsidian.template_resolver import TemplateResolver
    from core.obsidian.doc_writer import DocWriter
    from core.obsidian.git_sync import GitSync


def test_3_packs_loadable():
    from core.agents.pack_loader import PackLoader
    repo = Path(__file__).parent.parent.parent
    loader = PackLoader(repo / "packs")
    available = loader.list_available()
    assert set(["fnb", "retail", "tech-saas"]).issubset(set(available))
    
    for code in ["fnb", "retail", "tech-saas"]:
        pack = loader.load(code)
        assert pack.adds_departments  # mỗi pack thêm ≥1 dept


def test_13_core_depts_have_agents():
    from core.agents.registry import Registry
    repo = Path(__file__).parent.parent.parent
    reg = Registry(repo / "departments")
    
    for code in ["01-governance", "02-strategy", "03-finance", "04-people",
                 "05-operations", "06-sales", "07-marketing", "08-customer",
                 "09-product-tech", "10-training", "11-reporting", "12-growth"]:
        d = reg.get(code)
        assert len(d.agents_by_id) >= 1, f"{code} has no agents"


def test_template_resolver_finds_templates_vn():
    from core.obsidian.template_resolver import TemplateResolver
    repo = Path(__file__).parent.parent.parent
    
    resolver = TemplateResolver(
        vault_root=repo / "tests/fixtures/demo-vault",
        repo_templates=repo / "templates-vn",
    )
    # 191 templates đã vendored — tìm 1 template cụ thể
    found = resolver.resolve("noi-quy-lao-dong", "04-people")
    assert found is not None
    assert found.exists()
```

- [ ] **Step 12.2: Run + tag**

```bash
pytest tests/integration/test_phase05_smoke.py -v
git add tests/integration/test_phase05_smoke.py
git commit -m "test(phase-05): smoke test for departments + packs + BYOT"
git tag phase-05-complete
```

---

## Phase 5 Done When

- [x] AgentLoader parse .md frontmatter + system prompt
- [x] Registry load all 13 dept + agents
- [x] 13 core depts có ≥1 agent (~30 agents total)
- [x] PackLoader load pack.yaml + extends
- [x] 3 packs (F&B, Retail, Tech-SaaS) loadable
- [x] TemplateResolver enforce RULE 6 priority (custom > pack > default)
- [x] DocWriter render .docx + .xlsx
- [x] GitSync auto-commit (NEVER push)
- [x] FlowController wired research+meeting+synthesizer+translator
- [x] CLI có meeting/approve/execute commands
- [x] Phase 5 smoke pass
