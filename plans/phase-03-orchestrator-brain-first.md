# Phase 3 — Orchestrator + Brain-first

**Goal:** Router phân loại task + Gap analyzer + Clarifier (RULE 1: Brain-first) + Flow controller (Stop 1, Stop 2).

**Dependency:** Phase 1 + 2.

**Estimated tasks:** 10

---

### Task 1: Classifier rules + Router

**Files:**
- Create: `core/orchestrator/__init__.py`
- Create: `core/orchestrator/classifier_rules.yaml`
- Create: `core/orchestrator/router.py`
- Create: `tests/unit/test_router.py`

- [ ] **Step 1.1: Create classifier rules**

```yaml
# core/orchestrator/classifier_rules.yaml
SIMPLE:
  description: "Task đơn giản, không cần họp, 1-2 agent"
  keywords:
    - "soạn jd"
    - "viết jd"
    - "hợp đồng mẫu"
    - "biên bản"
    - "đơn từ"
    - "thư mời"
    - "công văn"
  max_departments: 2
  
COMPLEX:
  description: "Task phức tạp, cần họp 3-5 phòng debate"
  keywords:
    - "chiến dịch"
    - "kế hoạch"
    - "định giá"
    - "tuyển dụng"
    - "ra mắt sản phẩm"
    - "mở rộng"
    - "campaign"
    - "ngân sách"
  max_departments: 5

STRATEGIC:
  description: "Task chiến lược, cần CEO duyệt giữa chừng"
  keywords:
    - "gọi vốn"
    - "m&a"
    - "mở chi nhánh"
    - "pivot"
    - "exit"
    - "chuyển hướng"
    - "tái cấu trúc"
    - "ipo"
  min_departments: 5
```

- [ ] **Step 1.2: Write failing test**

```python
# tests/unit/test_router.py
from unittest.mock import MagicMock
from pathlib import Path
from core.orchestrator.router import Router, TaskClass
from core.brain.schema import (
    BrainContext, Strategy, Budget, Headcount, Product,
)

REPO = Path(__file__).parent.parent.parent


def _brain():
    return BrainContext(
        strategy=Strategy(vision="V", icp="SME"),
        products=[Product(code="P", name="X", price_vnd=1000, margin_pct=50)],
        budget=Budget(total_year_vnd=1_000_000_000),
        headcount=Headcount(active_departments=["07-marketing", "03-finance"]),
        laws=[], decisions=[], state="growth", glossary={},
    )


def test_router_keyword_simple():
    llm = MagicMock(complete=MagicMock(return_value='{"class": "SIMPLE", "departments": ["04-people"], "reasoning": "JD task"}'))
    r = Router(llm=llm, rules_path=REPO / "core/orchestrator/classifier_rules.yaml")
    result = r.classify("Soạn JD cho vị trí kế toán trưởng", _brain())
    assert result.class_ == TaskClass.SIMPLE


def test_router_keyword_complex():
    llm = MagicMock(complete=MagicMock(return_value=
        '{"class": "COMPLEX", "departments": ["07-marketing", "02-strategy", "03-finance", "08-customer", "01-governance"], "reasoning": "campaign needs many"}'
    ))
    r = Router(llm=llm, rules_path=REPO / "core/orchestrator/classifier_rules.yaml")
    result = r.classify("Tạo chiến dịch QC nhắm khách thu nhập 50tr+", _brain())
    assert result.class_ == TaskClass.COMPLEX
    assert len(result.departments) == 5


def test_router_returns_reasoning():
    llm = MagicMock(complete=MagicMock(return_value=
        '{"class": "STRATEGIC", "departments": ["02-strategy","03-finance","12-growth","01-governance","04-people"], "reasoning": "M&A high stakes"}'
    ))
    r = Router(llm=llm, rules_path=REPO / "core/orchestrator/classifier_rules.yaml")
    result = r.classify("Đánh giá M&A đối thủ Y", _brain())
    assert "M&A" in result.reasoning
```

- [ ] **Step 1.3: Implement Router**

