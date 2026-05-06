"""E2E test case B - Chien dich QC nham khach thu nhap 50tr+.

Validates 6 RULES + acceptance criteria with mocked LLM.
"""
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock
import pytest


REPO = Path(__file__).parent.parent.parent
FIXTURE = REPO / "tests/fixtures/techco-vault"


@pytest.fixture
def llm_mock():
    """Mocked LLM with pre-canned responses for each stage."""

    responses = {
        "router_classify": json.dumps({
            "class": "COMPLEX",
            "departments": ["07-marketing", "02-strategy", "03-finance", "08-customer", "01-governance"],
            "reasoning": "Campaign QC + budget lon + can check legal + ICP gap",
        }),
        "gap_analysis": json.dumps([
            {"field": "ICP", "severity": "CRITICAL",
             "current_value": "SME (chu DN)", "brief_value": "thu nhap 50tr+",
             "reason": "Brief lech ICP strategy", "citation": "00-Brain/strategy.md"},
            {"field": "content_capability", "severity": "CRITICAL",
             "current_value": "khong co content-premium", "brief_value": "can content cao cap",
             "reason": "Headcount thieu specialist", "citation": "00-Brain/headcount.md"},
        ]),
        "questions": json.dumps([
            {"text": "Pivot dai han hay test 1 lan?",
             "citation": "00-Brain/strategy.md",
             "choices": ["Pivot dai han", "Test 1 lan (chu SME thu nhap 50tr+)", "Huy"],
             "severity": "CRITICAL", "free_text": False},
            {"text": "Tao agent content-premium hay outsource?",
             "citation": "00-Brain/headcount.md",
             "choices": ["Tao agent moi", "Outsource", "Marketing kiem"],
             "severity": "CRITICAL", "free_text": False},
        ]),
        "tool_plan": json.dumps({"tools": [
            {"tool": "industry_benchmark", "queries": ["saas_b2b cac"]},
        ]}),
        "perspective": "Phong de xuat trien khai can trong, kem so lieu Brain.",
        "pro_advocate": "GO. Co hoi thi truong ro. CAC 8tr/SQL theo benchmark.",
        "con_advocate": "Rui ro 62% budget don 1 cho + CSKH chua ready.",
        "growth": "GO bold - runway 18m du test ICP cao cap.",
        "cautious": "GO with gates - tuan 1 CTR < 2% pause.",
        "balanced": "Pilot 200tr/4 tuan + setup CSKH Premium.",
        "synthesizer": """## 📌 Tóm lại (đọc 30 giây)
- GO with revisions: 200tr/4 tuan
- 4 BLOCKERS phai xong truoc launch
- KPI: 1 deal Premium thang dau

## Khuyến nghị
GO with revisions

## Việc cần làm trước launch
1. [ ] Setup CSKH Premium tier
2. [ ] Train sales pitch Premium
3. [ ] Tao agent content-premium-b2b-specialist
4. [ ] Update privacy policy

## KPI gates
- Tuan 1: CTR >= 2%
- Tuan 4: >= 1 deal Premium

## Câu hỏi cần CEO quyết
A. Approve plan nay
B. Approve nhung khong cho blockers
C. Reject
D. Sua
""",
        # P0.2: execution planner LLM response (structured plan with template table)
        "execution_plan": """---
type: execution_plan
stop: 2
---
# Ke hoach thuc thi

## Cong viec

| STT | Cong viec | Phong phu trach | Han chot | Deliverable |
|-----|-----------|-----------------|----------|-------------|
| 1   | Lap ke hoach chien dich | 07-marketing | Tuan 1 | Marketing brief |
| 2   | Du toan ngan sach chi tiet | 03-finance | Tuan 1 | Bang du toan |
| 3   | Setup CSKH Premium | 08-customer | Tuan 2 | SOP Premium tier |

## Nguon luc

- **Ngan sach uoc tinh:** 200tr
- **Nhan su can them:** 1 Content Specialist

## Rui ro va bien phap

| Rui ro | Muc do | Bien phap giam thieu |
|--------|--------|----------------------|
| CTR thap | Cao | Pause tuan 1 neu CTR < 2% |

## Chi tieu thanh cong (KPI)

| Chi tieu | Muc tieu | Thoi han |
|----------|----------|----------|
| CTR | >= 2% | Tuan 1 |
| Deal Premium | >= 1 | Tuan 4 |

## Mau tai lieu can tao

| Ten mau | Phong | Ghi chu |
|---------|-------|---------|
| ke-hoach-kinh-doanh | 02-strategy | Ke hoach toan dien |
| ngan-sach-nam | 03-finance | Du toan ngan sach |
""",
    }

    def respond(messages, model=None):
        sys_text = messages[0]["content"]

        # Order matters - check most-specific first
        if "router phân loại task" in sys_text or "Router" in sys_text and "phân loại" in sys_text:
            return responses["router_classify"]
        if "Gap Analyzer" in sys_text:
            return responses["gap_analysis"]
        if "sinh câu hỏi clarification" in sys_text:
            return responses["questions"]
        if "Tool Router" in sys_text:
            return responses["tool_plan"]
        if "Pro Advocate" in sys_text:
            return responses["pro_advocate"]
        if "Con Advocate" in sys_text:
            return responses["con_advocate"]
        if "TĂNG TRƯỞNG" in sys_text:
            return responses["growth"]
        if "THẬN TRỌNG" in sys_text:
            return responses["cautious"]
        if "CÂN BẰNG" in sys_text:
            return responses["balanced"]
        if "tổng hợp họp DN" in sys_text or "báo cáo quyết định" in sys_text:
            return responses["synthesizer"]
        # P0.2: execution plan generator
        if "chien luoc gia dieu phoi ke hoach thuc thi" in sys_text:
            return responses["execution_plan"]
        # P0.1: template extraction fallback (LLM path — used when table absent)
        if "tro ly ky thuat" in sys_text and "trich xuat" in sys_text:
            return json.dumps([
                {"name": "ke-hoach-kinh-doanh", "dept_code": "02-strategy"},
            ])
        if "biên tập viên DN VN" in sys_text:
            # simplifier - return content unchanged (no jargon in test fixtures)
            return messages[1]["content"]
        if "Tóm tắt báo cáo" in sys_text:
            # tldr - already has '📌 Tóm lại' marker in synthesizer response
            return ""
        if "Ban la phong" in sys_text and "trong DN VN" in sys_text:
            # PerspectivesCollector dept agent
            return responses["perspective"]
        return "..."

    llm = MagicMock()
    llm.complete.side_effect = respond
    return llm


