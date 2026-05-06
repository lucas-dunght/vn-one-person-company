"""Generate structured execution plan from decision report (P0.2 fix).

Input:  07-decision-report.md  (written by Synthesizer after meeting)
Output: 08-execution-plan.md  (structured YAML frontmatter + markdown body)

Structure of the generated plan:
  - tasks: list of {title, owner, deadline, deliverable}
  - resources: {budget, headcount}
  - risks: list of {risk, mitigation}
  - kpis: list of {metric, target, timeframe}
  - templates_needed: list of {name, dept_code}  ← used by DocumentExecutor
"""
from __future__ import annotations
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# System prompt for execution plan generation (Vietnamese, CEO-friendly)
# ──────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """Ban la chien luoc gia dieu phoi ke hoach thuc thi cho DN VN.
Nhiem vu: doc Bao cao quyet dinh, sinh KE HOACH THUC THI day du.

Tra ve dung dinh dang:

---
type: execution_plan
stop: 2
---
# Ke hoach thuc thi

## Cong viec

| STT | Cong viec | Phong phu trach | Han chot | Deliverable |
|-----|-----------|-----------------|----------|-------------|
| 1   | ...       | ...             | ...      | ...         |

## Nguon luc

- **Ngan sach uoc tinh:** ...
- **Nhan su can them:** ...

## Rui ro va bien phap

| Rui ro | Muc do | Bien phap giam thieu |
|--------|--------|----------------------|
| ...    | Cao    | ...                  |

## Chi tieu thanh cong (KPI)

| Chi tieu | Muc tieu | Thoi han |
|----------|----------|----------|
| ...      | ...      | ...      |

## Mau tai lieu can tao

| Ten mau | Phong | Ghi chu |
|---------|-------|---------|
| ke-hoach-kinh-doanh | 02-strategy | Ke hoach toan dien |
| ngan-sach-nam | 03-finance | Du toan ngan sach |

QUY TAC:
- Tieng Viet, don gian, tranh jargon ky thuat
- Giu nguyen so lieu tu Bao cao quyet dinh
- Bang "Mau tai lieu can tao": chi liet khuyen nghi thiet thuc (1-5 mau), khong phat minh
- Phong phu trach dung ma (vi du: 07-marketing, 03-finance)
- Han chot: ngay cu the hoac "Tuan X" ke tu ngay duyet
"""


def generate_execution_plan(
    task_folder: Path,
    llm,
    translator,
) -> Path:
    """Read 07-decision-report.md, call LLM, write 08-execution-plan.md.

    Args:
        task_folder: path to the task folder containing decision report.
        llm: LLM provider with .complete(messages) interface.
        translator: TranslatorPipeline instance (RULE 4).

    Returns:
        Path to the written 08-execution-plan.md.

    Raises:
        FileNotFoundError: if 07-decision-report.md does not exist.
    """
    decision_path = task_folder / "07-decision-report.md"
    if not decision_path.exists():
        raise FileNotFoundError(
            f"07-decision-report.md not found in {task_folder}. "
            "Run vn_meeting first to generate the decision report."
        )

    decision_text = decision_path.read_text(encoding="utf-8")

    # Build prompt: include the full decision report as context
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "BAO CAO QUYET DINH:\n\n"
                f"{decision_text}\n\n"
                "Hay sinh ke hoach thuc thi theo dung dinh dang da huong dan."
            ),
        },
    ]

    try:
        raw_plan = llm.complete(messages)
    except Exception as exc:
        log.error("LLM call failed during execution plan generation: %s", exc)
        raise

    # Apply translator pipeline (RULE 4 — CEO-friendly language)
    try:
        translated_plan = translator.apply(raw_plan)
    except Exception as exc:
        log.warning(
            "Translator failed during execution plan generation (%s), using raw output.",
            exc,
        )
        translated_plan = raw_plan

    # Ensure YAML frontmatter present (defensive: LLM may omit it)
    if not translated_plan.strip().startswith("---"):
        translated_plan = (
            "---\ntype: execution_plan\nstop: 2\n---\n" + translated_plan
        )

    out_path = task_folder / "08-execution-plan.md"
    out_path.write_text(translated_plan, encoding="utf-8")
    log.info("Execution plan written to %s", out_path)
    return out_path


def parse_templates_from_plan(plan_path: Path) -> list[dict]:
    """Parse 'Mau tai lieu can tao' table from 08-execution-plan.md.

    Returns list of dicts: [{name: str, dept_code: str}, ...]
    Falls back to [] if table not found.
    """
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("Cannot read execution plan at %s: %s", plan_path, exc)
        return []

    templates: list[dict] = []
    in_table = False

    for line in text.splitlines():
        stripped = line.strip()

        # Detect start of the templates table
        if "mau tai lieu" in stripped.lower() or "mẫu tài liệu" in stripped.lower():
            in_table = True
            continue

        if not in_table:
            continue

        # Table rows start with |
        if not stripped.startswith("|"):
            # End of table only on a new heading — blank lines between heading
            # and table header are allowed.
            if stripped.startswith("#"):
                in_table = False
            continue

        # Skip header/divider rows
        if "---" in stripped or "ten mau" in stripped.lower() or "tên mẫu" in stripped.lower():
            continue

        # Parse | name | dept | notes |
        parts = [p.strip() for p in stripped.split("|") if p.strip()]
        if len(parts) >= 2:
            name = parts[0].strip()
            dept = parts[1].strip()
            # Skip if name looks like a header
            if name and dept and name.lower() not in ("ten mau", "tên mẫu", "stt", "#"):
                templates.append({"name": name, "dept_code": dept})

    log.debug("Parsed %d template requests from execution plan", len(templates))
    return templates