```python
# core/orchestrator/router.py
"""Phân loại task: SIMPLE / COMPLEX / STRATEGIC + chọn phòng tham gia."""
from __future__ import annotations
from enum import Enum
from pathlib import Path
import json
import yaml
from dataclasses import dataclass
from core.brain.schema import BrainContext


class TaskClass(str, Enum):
    SIMPLE = "SIMPLE"
    COMPLEX = "COMPLEX"
    STRATEGIC = "STRATEGIC"


@dataclass
class TaskClassification:
    class_: TaskClass
    departments: list[str]
    reasoning: str
    confidence: float = 0.8


ROUTER_PROMPT = """Bạn là router phân loại task DN VN.

## Phân loại
- SIMPLE: 1-2 phòng, không cần họp. VD: soạn JD, hợp đồng mẫu.
- COMPLEX: 3-5 phòng họp debate. VD: chiến dịch QC, kế hoạch tuyển dụng.
- STRATEGIC: 5+ phòng, CEO duyệt giữa chừng. VD: gọi vốn, M&A, pivot.

## Phòng ban (mã chuẩn)
01-governance, 02-strategy, 03-finance, 04-people, 05-operations,
06-sales, 07-marketing, 08-customer, 09-product-tech, 10-training,
11-reporting, 12-growth, + pack-specific (13-XX)

## Output JSON BẮT BUỘC
```json
{
  "class": "SIMPLE|COMPLEX|STRATEGIC",
  "departments": ["XX-name", ...],
  "reasoning": "..."
}
```

## Nguyên tắc chọn phòng
- Suy ra từ keyword trong brief
- Tham chiếu Brain để biết phòng nào active
- Strict: chỉ chọn phòng thực sự cần
"""


class Router:
    def __init__(self, llm, rules_path: Path | None = None):
        self.llm = llm
        if rules_path:
            self.rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
        else:
            self.rules = {}
    
    def classify(self, brief: str, brain: BrainContext) -> TaskClassification:
        active = brain.headcount.active_departments
        rules_text = yaml.safe_dump(self.rules, allow_unicode=True)
        
        messages = [
            {"role": "system", "content": ROUTER_PROMPT + f"\n\n## RULES\n```yaml\n{rules_text}\n```"},
            {"role": "user", "content": (
                f"## BRIEF\n{brief}\n\n"
                f"## PHÒNG ĐANG ACTIVE\n{active}\n\n"
                f"Phân loại + chọn phòng cần triệu tập. Trả JSON đúng format."
            )},
        ]
        raw = self.llm.complete(messages)
        data = self._parse_json(raw)
        return TaskClassification(
            class_=TaskClass(data["class"]),
            departments=data["departments"],
            reasoning=data.get("reasoning", ""),
            confidence=float(data.get("confidence", 0.8)),
        )
    
    @staticmethod
    def _parse_json(raw: str) -> dict:
        # Extract JSON từ response (có thể có markdown ```json)
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError(f"Router output no JSON: {raw[:200]}")
        return json.loads(m.group(0))
```

- [ ] **Step 1.4: Run + commit**

```bash
pytest tests/unit/test_router.py -v
git add core/orchestrator/__init__.py core/orchestrator/router.py core/orchestrator/classifier_rules.yaml tests/unit/test_router.py
git commit -m "feat(orchestrator): add Router (SIMPLE/COMPLEX/STRATEGIC)"
```

---

### Task 2: Gap Analyzer (Brain vs Brief)

**Files:**
- Create: `core/brain/gap_analyzer.py`
- Create: `tests/unit/test_gap_analyzer.py`

- [ ] **Step 2.1: Write failing test**

```python
# tests/unit/test_gap_analyzer.py
from unittest.mock import MagicMock
import json
from core.brain.gap_analyzer import GapAnalyzer, Gap, Severity
from core.brain.schema import BrainContext, Strategy, Product, Budget, Headcount


def _brain():
    return BrainContext(
        strategy=Strategy(vision="V", icp="SME 5-50 NV (chủ DN)"),
        products=[
            Product(code="STR", name="Starter", price_vnd=1_000_000, margin_pct=60),
            Product(code="PRE", name="Premium", price_vnd=20_000_000, margin_pct=75),
        ],
        budget=Budget(total_year_vnd=1_200_000_000, mkt_quarter_remaining_vnd=800_000_000),
        headcount=Headcount(
            active_departments=["07-marketing"],
            active_agents={"07-marketing": ["brand-manager", "ads-specialist"]},
        ),
        laws=[], decisions=[], state="growth", glossary={},
    )


def test_gap_detects_icp_mismatch():
    fake = json.dumps([
        {"field": "ICP", "severity": "CRITICAL",
         "current_value": "SME (chủ DN)",
         "brief_value": "cá nhân thu nhập 50tr+",
         "reason": "Brief lệch khỏi strategy ICP", "citation": "00-Brain/strategy.md"}
    ])
    llm = MagicMock(complete=MagicMock(return_value=fake))
    g = GapAnalyzer(llm=llm)
    gaps = g.analyze(brief="QC nhắm khách thu nhập 50tr+", brain=_brain())
    assert len(gaps) == 1
    assert gaps[0].severity == Severity.CRITICAL
    assert "ICP" in gaps[0].field


def test_gap_empty_when_brain_sufficient():
    llm = MagicMock(complete=MagicMock(return_value="[]"))
    g = GapAnalyzer(llm=llm)
    gaps = g.analyze(brief="Soạn JD kế toán", brain=_brain())
    assert gaps == []
```

- [ ] **Step 2.2: Implement**

```python
# core/brain/gap_analyzer.py
"""So brief với Brain → list gaps cần CEO làm rõ.

🔒 RULE 1 enforce: gap PHẢI có citation chỉ về Brain file/section.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import json
from core.brain.schema import BrainContext


class Severity(str, Enum):
    CRITICAL = "CRITICAL"   # phải hỏi CEO
    WARN = "WARN"           # nên hỏi
    INFO = "INFO"           # skip


@dataclass
class Gap:
    field: str
    severity: Severity
    current_value: str
    brief_value: str
    reason: str
    citation: str   # 00-Brain/<file>.md[:section]


GAP_PROMPT = """Bạn là Gap Analyzer. So brief với Brain context, tìm điểm mâu thuẫn / thiếu thông tin.