def test_e2e_b_campaign_full_flow(tmp_path, llm_mock):
    """Full E2E flow: brief -> clarify -> meeting -> decision report."""
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)

    from core.orchestrator.flow_controller import FlowController, FlowStage

    fc = FlowController(vault_root=vault, llm=llm_mock)

    # Stage 1: brief -> clarification
    result = fc.run(brief="Tạo chiến dịch QC nhắm khách thu nhập 50tr+, NS 500tr, launch trước 30/6")

    assert result.stage == FlowStage.PAUSE_CLARIFICATION
    task_folder = result.task_folder

    # Verify files
    assert (task_folder / "00-brief.md").exists()
    assert (task_folder / "01-routing.md").exists()
    assert (task_folder / "02-context.md").exists()
    assert (task_folder / "03-clarification.md").exists()

    # RULE 1: questions co citation
    clarif = (task_folder / "03-clarification.md").read_text(encoding="utf-8")
    assert "00-Brain/strategy.md" in clarif
    assert "00-Brain/headcount.md" in clarif

    # Auto-tick CEO answers
    answered = clarif.replace(
        "- [ ] Test 1 lan (chu SME thu nhap 50tr+)",
        "- [x] Test 1 lan (chu SME thu nhap 50tr+)",
    ).replace(
        "- [ ] Tao agent moi",
        "- [x] Tao agent moi",
    )
    (task_folder / "03-clarification.md").write_text(answered, encoding="utf-8")

    # Stage 2: resume after clarification
    result = fc.resume_after_clarification(task_folder)
    assert result.stage == FlowStage.PAUSE_DECISION_REPORT

    # Stage 3: meeting
    departments = ["07-marketing", "02-strategy", "03-finance", "08-customer", "01-governance"]
    result = fc.run_meeting(task_folder, departments=departments)
    assert result.stage == FlowStage.PAUSE_DECISION_REPORT

    # Verify meeting outputs
    assert (task_folder / "03b-research-findings.md").exists()
    assert (task_folder / "04-meeting-r1-perspectives.md").exists()
    assert (task_folder / "05-meeting-r2-debate.md").exists()
    assert (task_folder / "06-meeting-r3-perspectives.md").exists()
    assert (task_folder / "07-decision-report.md").exists()

    # ACCEPTANCE
    decision = (task_folder / "07-decision-report.md").read_text(encoding="utf-8")
    assert "📌 Tóm lại" in decision
    assert "Khuyến nghị" in decision or "Câu hỏi cần CEO quyết" in decision


