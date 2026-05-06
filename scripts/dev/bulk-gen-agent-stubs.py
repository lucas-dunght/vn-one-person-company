#!/usr/bin/env python3
"""Generate agent .md stubs từ definition table và update department.yaml."""
from pathlib import Path
import yaml

AGENTS = {
    "01-governance": [
        ("legal-officer", "Cán bộ Pháp chế", ""),
        ("compliance-checker", "Cán bộ Tuân thủ", ""),
    ],
    "02-strategy": [
        ("strategy-lead", "Trưởng phòng Chiến lược", ""),
        ("market-researcher", "Nghiên cứu thị trường", ""),
    ],
    "03-finance": [
        ("cfo", "Giám đốc Tài chính", ""),
        ("accountant", "Kế toán", ""),
        ("financial-analyst", "Chuyên viên Phân tích Tài chính", ""),
    ],
    "04-people": [
        ("hr-manager", "Trưởng phòng Nhân sự", ""),
        ("recruiter", "Chuyên viên Tuyển dụng", ""),
        ("training-coordinator", "Điều phối Đào tạo", ""),
    ],
    "05-operations": [
        ("ops-manager", "Trưởng phòng Vận hành", ""),
        ("vendor-manager", "Quản lý Nhà cung cấp", ""),
        ("office-admin", "Hành chính Văn phòng", ""),
    ],
    "06-sales": [
        ("sales-lead", "Trưởng phòng Kinh doanh", ""),
        ("account-manager", "Account Manager", ""),
        ("sdr", "Chuyên viên Tìm kiếm KH", ""),
    ],
    "07-marketing": [
        ("brand-manager", "Trưởng phòng Thương hiệu", ""),
        ("content-creator", "Sáng tạo Nội dung", ""),
        ("ads-specialist", "Chuyên viên Quảng cáo", ""),
        ("seo-specialist", "Chuyên viên SEO", ""),
    ],
    "08-customer": [
        ("cs-lead", "Trưởng phòng CSKH", ""),
        ("support-tier1", "Hỗ trợ Tier 1", ""),
        ("retention-officer", "Giữ chân Khách hàng", ""),
    ],
    "09-product-tech": [
        ("product-manager", "Quản lý Sản phẩm", ""),
        ("tech-lead", "Trưởng phòng Kỹ thuật", ""),
        ("security-officer", "Cán bộ An toàn TT", ""),
    ],
    "10-training": [
        ("training-lead", "Trưởng phòng Đào tạo", ""),
        ("mentor", "Mentor", ""),
        ("knowledge-curator", "Quản lý Tri thức", ""),
    ],
    "11-reporting": [
        ("data-analyst", "Chuyên viên Phân tích Dữ liệu", ""),
        ("dashboard-designer", "Thiết kế Dashboard", ""),
    ],
    "12-growth": [
        ("growth-strategist", "Chiến lược Tăng trưởng", ""),
        ("fundraising-lead", "Phụ trách Gọi vốn", ""),
    ],
}

DEPT_NAMES_VN = {
    "01-governance": "Quản trị & Pháp lý",
    "02-strategy": "Chiến lược & Kế hoạch",
    "03-finance": "Tài chính & Kế toán",
    "04-people": "Nhân sự & Con người",
    "05-operations": "Hành chính & Vận hành",
    "06-sales": "Kinh doanh & Bán hàng",
    "07-marketing": "Marketing & Thương hiệu",
    "08-customer": "Khách hàng & Dịch vụ",
    "09-product-tech": "Sản phẩm & Công nghệ",
    "10-training": "Đào tạo & Phát triển",
    "11-reporting": "Báo cáo & Đo lường",
    "12-growth": "Tăng trưởng & Đầu tư",
}

DEFAULT_SPEAKERS = {
    "01-governance": "legal-officer",
    "02-strategy": "strategy-lead",
    "03-finance": "cfo",
    "04-people": "hr-manager",
    "05-operations": "ops-manager",
    "06-sales": "sales-lead",
    "07-marketing": "brand-manager",
    "08-customer": "cs-lead",
    "09-product-tech": "product-manager",
    "10-training": "training-lead",
    "11-reporting": "data-analyst",
    "12-growth": "growth-strategist",
}

ROUTING_RULES = {
    "07-marketing": [
        {"keywords": ["ads", "quảng cáo", "fb", "google", "campaign"], "agent": "ads-specialist"},
        {"keywords": ["seo", "rank", "organic"], "agent": "seo-specialist"},
        {"keywords": ["content", "viết bài", "editorial"], "agent": "content-creator"},
    ],
    "06-sales": [
        {"keywords": ["account", "key account", "kh lớn"], "agent": "account-manager"},
        {"keywords": ["lead", "prospect", "tìm khách"], "agent": "sdr"},
    ],
    "09-product-tech": [
        {"keywords": ["security", "bảo mật", "vuln"], "agent": "security-officer"},
        {"keywords": ["tech", "kỹ thuật", "infra"], "agent": "tech-lead"},
    ],
    "03-finance": [
        {"keywords": ["kế toán", "phiếu thu chi", "hạch toán"], "agent": "accountant"},
        {"keywords": ["phân tích", "báo cáo tc"], "agent": "financial-analyst"},
    ],
    "04-people": [
        {"keywords": ["tuyển dụng", "jd", "phỏng vấn"], "agent": "recruiter"},
        {"keywords": ["đào tạo", "training"], "agent": "training-coordinator"},
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


def gen_stubs(repo_root: Path) -> int:
    depts_root = repo_root / "departments"
    total = 0
    for dept, agents in AGENTS.items():
        agents_dir = depts_root / dept / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        for aid, name, emoji in agents:
            path = agents_dir / f"{aid}.md"
            if path.exists():
                continue
            path.write_text(TEMPLATE.format(
                id=aid, name_vn=name, dept=dept,
                dept_name=DEPT_NAMES_VN.get(dept, dept), emoji=emoji,
            ), encoding="utf-8")
            total += 1
            print(f"  + {dept}/{aid}.md")
    return total


def update_dept_yamls(repo_root: Path) -> int:
    count = 0
    for dept_code, agents in AGENTS.items():
        yaml_path = repo_root / "departments" / dept_code / "department.yaml"
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        data["agents"] = [aid for aid, _, _ in agents]
        data["default_speaker"] = DEFAULT_SPEAKERS.get(dept_code, agents[0][0])
        if dept_code in ROUTING_RULES:
            data["routing_rules"] = ROUTING_RULES[dept_code]
        yaml_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8"
        )
        count += 1
        print(f"  [updated] {yaml_path.relative_to(repo_root)}: {len(agents)} agents")
    return count


if __name__ == "__main__":
    repo = Path(__file__).parent.parent.parent
    print("=== Generating agent stubs ===")
    created = gen_stubs(repo)
    print(f"\nCreated {created} agent files.\n")
    print("=== Updating department.yaml files ===")
    updated = update_dept_yamls(repo)
    print(f"\nUpdated {updated} department YAMLs.")