## Output JSON BẮT BUỘC: array of gaps
```json
[
  {
    "field": "ICP|budget|product_fit|headcount|...",
    "severity": "CRITICAL|WARN|INFO",
    "current_value": "...",
    "brief_value": "...",
    "reason": "...",
    "citation": "00-Brain/<file>.md hoặc 00-Brain/<file>.md:<section>"
  }
]
```

## Nguyên tắc
- 🔒 RULE 1: Mỗi gap PHẢI có citation về Brain
- CRITICAL: brief mâu thuẫn strategy/budget/laws
- WARN: brief có thể OK nhưng cần CEO confirm
- INFO: nice-to-know, KHÔNG hỏi CEO
- Nếu brief KHỚP Brain hoàn toàn → return []
- Trả JSON array, KHÔNG kèm markdown
"""


class GapAnalyzer:
    def __init__(self, llm):
        self.llm = llm
    
    def analyze(self, brief: str, brain: BrainContext) -> list[Gap]:
        brain_dump = brain.model_dump_json(indent=2)
        messages = [
            {"role": "system", "content": GAP_PROMPT},
            {"role": "user", "content": (
                f"## BRIEF\n{brief}\n\n"
                f"## BRAIN\n```json\n{brain_dump}\n```\n\n"
                "Tìm gaps. Trả JSON array."
            )},
        ]
        raw = self.llm.complete(messages)
        data = self._parse_json_array(raw)
        return [Gap(
            field=d["field"],
            severity=Severity(d["severity"]),
            current_value=d.get("current_value", ""),
            brief_value=d.get("brief_value", ""),
            reason=d.get("reason", ""),
            citation=d["citation"],
        ) for d in data]
    
    @staticmethod
    def _parse_json_array(raw: str) -> list[dict]:
        import re
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m:
            return []
        return json.loads(m.group(0))
```

- [ ] **Step 2.3: Run + commit**

```bash
pytest tests/unit/test_gap_analyzer.py -v
git add core/brain/gap_analyzer.py tests/unit/test_gap_analyzer.py
git commit -m "feat(brain): add GapAnalyzer (RULE 1 Brain-first enforcement)"
```

---

### Task 3: Question Generator (Brain-first clarification)

**Files:**
- Create: `core/clarifier/__init__.py`
- Create: `core/clarifier/question_generator.py`
- Create: `tests/unit/test_question_generator.py`

- [ ] **Step 3.1: Write failing test**

```python
# tests/unit/test_question_generator.py
import json
from unittest.mock import MagicMock
from core.clarifier.question_generator import QuestionGenerator, Question
from core.brain.gap_analyzer import Gap, Severity


def test_no_gaps_no_questions():
    qg = QuestionGenerator(llm=MagicMock())
    questions = qg.generate(gaps=[], brain={}, brief="x")
    assert questions == []


def test_critical_gap_generates_critical_question():
    fake = json.dumps([{
        "text": "strategy.md ghi ICP là SME. Brief 50tr+ — pivot hay test?",
        "citation": "00-Brain/strategy.md",
        "choices": ["Pivot dài hạn", "Test 1 lần", "Hủy"],
        "severity": "CRITICAL",
    }])
    llm = MagicMock(complete=MagicMock(return_value=fake))
    qg = QuestionGenerator(llm=llm)
    gap = Gap(field="ICP", severity=Severity.CRITICAL,
              current_value="SME", brief_value="50tr+",
              reason="r", citation="00-Brain/strategy.md")
    questions = qg.generate(gaps=[gap], brain={"strategy": "..."}, brief="b")
    assert len(questions) == 1
    assert questions[0].severity == Severity.CRITICAL
    assert "strategy.md" in questions[0].citation
```

- [ ] **Step 3.2: Implement**

```python
# core/clarifier/question_generator.py
"""Sinh câu hỏi clarification dựa trên gap.

🔒 RULE 1: KHÔNG generate question nếu gaps rỗng.
🔒 RULE 4: Tiếng Việt, định nghĩa thuật ngữ.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
from core.brain.gap_analyzer import Gap, Severity


@dataclass
class Question:
    text: str
    citation: str
    severity: Severity
    choices: list[str] = field(default_factory=list)
    free_text: bool = False