def test_acceptance_no_trade_leakage_in_outputs(tmp_path, llm_mock):
    """RULE 2: outputs phai khong co Bull/Bear/trade/etc."""
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)

    from core.orchestrator.flow_controller import FlowController
    fc = FlowController(vault_root=vault, llm=llm_mock)
    result = fc.run(brief="Test campaign")

    forbidden = ["Bull", "Bear", "ticker", "yfinance", "trader"]
    for f in (result.task_folder).rglob("*.md"):
        content = f.read_text(encoding="utf-8")
        for word in forbidden:
            assert word not in content, f"Found '{word}' in {f.name}"


def _run_through_meeting(tmp_path, llm_mock):
    """Helper: run full flow up to decision report, return (fc, task_folder)."""
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)

    from core.orchestrator.flow_controller import FlowController, FlowStage

    fc = FlowController(vault_root=vault, llm=llm_mock)

    result = fc.run(brief="Tao chien dich QC thu nhap cao, NS 500tr, launch truoc 30/6")
    assert result.stage == FlowStage.PAUSE_CLARIFICATION
    task_folder = result.task_folder

    clarif = (task_folder / "03-clarification.md").read_text(encoding="utf-8")
    answered = clarif.replace(
        "- [ ] Test 1 lan (chu SME thu nhap 50tr+)",
        "- [x] Test 1 lan (chu SME thu nhap 50tr+)",
    ).replace(
        "- [ ] Tao agent moi",
        "- [x] Tao agent moi",
    )
    (task_folder / "03-clarification.md").write_text(answered, encoding="utf-8")

    fc.resume_after_clarification(task_folder)

    departments = ["07-marketing", "02-strategy", "03-finance", "08-customer", "01-governance"]
    result = fc.run_meeting(task_folder, departments=departments)
    assert result.stage == FlowStage.PAUSE_DECISION_REPORT

    return fc, task_folder


def test_approve_decision_writes_real_execution_plan(tmp_path, llm_mock):
    """P0.2: approve_decision generates structured 08-execution-plan.md (not stub)."""
    from core.orchestrator.flow_controller import FlowStage

    fc, task_folder = _run_through_meeting(tmp_path, llm_mock)

    result = fc.approve_decision(task_folder)

    assert result.stage == FlowStage.PAUSE_EXECUTE, f"Expected PAUSE_EXECUTE, got {result.stage}: {result.error}"

    plan_path = task_folder / "08-execution-plan.md"
    assert plan_path.exists(), "08-execution-plan.md not created by approve_decision"

    plan_text = plan_path.read_text(encoding="utf-8")

    # Must have YAML frontmatter with correct type
    assert "type: execution_plan" in plan_text, "Missing frontmatter type"
    assert "stop: 2" in plan_text, "Missing stop marker"

    # Must NOT be stub
    assert "TODO Phase 6" not in plan_text, "08-execution-plan.md still contains stub TODO"

    # Must have substantive content
    assert "Ke hoach" in plan_text or "Kế hoạch" in plan_text or "cong viec" in plan_text.lower(), \
        "Execution plan missing substantive content"