QG_PROMPT = """Bạn sinh câu hỏi clarification cho CEO DN VN.

## Nguyên tắc CỨNG (vi phạm = reject output)
- 🔒 Mỗi câu hỏi PHẢI có citation về Brain (file:section)
- 🔒 Tiếng Việt, không jargon trừ khi định nghĩa kèm
- 🔒 Có 2-4 choices (đa số), hoặc free_text nếu open-ended
- 🔒 Câu hỏi ngắn gọn, đọc 30 giây hiểu

## Output JSON: array of questions
```json
[
  {
    "text": "...",
    "citation": "00-Brain/<file>.md[:section]",
    "choices": ["A", "B", "C"],
    "severity": "CRITICAL|WARN",
    "free_text": false
  }
]
```

CRITICAL gap → câu hỏi PHẢI hỏi.
WARN gap → câu hỏi NÊN hỏi (CEO có thể skip).
INFO gap → KHÔNG hỏi.
"""


class QuestionGenerator:
    def __init__(self, llm):
        self.llm = llm
    
    def generate(self, gaps: list[Gap], brain: dict, brief: str) -> list[Question]:
        # 🔒 RULE 1: no gaps → no questions
        if not gaps:
            return []
        
        actionable = [g for g in gaps if g.severity in (Severity.CRITICAL, Severity.WARN)]
        if not actionable:
            return []
        
        gaps_text = "\n".join(
            f"- [{g.severity.value}] {g.field}: brief='{g.brief_value}' vs brain='{g.current_value}' "
            f"(cite: {g.citation}) — {g.reason}"
            for g in actionable
        )
        
        messages = [
            {"role": "system", "content": QG_PROMPT},
            {"role": "user", "content": f"## BRIEF\n{brief}\n\n## GAPS\n{gaps_text}\n\nSinh questions."},
        ]
        raw = self.llm.complete(messages)
        
        import re
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(0))
        
        return [Question(
            text=d["text"],
            citation=d["citation"],
            severity=Severity(d["severity"]),
            choices=d.get("choices", []),
            free_text=d.get("free_text", False),
        ) for d in data]
```

- [ ] **Step 3.3: Run + commit**

```bash
pytest tests/unit/test_question_generator.py -v
git add core/clarifier/__init__.py core/clarifier/question_generator.py tests/unit/test_question_generator.py
git commit -m "feat(clarifier): add QuestionGenerator (Brain-first, RULE 1)"
```

---

### Task 4: Clarification Writer + Reader (file-based dialog)

**Files:**
- Create: `core/clarifier/clarification_io.py`
- Create: `tests/unit/test_clarification_io.py`

- [ ] **Step 4.1: Write failing test**

```python
# tests/unit/test_clarification_io.py
from pathlib import Path
from core.clarifier.question_generator import Question
from core.brain.gap_analyzer import Severity
from core.clarifier.clarification_io import (
    write_clarification, read_answers, AnsweredQuestion,
)


def test_write_clarification_creates_file(tmp_path):
    qs = [Question(
        text="Pivot hay test?",
        citation="00-Brain/strategy.md",
        choices=["Pivot dài hạn", "Test 1 lần"],
        severity=Severity.CRITICAL,
    )]
    f = tmp_path / "03-clarification.md"
    write_clarification(f, qs)
    content = f.read_text(encoding="utf-8")
    assert "Pivot hay test?" in content
    assert "[ ] Pivot dài hạn" in content
    assert "00-Brain/strategy.md" in content


def test_read_answers_parses_user_choice(tmp_path):
    f = tmp_path / "03-clarification.md"
    f.write_text(
        "---\ntype: clarification\n---\n"
        "## Q1 [CRITICAL]\n_Cite: 00-Brain/strategy.md_\n"
        "Pivot hay test?\n\n"
        "- [ ] Pivot dài hạn\n"
        "- [x] Test 1 lần\n"
        "- [ ] Hủy\n",
        encoding="utf-8",
    )
    answers = read_answers(f)
    assert len(answers) == 1
    assert answers[0].choice == "Test 1 lần"
```

- [ ] **Step 4.2: Implement**

```python
# core/clarifier/clarification_io.py
"""Write clarification.md cho CEO + parse answer khi CEO tick checkbox."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re
import yaml
from core.clarifier.question_generator import Question


@dataclass
class AnsweredQuestion:
    question_text: str
    choice: Optional[str]
    free_text_answer: Optional[str] = None


def write_clarification(path: Path, questions: list[Question]) -> None:
    parts = ["---", "type: clarification", "answered: false", "---", ""]
    parts.append("# 🤖 Câu hỏi từ hệ thống (Brain-first)")
    parts.append("")
    parts.append("> Tick `[x]` vào lựa chọn của CEO, hoặc điền free-text. Lưu file.")
    parts.append("")
    
    for i, q in enumerate(questions, 1):
        parts.append(f"## Q{i} [{q.severity.value}]")
        parts.append(f"_Cite: {q.citation}_")
        parts.append("")
        parts.append(q.text)
        parts.append("")
        if q.choices:
            for c in q.choices:
                parts.append(f"- [ ] {c}")
        if q.free_text:
            parts.append("")
            parts.append("**Trả lời:**")
            parts.append("```")
            parts.append("(điền vào đây)")
            parts.append("```")
        parts.append("")
    
    path.write_text("\n".join(parts), encoding="utf-8")


def read_answers(path: Path) -> list[AnsweredQuestion]:
    content = path.read_text(encoding="utf-8")
    answers = []
    
    blocks = re.split(r"^## Q\d+", content, flags=re.MULTILINE)[1:]
    for block in blocks:
        # Tìm checked choice
        checked = re.search(r"^-\s+\[x\]\s+(.+)$", block, re.MULTILINE | re.IGNORECASE)
        # Tìm free text
        free = re.search(r"```\n(.*?)\n```", block, re.DOTALL)
        free_text = None
        if free:
            txt = free.group(1).strip()
            if txt and txt != "(điền vào đây)":
                free_text = txt
        # Question text
        qm = re.search(r"\n\n([^\n]+\?)\s*$", block.split("- [")[0], re.MULTILINE)
        question_text = qm.group(1) if qm else "(unknown)"
        
        answers.append(AnsweredQuestion(
            question_text=question_text,
            choice=checked.group(1).strip() if checked else None,
            free_text_answer=free_text,
        ))
    
    return answers
```

- [ ] **Step 4.3: Run + commit**

```bash
pytest tests/unit/test_clarification_io.py -v
git add core/clarifier/clarification_io.py tests/unit/test_clarification_io.py
git commit -m "feat(clarifier): add markdown clarification I/O (CEO tick checkbox)"
```

---

### Task 5: Perspectives Collector (round 1 từ phòng ban)

**Files:**
- Create: `core/orchestrator/perspectives_collector.py`
- Create: `tests/unit/test_perspectives_collector.py`

- [ ] **Step 5.1: Write failing test**

```python
# tests/unit/test_perspectives_collector.py
from unittest.mock import MagicMock
from pathlib import Path
from core.orchestrator.perspectives_collector import PerspectivesCollector
from core.meeting.debate_state import new_meeting_state


def test_collector_loads_dept_and_calls_agent():
    """Collector cho mỗi dept → load default speaker → call LLM."""
    llm = MagicMock(complete=MagicMock(return_value="Phòng X nói: ABC"))
    
    repo = Path(__file__).parent.parent.parent
    collector = PerspectivesCollector(
        departments_root=repo / "departments",
        llm=llm,
    )
    
    state = new_meeting_state(
        brief="test", departments=["07-marketing"],
    )
    out = collector.collect(state)
    
    assert "07-marketing" in out["perspectives"]
    assert "ABC" in out["perspectives"]["07-marketing"]
```

- [ ] **Step 5.2: Implement**

```python
# core/orchestrator/perspectives_collector.py
"""Round 1 — mỗi phòng phát biểu góc nhìn (parallel)."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core.agents.department import DepartmentLoader
from core.agents.base_agent import BaseAgent
from core.meeting.debate_state import MeetingState


PERSPECTIVE_PROMPT = """Bạn là phòng {dept_name} trong DN VN.

Đọc brief + Brain context. Phát biểu GÓC NHÌN của phòng bạn:
- Phòng bạn quan tâm điều gì trong brief này?
- Cơ hội / rủi ro từ góc độ phòng bạn?
- Số liệu Brain liên quan (cite cụ thể)?
- Đề xuất ngắn gọn

Tiếng Việt. Định nghĩa thuật ngữ. Cite Brain mỗi nhận định.
KHÔNG dài quá 400 từ — đây là round 1.
"""


class PerspectivesCollector:
    def __init__(self, departments_root: Path, llm, max_parallel: int = 5):
        self.loader = DepartmentLoader(departments_root)
        self.llm = llm
        self.max_parallel = max_parallel
    
    def collect(self, state: MeetingState) -> dict:
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            futures = {
                executor.submit(self._speak_dept, dept_code, state): dept_code
                for dept_code in state["departments"]
            }
            for fut in futures:
                dept_code = futures[fut]
                try:
                    results[dept_code] = fut.result()
                except Exception as e:
                    results[dept_code] = f"[ERROR] {e}"
        
        return {"perspectives": results}
    
    def _speak_dept(self, dept_code: str, state: MeetingState) -> str:
        try:
            dept = self.loader.load(dept_code)
        except FileNotFoundError:
            return f"[Phòng {dept_code} chưa tồn tại trong vault]"
        
        agent = BaseAgent(
            name_vn=dept.name_vn,
            role=dept_code,
            system_prompt=PERSPECTIVE_PROMPT.format(dept_name=dept.name_vn),
            llm=self.llm,
            department=dept_code,
            temperature=0.5,
        )
        return agent.speak(
            brief=state["brief"],
            brain_context=state["brain_context"],
            history=[],
        )
```

- [ ] **Step 5.3: Run + commit**

```bash
pytest tests/unit/test_perspectives_collector.py -v
git add core/orchestrator/perspectives_collector.py tests/unit/test_perspectives_collector.py
git commit -m "feat(orchestrator): add PerspectivesCollector (parallel round 1)"
```

---

### Task 6: Flow Controller (Stop 1, Stop 2)

**Files:**
- Create: `core/orchestrator/flow_controller.py`
- Create: `tests/integration/test_flow_controller.py`

- [ ] **Step 6.1: Write integration test**

```python
# tests/integration/test_flow_controller.py
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
from core.orchestrator.flow_controller import FlowController, FlowResult, FlowStage