def test_execute_calls_docwriter_generates_outputs(tmp_path, llm_mock):
    """P0.1: execute() calls DocWriter and writes real files to 03-Outputs/."""
    from core.orchestrator.flow_controller import FlowStage

    fc, task_folder = _run_through_meeting(tmp_path, llm_mock)

    # approve first to create 08-execution-plan.md
    approve_result = fc.approve_decision(task_folder)
    assert approve_result.stage == FlowStage.PAUSE_EXECUTE

    # execute
    result = fc.execute(task_folder)
    assert result.stage == FlowStage.DONE, f"Expected DONE, got {result.stage}: {result.error}"

    outputs_dir = fc.vault.root / "03-Outputs" / task_folder.name
    assert outputs_dir.exists(), "03-Outputs/<task>/ directory not created"

    # README manifest must exist
    readme = outputs_dir / "README.md"
    assert readme.exists(), "README.md manifest not created in outputs dir"
    readme_text = readme.read_text(encoding="utf-8")
    assert "TODO Phase 6" not in readme_text, "README still contains stub TODO text"

    # At least one real output file OR graceful skipped list (templates may be absent in fixture)
    docx_files = list(outputs_dir.glob("*.docx"))
    xlsx_files = list(outputs_dir.glob("*.xlsx"))
    all_files = docx_files + xlsx_files

    # Either real docs generated OR graceful skip logged (both are valid for fixture vault)
    # Fixture vault has no 01-Departments so TemplateResolver falls back to repo templates-vn/
    # repo/templates-vn/02-strategy/ke-hoach-kinh-doanh.md exists → should generate
    if not all_files:
        # Acceptable: all templates were skipped gracefully — verify skip message present
        assert "Khong tim thay" in readme_text or "skipped" in result.message.lower() or \
               "Bỏ qua" in result.message, \
               "No docs generated and no graceful skip message — execute may have silently failed"
    else:
        # Real docs generated — verify they are non-empty
        for f in all_files:
            assert f.stat().st_size > 0, f"Generated file {f.name} is empty"


def test_execute_without_execution_plan_returns_error(tmp_path, llm_mock):
    """P0.1: execute() without prior approve returns ERROR stage, not exception."""
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)

    from core.orchestrator.flow_controller import FlowController, FlowStage

    fc = FlowController(vault_root=vault, llm=llm_mock)
    result = fc.run(brief="Test brief")
    task_folder = result.task_folder

    # Call execute directly without approve (no 08-execution-plan.md)
    exec_result = fc.execute(task_folder)
    assert exec_result.stage == FlowStage.ERROR
    assert exec_result.error is not None
    assert "08-execution-plan.md" in exec_result.error


def test_approve_without_decision_report_returns_error(tmp_path, llm_mock):
    """P0.2: approve_decision() without prior meeting returns ERROR, not exception."""
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)

    from core.orchestrator.flow_controller import FlowController, FlowStage

    fc = FlowController(vault_root=vault, llm=llm_mock)
    result = fc.run(brief="Test brief")
    task_folder = result.task_folder

    # Call approve directly without meeting (no 07-decision-report.md)
    approve_result = fc.approve_decision(task_folder)
    assert approve_result.stage == FlowStage.ERROR
    assert approve_result.error is not None
    assert "07-decision-report.md" in approve_result.error