def test_flow_pauses_at_clarification_when_gaps_exist(tmp_path):
    """Khi có gaps → flow tạo clarification + dừng → trả PAUSE_CLARIFICATION."""
    
    fixture = Path(__file__).parent.parent / "fixtures" / "demo-vault"
    
    # Setup vault tạm
    import shutil
    vault = tmp_path / "vault"
    shutil.copytree(fixture, vault)
    
    llm = MagicMock()
    # Router output
    router_resp = json.dumps({"class": "COMPLEX", "departments": ["07-marketing", "03-finance"], "reasoning": "x"})
    # Gap analyzer output (1 gap)
    gap_resp = json.dumps([{
        "field": "ICP", "severity": "CRITICAL",
        "current_value": "SME", "brief_value": "50tr+",
        "reason": "lệch", "citation": "00-Brain/strategy.md"
    }])
    # Question gen output
    q_resp = json.dumps([{
        "text": "Pivot hay test?",
        "citation": "00-Brain/strategy.md",
        "choices": ["Pivot", "Test"],
        "severity": "CRITICAL",
        "free_text": False,
    }])
    llm.complete.side_effect = [router_resp, gap_resp, q_resp]
    
    fc = FlowController(vault_root=vault, llm=llm)
    result = fc.run(brief="Tạo chiến dịch QC nhắm khách thu nhập 50tr+")
    
    assert result.stage == FlowStage.PAUSE_CLARIFICATION
    assert result.task_folder.exists()
    assert (result.task_folder / "03-clarification.md").exists()
```

- [ ] **Step 6.2: Implement Flow Controller**

```python
# core/orchestrator/flow_controller.py
"""Điều phối toàn bộ flow: brief → router → gap → clarify (Stop pre) → 
   research → meeting → synthesizer (Stop 1) → execution (Stop 2)."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import re

from core.brain.reader import BrainReader
from core.brain.gap_analyzer import GapAnalyzer
from core.clarifier.question_generator import QuestionGenerator
from core.clarifier.clarification_io import (
    write_clarification, read_answers,
)
from core.obsidian.vault import ObsidianVault
from core.orchestrator.router import Router
from core.utils.config import load_config


class FlowStage(str, Enum):
    PAUSE_CLARIFICATION = "PAUSE_CLARIFICATION"   # đang chờ CEO trả lời
    PAUSE_DECISION_REPORT = "PAUSE_DECISION_REPORT"  # Stop 1
    PAUSE_EXECUTE = "PAUSE_EXECUTE"               # Stop 2
    DONE = "DONE"
    ERROR = "ERROR"


@dataclass
class FlowResult:
    stage: FlowStage
    task_folder: Path
    message: str = ""
    error: Optional[str] = None


def _slugify(brief: str, max_len: int = 50) -> str:
    s = re.sub(r"[^\w\s-]", "", brief.lower())
    s = re.sub(r"\s+", "-", s.strip())[:max_len]
    return s.strip("-") or "task"


class FlowController:
    def __init__(self, vault_root: Path, llm):
        self.vault = ObsidianVault(vault_root)
        self.llm = llm
        self.config = load_config()
    
    def run(self, brief: str) -> FlowResult:
        """Stage 1: brief → router → gap → clarification (PAUSE)."""
        # 1. Create task folder
        task_folder = self.vault.create_task_folder(_slugify(brief))
        (task_folder / "00-brief.md").write_text(
            f"---\ntype: brief\n---\n# Brief\n\n{brief}\n", encoding="utf-8",
        )
        
        # 2. Read Brain
        brain = BrainReader(self.vault.root).load()
        
        # 3. Router classify
        rules_path = Path(__file__).parent / "classifier_rules.yaml"
        router = Router(self.llm, rules_path=rules_path)
        classification = router.classify(brief, brain)
        
        (task_folder / "01-routing.md").write_text(
            f"---\ntype: routing\n---\n# Phân loại task\n\n"
            f"- **Class:** {classification.class_.value}\n"
            f"- **Departments:** {', '.join(classification.departments)}\n"
            f"- **Reasoning:** {classification.reasoning}\n",
            encoding="utf-8",
        )
        
        # 4. Context dump
        (task_folder / "02-context.md").write_text(
            "---\ntype: context\n---\n# Brain context loaded\n\n"
            f"```yaml\n{brain.model_dump_json(indent=2)}\n```\n",
            encoding="utf-8",
        )
        
        # 5. Gap analysis
        analyzer = GapAnalyzer(self.llm)
        gaps = analyzer.analyze(brief, brain)
        
        if not gaps:
            # Skip clarification → straight to research+meeting (Phase 4 will hook here)
            return FlowResult(
                stage=FlowStage.PAUSE_DECISION_REPORT,   # placeholder until phase 4-5 wires meeting
                task_folder=task_folder,
                message="Không có gap, sẵn sàng chạy meeting (Phase 4+5 sẽ wire).",
            )
        
        # 6. Generate questions
        qg = QuestionGenerator(self.llm)
        questions = qg.generate(gaps, brain.model_dump(), brief)
        
        if not questions:
            return FlowResult(
                stage=FlowStage.PAUSE_DECISION_REPORT,
                task_folder=task_folder,
                message="Gap có nhưng không CRITICAL/WARN, skip clarification.",
            )
        
        # 7. Write clarification + PAUSE
        clarification_path = task_folder / "03-clarification.md"
        write_clarification(clarification_path, questions)
        
        return FlowResult(
            stage=FlowStage.PAUSE_CLARIFICATION,
            task_folder=task_folder,
            message=f"Vui lòng trả lời {len(questions)} câu trong {clarification_path.name}",
        )
    
    def resume_after_clarification(self, task_folder: Path) -> FlowResult:
        """Stage 2: read answers → continue flow (Phase 4+ sẽ wire research+meeting)."""
        clarification_path = task_folder / "03-clarification.md"
        if not clarification_path.exists():
            return FlowResult(
                stage=FlowStage.ERROR, task_folder=task_folder,
                error="Không tìm thấy 03-clarification.md",
            )
        
        answers = read_answers(clarification_path)
        unanswered = [a for a in answers if a.choice is None and not a.free_text_answer]
        if unanswered:
            return FlowResult(
                stage=FlowStage.PAUSE_CLARIFICATION,
                task_folder=task_folder,
                message=f"Còn {len(unanswered)} câu chưa trả lời",
            )
        
        # Save normalized answers
        (task_folder / "03-clarification-answered.md").write_text(
            "---\ntype: answers\n---\n"
            + "\n".join(f"- Q: {a.question_text}\n  A: {a.choice or a.free_text_answer}"
                       for a in answers),
            encoding="utf-8",
        )
        
        # Phase 4-5 wires research + meeting here
        return FlowResult(
            stage=FlowStage.PAUSE_DECISION_REPORT,
            task_folder=task_folder,
            message="Đã ghi nhận trả lời. Phase 4+5 sẽ wire research + meeting.",
        )
```

- [ ] **Step 6.3: Run + commit**

```bash
pytest tests/integration/test_flow_controller.py -v
git add core/orchestrator/flow_controller.py tests/integration/test_flow_controller.py
git commit -m "feat(orchestrator): add FlowController with Stop 1 (clarification pause)"
```

---

### Task 7: Wire CLI to Flow Controller

**Files:**
- Modify: `core/cli.py:run` command (replace stub from Phase 1)

- [ ] **Step 7.1: Update CLI**

```python
# Replace `@main.command() def run(...)` trong core/cli.py
@main.command()
@click.option("--brief", required=True, help="Task brief (Vietnamese)")
@click.option("--vault", type=click.Path(), default=".")
def run(brief, vault):
    """Chạy task qua orchestrator (Stage 1: brief → clarification)."""
    from pathlib import Path
    from core.orchestrator.flow_controller import FlowController, FlowStage
    from core.llm.providers import get_default_provider
    
    fc = FlowController(vault_root=Path(vault), llm=get_default_provider())
    result = fc.run(brief)
    
    if result.stage == FlowStage.PAUSE_CLARIFICATION:
        console.print(f"[yellow]⏸  Pause cho clarification[/]")
        console.print(f"   Folder: {result.task_folder}")
        console.print(f"   {result.message}")
        console.print(f"\n[bold]Bước tiếp:[/] mở {result.task_folder}/03-clarification.md, "
                      f"tick câu trả lời, lưu file. Rồi chạy:")
        console.print(f"  [cyan]vn-os resume {result.task_folder}[/]")
    elif result.stage == FlowStage.ERROR:
        console.print(f"[red]✗ {result.error}[/]")
    else:
        console.print(f"[green]→ {result.stage.value}[/]: {result.message}")


@main.command()
@click.argument("task_folder", type=click.Path(exists=True))
def resume(task_folder):
    """Resume flow sau khi CEO trả lời clarification."""
    from pathlib import Path
    from core.orchestrator.flow_controller import FlowController, FlowStage
    from core.llm.providers import get_default_provider
    
    folder = Path(task_folder)
    vault_root = folder.parent.parent   # task_folder = vault/02-Tasks/<id>
    
    fc = FlowController(vault_root=vault_root, llm=get_default_provider())
    result = fc.resume_after_clarification(folder)
    console.print(f"[cyan]Stage:[/] {result.stage.value}")
    console.print(f"   {result.message}")
```

- [ ] **Step 7.2: Manual smoke test**

```bash
# Cần ANTHROPIC_API_KEY trong env
export ANTHROPIC_API_KEY=sk-...
vn-os run --brief "Tạo chiến dịch QC nhắm khách thu nhập 50tr+" --vault tests/fixtures/demo-vault
# Expected: tạo folder 02-Tasks/<ts>-tao-chien-dich-qc-... + write 03-clarification.md + report PAUSE
```

- [ ] **Step 7.3: Commit**

```bash
git add core/cli.py
git commit -m "feat(cli): wire run + resume commands to FlowController"
```

---

### Task 8: Domain-neutral check script

**Files:**
- Create: `scripts/dev/check-domain-neutral.sh`
- Create: `tests/integration/test_domain_neutral.py`

- [ ] **Step 8.1: Write check script**

```bash
#!/usr/bin/env bash
# Verify RULE 2: no trade/finance leakage trong core/
set -euo pipefail

FORBIDDEN_PATTERNS=(
  "Bull"
  "Bear"
  "trader"
  "ticker"
  "yfinance"
  "Alpha Vantage"
  "portfolio"
  "stock"
)

FAILED=0
for pat in "${FORBIDDEN_PATTERNS[@]}"; do
  echo "Checking: $pat"
  if grep -ri --include="*.py" -E "\b$pat\b" core/ 2>/dev/null; then
    echo "❌ Found '$pat' in core/ — RULE 2 violation"
    FAILED=1
  fi
done

if [ $FAILED -eq 1 ]; then
  echo "❌ Domain-neutral check FAILED"
  exit 1
fi
echo "✅ Domain-neutral check passed"
```

- [ ] **Step 8.2: Write Python test wrapper**

```python
# tests/integration/test_domain_neutral.py
import subprocess
from pathlib import Path


def test_no_trade_leakage_in_core():
    """RULE 2: core/ không được có Bull/Bear/trader/ticker/etc."""
    repo = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["bash", str(repo / "scripts/dev/check-domain-neutral.sh")],
        cwd=repo, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Domain-neutral check failed:\n{result.stdout}\n{result.stderr}"
```

- [ ] **Step 8.3: Run + commit**

```bash
chmod +x scripts/dev/check-domain-neutral.sh
bash scripts/dev/check-domain-neutral.sh
pytest tests/integration/test_domain_neutral.py -v
git add scripts/dev/check-domain-neutral.sh tests/integration/test_domain_neutral.py
git commit -m "test(rules): add RULE 2 domain-neutral check script"
```

---

### Task 9: Phase 3 integration smoke test

**Files:**
- Create: `tests/integration/test_phase03_smoke.py`

- [ ] **Step 9.1: Write smoke test**

```python
# tests/integration/test_phase03_smoke.py
"""Phase 3 smoke: orchestrator pipeline imports + run với mock LLM."""
from unittest.mock import MagicMock
from pathlib import Path
import json
import shutil


def test_full_orchestrator_imports():
    from core.orchestrator.router import Router, TaskClass
    from core.orchestrator.flow_controller import FlowController, FlowStage
    from core.orchestrator.perspectives_collector import PerspectivesCollector
    from core.brain.gap_analyzer import GapAnalyzer
    from core.clarifier.question_generator import QuestionGenerator
    from core.clarifier.clarification_io import write_clarification, read_answers


def test_full_flow_writes_all_task_files(tmp_path):
    fixture = Path(__file__).parent.parent / "fixtures" / "demo-vault"
    vault = tmp_path / "vault"
    shutil.copytree(fixture, vault)
    
    llm = MagicMock()
    llm.complete.side_effect = [
        json.dumps({"class": "COMPLEX", "departments": ["07-marketing"], "reasoning": "r"}),
        json.dumps([{
            "field": "ICP", "severity": "CRITICAL",
            "current_value": "SME", "brief_value": "50tr+",
            "reason": "x", "citation": "00-Brain/strategy.md"
        }]),
        json.dumps([{
            "text": "Pivot?", "citation": "00-Brain/strategy.md",
            "choices": ["A", "B"], "severity": "CRITICAL", "free_text": False,
        }]),
    ]
    
    from core.orchestrator.flow_controller import FlowController
    fc = FlowController(vault_root=vault, llm=llm)
    r = fc.run(brief="Tạo chiến dịch")
    
    expected = ["00-brief.md", "01-routing.md", "02-context.md", "03-clarification.md"]
    for fname in expected:
        assert (r.task_folder / fname).exists(), f"Missing {fname}"
```

- [ ] **Step 9.2: Run + tag**

```bash
pytest tests/integration/test_phase03_smoke.py -v
git add tests/integration/test_phase03_smoke.py
git commit -m "test(phase-03): smoke test for full orchestrator pipeline"
git tag phase-03-complete
```

---

## Phase 3 Done When

- [x] Router classify SIMPLE/COMPLEX/STRATEGIC + chọn phòng
- [x] GapAnalyzer detect gap với citation Brain
- [x] QuestionGenerator chỉ sinh question khi có gap (RULE 1)
- [x] Clarification I/O: write markdown + parse CEO checkbox
- [x] PerspectivesCollector parallel call multiple depts
- [x] FlowController có Stop 1 (clarification pause) work
- [x] CLI `vn-os run` + `vn-os resume` work
- [x] Domain-neutral check script pass
- [x] Phase 3 smoke test pass
