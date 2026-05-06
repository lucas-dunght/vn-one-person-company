# Phase 2 — Debate Engine

**Goal:** Bóc engine debate từ TradingAgents → rename neutral (RULE 2: Domain-neutral). Implement MeetingState, conditional logic, checkpointer, Pro/Con/Perspective debators.

**Dependency:** Phase 1 done (Brain + DepartmentLoader available).

**Estimated tasks:** 8

---

### Task 1: Vendor TradingAgents reference (read-only)

**Files:**
- Create: `references/tradingagents/` (clone shallow, exclude from package)

- [ ] **Step 1.1: Clone TradingAgents để tham khảo**

```bash
mkdir -p references/
git clone --depth 1 https://github.com/TauricResearch/TradingAgents references/tradingagents
echo "references/" >> .gitignore   # KHÔNG vendor vào package
```

- [ ] **Step 1.2: Identify reusable files**

Read these reference files (DO NOT copy verbatim — adapt only):
- `tradingagents/graph/trading_graph.py` → graph orchestrator pattern
- `tradingagents/graph/conditional_logic.py` → debate routing pattern
- `tradingagents/graph/checkpointer.py` → SQLite checkpoint pattern
- `tradingagents/agents/utils/agent_states.py` → TypedDict state pattern
- `tradingagents/agents/researchers/bull_researcher.py` → debater impl pattern

- [ ] **Step 1.3: Verify .gitignore**

```bash
git status   # references/ should not appear
```

---

### Task 2: MeetingState (TypedDict, neutral naming)

**Files:**
- Create: `core/meeting/__init__.py`
- Create: `core/meeting/debate_state.py`
- Create: `tests/unit/test_meeting_state.py`

- [ ] **Step 2.1: Write failing test**

```python
# tests/unit/test_meeting_state.py
from core.meeting.debate_state import (
    MeetingState, PerspectiveDebateState, ProConDebateState,
    new_meeting_state,
)


def test_new_state_has_defaults():
    state = new_meeting_state(
        brief="Test campaign",
        departments=["07-marketing", "03-finance"],
        max_rounds=2,
    )
    assert state["brief"] == "Test campaign"
    assert state["departments"] == ["07-marketing", "03-finance"]
    assert state["pro_con_debate"]["pro_history"] == []
    assert state["pro_con_debate"]["count"] == 0
    assert state["max_debate_rounds"] == 2


def test_perspective_debate_three_voices():
    state = new_meeting_state(brief="x", departments=[])
    pd = state["perspective_debate"]
    assert "growth_history" in pd
    assert "cautious_history" in pd
    assert "balanced_history" in pd
    assert pd["latest_speaker"] is None


def test_state_serializable():
    """Critical: state must serialize for SQLite checkpoint."""
    import json
    state = new_meeting_state(brief="x", departments=[])
    # Convert dict (TypedDict is dict)
    s = json.dumps(state, default=str)
    assert "brief" in s
```

- [ ] **Step 2.2: Run test (expect FAIL)**

```bash
pytest tests/unit/test_meeting_state.py -v
```

- [ ] **Step 2.3: Implement MeetingState**

```python
# core/meeting/debate_state.py
"""TypedDict states cho LangGraph meeting orchestrator.

🔒 RULE 2: Domain-neutral. KHÔNG dùng từ trade/finance.
Adapted from TradingAgents/agents/utils/agent_states.py với rename neutral.
"""
from __future__ import annotations
from typing import TypedDict, Optional


class ProConDebateState(TypedDict):
    """Bull/Bear → Pro/Con (neutral). Phe đẩy mạnh vs phe phản biện."""
    pro_history: list[str]      # was: bull_history
    con_history: list[str]      # was: bear_history
    history: list[str]           # full turn-based transcript
    latest_speaker: Optional[str]
    count: int                   # số vòng đã chạy
    judge_decision: Optional[str]


class PerspectiveDebateState(TypedDict):
    """Risk debators → Perspective debators (neutral).
    
    growth   = was aggressive (champions high-reward strategies)
    cautious = was conservative (capital preservation, worst-case)
    balanced = was neutral (middle ground)
    """
    growth_history: list[str]
    cautious_history: list[str]
    balanced_history: list[str]
    history: list[str]
    latest_speaker: Optional[str]
    count: int
    judge_decision: Optional[str]


class MeetingState(TypedDict):
    """Root state cho LangGraph meeting graph."""
    # Inputs
    brief: str
    departments: list[str]
    brain_context: dict          # serialized BrainContext
    research_findings: dict      # tools output (Phase 4)
    
    # Per-department perspectives (round 1)
    perspectives: dict[str, str]
    
    # Debates (rounds 2 + 3)
    pro_con_debate: ProConDebateState
    perspective_debate: PerspectiveDebateState
    
    # Limits
    max_perspective_rounds: int
    max_debate_rounds: int
    max_perspective_debate_rounds: int
    
    # Output
    final_report: Optional[str]
    
    # Metadata
    task_id: str
    timestamp: str


def new_meeting_state(
    brief: str,
    departments: list[str],
    brain_context: dict | None = None,
    max_rounds: int = 2,
    task_id: str = "",
) -> MeetingState:
    from datetime import datetime
    return MeetingState(
        brief=brief,
        departments=departments,
        brain_context=brain_context or {},
        research_findings={},
        perspectives={},
        pro_con_debate=ProConDebateState(
            pro_history=[], con_history=[], history=[],
            latest_speaker=None, count=0, judge_decision=None,
        ),
        perspective_debate=PerspectiveDebateState(
            growth_history=[], cautious_history=[], balanced_history=[],
            history=[], latest_speaker=None, count=0, judge_decision=None,
        ),
        max_perspective_rounds=1,
        max_debate_rounds=max_rounds,
        max_perspective_debate_rounds=1,
        final_report=None,
        task_id=task_id,
        timestamp=datetime.now().isoformat(),
    )
```

- [ ] **Step 2.4: Run + commit**

```bash
pytest tests/unit/test_meeting_state.py -v
git add core/meeting/__init__.py core/meeting/debate_state.py tests/unit/test_meeting_state.py
git commit -m "feat(meeting): add neutral MeetingState (Pro/Con + Perspective)"
```

---

### Task 3: BaseAgent (foundation cho mọi debater)

**Files:**
- Create: `core/agents/base_agent.py`
- Create: `tests/unit/test_base_agent.py`

- [ ] **Step 3.1: Write failing test**

```python
# tests/unit/test_base_agent.py
from core.agents.base_agent import BaseAgent
from unittest.mock import MagicMock


def test_base_agent_speak_calls_llm():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "Tôi đồng ý phương án A vì..."
    
    agent = BaseAgent(
        name_vn="Test Agent",
        role="tester",
        system_prompt="Bạn là chuyên viên test.",
        llm=mock_llm,
    )
    
    response = agent.speak(
        brief="Test brief",
        brain_context={"strategy": "..."},
        history=[],
    )
    
    assert "đồng ý" in response
    mock_llm.complete.assert_called_once()


def test_base_agent_includes_brain_in_prompt():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "ok"
    
    agent = BaseAgent(name_vn="A", role="r", system_prompt="sys", llm=mock_llm)
    agent.speak(brief="b", brain_context={"strategy": "VN"}, history=[])
    
    # Verify brain_context được inject
    call_args = mock_llm.complete.call_args
    messages = call_args[0][0] if call_args[0] else call_args.kwargs["messages"]
    full_text = str(messages)
    assert "VN" in full_text
```

- [ ] **Step 3.2: Implement**

```python
# core/agents/base_agent.py
"""BaseAgent — foundation cho mọi agent (department member, debater, ...)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol


class LLM(Protocol):
    def complete(self, messages: list[dict], model: str | None = None) -> str:
        ...


@dataclass
class BaseAgent:
    name_vn: str
    role: str
    system_prompt: str
    llm: LLM
    department: str = ""
    expertise: list[str] = field(default_factory=list)
    required_refs: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    model_override: str | None = None
    temperature: float = 0.7
    
    def build_messages(
        self,
        brief: str,
        brain_context: dict,
        history: list[str],
        extra_context: str = "",
    ) -> list[dict]:
        """Compose messages cho LLM call."""
        sys_parts = [
            self.system_prompt,
            "",
            "## DỮ LIỆU DOANH NGHIỆP (Brain context):",
            f"```yaml\n{self._format_brain(brain_context)}\n```",
        ]
        if extra_context:
            sys_parts.append("\n## NGỮ CẢNH BỔ SUNG:\n" + extra_context)
        
        user_parts = [f"## NHIỆM VỤ\n{brief}"]
        if history:
            user_parts.append("\n## TRANSCRIPT TRƯỚC ĐÓ\n" + "\n".join(history))
        user_parts.append("\n## YÊU CẦU\nPhát biểu góc nhìn của bạn (tiếng Việt, có dẫn nguồn Brain).")
        
        return [
            {"role": "system", "content": "\n".join(sys_parts)},
            {"role": "user", "content": "\n".join(user_parts)},
        ]
    
    @staticmethod
    def _format_brain(ctx: dict) -> str:
        import yaml
        return yaml.safe_dump(ctx, allow_unicode=True, sort_keys=False, width=120)
    
    def speak(
        self,
        brief: str,
        brain_context: dict,
        history: list[str],
        extra_context: str = "",
    ) -> str:
        messages = self.build_messages(brief, brain_context, history, extra_context)
        return self.llm.complete(messages, model=self.model_override)
```

- [ ] **Step 3.3: Run + commit**

```bash
pytest tests/unit/test_base_agent.py -v
git add core/agents/base_agent.py tests/unit/test_base_agent.py
git commit -m "feat(agents): add BaseAgent with brain-aware message builder"
```

---

### Task 4: Pro / Con Advocate (replaces Bull/Bear Researcher)

**Files:**
- Create: `core/agents/pro_advocate.py`
- Create: `core/agents/con_advocate.py`
- Create: `tests/unit/test_advocates.py`

- [ ] **Step 4.1: Write failing test**

```python
# tests/unit/test_advocates.py
from unittest.mock import MagicMock
from core.agents.pro_advocate import ProAdvocate
from core.agents.con_advocate import ConAdvocate
from core.meeting.debate_state import new_meeting_state


def test_pro_advocate_pushes_for_action():
    mock_llm = MagicMock(complete=MagicMock(return_value="Đề xuất triển khai."))
    pro = ProAdvocate(llm=mock_llm)
    state = new_meeting_state(brief="Launch X", departments=[])
    state["perspectives"] = {"07-marketing": "OK", "03-finance": "Risky"}
    
    output = pro.run(state)
    assert "triển khai" in output["pro_con_debate"]["pro_history"][-1]
    assert output["pro_con_debate"]["latest_speaker"] == "pro"


def test_con_advocate_raises_concerns():
    mock_llm = MagicMock(complete=MagicMock(return_value="Cảnh báo rủi ro."))
    con = ConAdvocate(llm=mock_llm)
    state = new_meeting_state(brief="Launch X", departments=[])
    state["pro_con_debate"]["pro_history"] = ["Pro nói: GO"]
    
    output = con.run(state)
    assert "rủi ro" in output["pro_con_debate"]["con_history"][-1].lower()
    assert output["pro_con_debate"]["count"] == 1   # round counter incremented after Con
```

- [ ] **Step 4.2: Implement Pro Advocate**

```python
# core/agents/pro_advocate.py
"""Pro Advocate — phe đẩy mạnh, đề xuất hành động.

Adapted from TradingAgents bull_researcher.py với neutral naming.
"""
from __future__ import annotations
from core.agents.base_agent import BaseAgent
from core.meeting.debate_state import MeetingState

PRO_SYSTEM_PROMPT = """Bạn là Pro Advocate (phe đẩy mạnh) trong cuộc họp ban điều hành DN VN.

## Vai trò
- Tổng hợp các góc nhìn phòng ban
- Đề xuất HÀNH ĐỘNG triển khai
- Chỉ ra cơ hội, lợi thế, đường thắng
- ĐỐI ĐẦU với Con Advocate (phản biện)

## Nguyên tắc
- LUÔN dẫn nguồn Brain (strategy.md, products.md, budget.md, ...)
- KHÔNG nói chung chung — phải kèm số liệu cụ thể
- Phản bác lập luận Con Advocate ở các round sau (đọc con_history)
- Tiếng Việt 100%, định nghĩa thuật ngữ nếu dùng (CAC, ROAS, ...)
"""


class ProAdvocate:
    def __init__(self, llm):
        self.agent = BaseAgent(
            name_vn="Pro Advocate",
            role="pro_advocate",
            system_prompt=PRO_SYSTEM_PROMPT,
            llm=llm,
            temperature=0.6,
        )
    
    def run(self, state: MeetingState) -> dict:
        debate = state["pro_con_debate"]
        history_text = []
        for p in debate["pro_history"]:
            history_text.append(f"[Pro round trước]: {p}")
        for c in debate["con_history"]:
            history_text.append(f"[Con phản biện]: {c}")
        
        perspectives_text = "\n".join(
            f"- {dept}: {persp[:300]}..." for dept, persp in state["perspectives"].items()
        )
        extra = f"## GÓC NHÌN PHÒNG BAN (round 1)\n{perspectives_text}"
        
        response = self.agent.speak(
            brief=state["brief"],
            brain_context=state["brain_context"],
            history=history_text,
            extra_context=extra,
        )
        
        return {
            "pro_con_debate": {
                **debate,
                "pro_history": debate["pro_history"] + [response],
                "history": debate["history"] + [f"PRO: {response}"],
                "latest_speaker": "pro",
            }
        }
```

- [ ] **Step 4.3: Implement Con Advocate**

```python
# core/agents/con_advocate.py
"""Con Advocate — phe phản biện, chỉ ra rủi ro."""
from __future__ import annotations
from core.agents.base_agent import BaseAgent
from core.meeting.debate_state import MeetingState

CON_SYSTEM_PROMPT = """Bạn là Con Advocate (phe phản biện) trong cuộc họp ban điều hành DN VN.

## Vai trò
- Tổng hợp các góc nhìn phòng ban
- Chỉ ra RỦI RO, LỖ HỔNG, scenarios xấu
- Phản biện đề xuất của Pro Advocate
- Bảo vệ DN khỏi quyết định liều lĩnh

## Nguyên tắc
- LUÔN dẫn nguồn Brain
- Số liệu cụ thể, không nói chung
- Phản biện trực tiếp pro_history (đọc kỹ Pro nói gì rồi mới counter)
- Tiếng Việt 100%, định nghĩa thuật ngữ
"""


class ConAdvocate:
    def __init__(self, llm):
        self.agent = BaseAgent(
            name_vn="Con Advocate",
            role="con_advocate",
            system_prompt=CON_SYSTEM_PROMPT,
            llm=llm,
            temperature=0.6,
        )
    
    def run(self, state: MeetingState) -> dict:
        debate = state["pro_con_debate"]
        history_text = []
        for p in debate["pro_history"]:
            history_text.append(f"[Pro lập luận]: {p}")
        for c in debate["con_history"]:
            history_text.append(f"[Con round trước]: {c}")
        
        perspectives_text = "\n".join(
            f"- {dept}: {persp[:300]}..." for dept, persp in state["perspectives"].items()
        )
        extra = f"## GÓC NHÌN PHÒNG BAN\n{perspectives_text}"
        
        response = self.agent.speak(
            brief=state["brief"],
            brain_context=state["brain_context"],
            history=history_text,
            extra_context=extra,
        )
        
        return {
            "pro_con_debate": {
                **debate,
                "con_history": debate["con_history"] + [response],
                "history": debate["history"] + [f"CON: {response}"],
                "latest_speaker": "con",
                "count": debate["count"] + 1,   # increment AFTER con (1 round = pro+con)
            }
        }
```

- [ ] **Step 4.4: Run + commit**

```bash
pytest tests/unit/test_advocates.py -v
git add core/agents/pro_advocate.py core/agents/con_advocate.py tests/unit/test_advocates.py
git commit -m "feat(agents): add Pro/Con Advocate (was Bull/Bear, neutral naming)"
```

---

### Task 5: Perspective Debators (3 góc nhìn)

**Files:**
- Create: `core/agents/perspective_debators.py`
- Create: `tests/unit/test_perspective_debators.py`

- [ ] **Step 5.1: Write failing test**

```python
# tests/unit/test_perspective_debators.py
from unittest.mock import MagicMock
from core.agents.perspective_debators import (
    GrowthDebator, CautiousDebator, BalancedDebator,
)
from core.meeting.debate_state import new_meeting_state


def test_growth_debator_appends_to_history():
    llm = MagicMock(complete=MagicMock(return_value="GO bold"))
    g = GrowthDebator(llm=llm)
    state = new_meeting_state(brief="x", departments=[])
    state["pro_con_debate"]["history"] = ["PRO: ...", "CON: ..."]
    out = g.run(state)
    assert "GO" in out["perspective_debate"]["growth_history"][-1]


def test_cautious_debator_speaks_after_growth():
    llm = MagicMock(complete=MagicMock(return_value="Hold gates first"))
    c = CautiousDebator(llm=llm)
    state = new_meeting_state(brief="x", departments=[])
    state["perspective_debate"]["growth_history"] = ["GO bold"]
    out = c.run(state)
    assert "Hold" in out["perspective_debate"]["cautious_history"][-1]


def test_balanced_debator_synthesizes():
    llm = MagicMock(complete=MagicMock(return_value="Pilot 4 weeks"))
    b = BalancedDebator(llm=llm)
    state = new_meeting_state(brief="x", departments=[])
    state["perspective_debate"]["growth_history"] = ["GO bold"]
    state["perspective_debate"]["cautious_history"] = ["Hold"]
    out = b.run(state)
    assert "Pilot" in out["perspective_debate"]["balanced_history"][-1]
    assert out["perspective_debate"]["count"] == 1
```

- [ ] **Step 5.2: Implement**

```python
# core/agents/perspective_debators.py
"""3 perspective debators: Growth / Cautious / Balanced.

Adapted from TradingAgents risk_mgmt/{aggressive,conservative,neutral}_debator.py
với neutral naming (no "risk" leak).
"""
from __future__ import annotations
from core.agents.base_agent import BaseAgent
from core.meeting.debate_state import MeetingState


GROWTH_PROMPT = """Bạn là phía TĂNG TRƯỞNG (Growth) trong họp DN VN.
Nhiệm vụ: Bảo vệ phương án táo bạo nhất, ưu tiên scale, chấp nhận rủi ro lớn để có upside cao.
Bám số liệu Brain. Tiếng Việt. Định nghĩa thuật ngữ."""

CAUTIOUS_PROMPT = """Bạn là phía THẬN TRỌNG (Cautious) trong họp DN VN.
Nhiệm vụ: Bảo vệ vốn, scenario xấu, gates cụ thể (pause/kill conditions).
Bám số liệu Brain. Tiếng Việt. Định nghĩa thuật ngữ."""

BALANCED_PROMPT = """Bạn là phía CÂN BẰNG (Balanced) trong họp DN VN.
Nhiệm vụ: Tổng hợp Growth + Cautious thành phương án trung dung khả thi.
Bám số liệu Brain. Tiếng Việt. Định nghĩa thuật ngữ."""


def _build_extra(state: MeetingState) -> str:
    pc = state["pro_con_debate"]
    pd = state["perspective_debate"]
    parts = ["## TRANSCRIPT PRO/CON\n" + "\n".join(pc["history"])]
    if pd["growth_history"]:
        parts.append("## GROWTH ĐÃ NÓI\n" + "\n".join(pd["growth_history"]))
    if pd["cautious_history"]:
        parts.append("## CAUTIOUS ĐÃ NÓI\n" + "\n".join(pd["cautious_history"]))
    if pd["balanced_history"]:
        parts.append("## BALANCED ĐÃ NÓI\n" + "\n".join(pd["balanced_history"]))
    return "\n\n".join(parts)


class GrowthDebator:
    def __init__(self, llm):
        self.agent = BaseAgent(name_vn="Growth", role="growth", system_prompt=GROWTH_PROMPT, llm=llm)
    
    def run(self, state: MeetingState) -> dict:
        resp = self.agent.speak(
            brief=state["brief"], brain_context=state["brain_context"],
            history=[], extra_context=_build_extra(state),
        )
        pd = state["perspective_debate"]
        return {"perspective_debate": {
            **pd,
            "growth_history": pd["growth_history"] + [resp],
            "history": pd["history"] + [f"GROWTH: {resp}"],
            "latest_speaker": "growth",
        }}


class CautiousDebator:
    def __init__(self, llm):
        self.agent = BaseAgent(name_vn="Cautious", role="cautious", system_prompt=CAUTIOUS_PROMPT, llm=llm)
    
    def run(self, state: MeetingState) -> dict:
        resp = self.agent.speak(
            brief=state["brief"], brain_context=state["brain_context"],
            history=[], extra_context=_build_extra(state),
        )
        pd = state["perspective_debate"]
        return {"perspective_debate": {
            **pd,
            "cautious_history": pd["cautious_history"] + [resp],
            "history": pd["history"] + [f"CAUTIOUS: {resp}"],
            "latest_speaker": "cautious",
        }}


class BalancedDebator:
    def __init__(self, llm):
        self.agent = BaseAgent(name_vn="Balanced", role="balanced", system_prompt=BALANCED_PROMPT, llm=llm)
    
    def run(self, state: MeetingState) -> dict:
        resp = self.agent.speak(
            brief=state["brief"], brain_context=state["brain_context"],
            history=[], extra_context=_build_extra(state),
        )
        pd = state["perspective_debate"]
        return {"perspective_debate": {
            **pd,
            "balanced_history": pd["balanced_history"] + [resp],
            "history": pd["history"] + [f"BALANCED: {resp}"],
            "latest_speaker": "balanced",
            "count": pd["count"] + 1,    # 1 round = growth+cautious+balanced
        }}
```

- [ ] **Step 5.3: Run + commit**

```bash
pytest tests/unit/test_perspective_debators.py -v
git add core/agents/perspective_debators.py tests/unit/test_perspective_debators.py
git commit -m "feat(agents): add Growth/Cautious/Balanced perspective debators"
```

---

### Task 6: Conditional logic (debate routing)

**Files:**
- Create: `core/meeting/conditional_logic.py`
- Create: `tests/unit/test_conditional_logic.py`

- [ ] **Step 6.1: Write failing test**

```python
# tests/unit/test_conditional_logic.py
from core.meeting.conditional_logic import (
    next_pro_con_node, next_perspective_node,
)
from core.meeting.debate_state import new_meeting_state


def test_pro_con_alternates():
    state = new_meeting_state(brief="x", departments=[], max_rounds=2)
    
    state["pro_con_debate"]["latest_speaker"] = None
    assert next_pro_con_node(state) == "pro"
    
    state["pro_con_debate"]["latest_speaker"] = "pro"
    assert next_pro_con_node(state) == "con"
    
    state["pro_con_debate"]["latest_speaker"] = "con"
    state["pro_con_debate"]["count"] = 1
    assert next_pro_con_node(state) == "pro"   # next round
    
    state["pro_con_debate"]["count"] = 2
    state["pro_con_debate"]["latest_speaker"] = "con"
    assert next_pro_con_node(state) == "perspective_phase"   # done


def test_perspective_cycles_growth_cautious_balanced():
    state = new_meeting_state(brief="x", departments=[])
    
    state["perspective_debate"]["latest_speaker"] = None
    assert next_perspective_node(state) == "growth"
    
    state["perspective_debate"]["latest_speaker"] = "growth"
    assert next_perspective_node(state) == "cautious"
    
    state["perspective_debate"]["latest_speaker"] = "cautious"
    assert next_perspective_node(state) == "balanced"
    
    state["perspective_debate"]["latest_speaker"] = "balanced"
    state["perspective_debate"]["count"] = 1
    state["max_perspective_debate_rounds"] = 1
    assert next_perspective_node(state) == "synthesizer"   # done
```

- [ ] **Step 6.2: Implement**

```python
# core/meeting/conditional_logic.py
"""LangGraph routing logic — quyết định node kế tiếp dựa state.

Adapted from TradingAgents/graph/conditional_logic.py với neutral naming.
"""
from __future__ import annotations
from core.meeting.debate_state import MeetingState


def next_pro_con_node(state: MeetingState) -> str:
    """Sau Pro hoặc Con node, decide node kế tiếp."""
    debate = state["pro_con_debate"]
    max_rounds = state["max_debate_rounds"]
    
    if debate["count"] >= max_rounds:
        return "perspective_phase"
    
    speaker = debate["latest_speaker"]
    if speaker is None or speaker == "con":
        return "pro"
    return "con"


def next_perspective_node(state: MeetingState) -> str:
    """Cycle growth → cautious → balanced. Sau N round → synthesizer."""
    pd = state["perspective_debate"]
    max_rounds = state["max_perspective_debate_rounds"]
    
    if pd["count"] >= max_rounds:
        return "synthesizer"
    
    speaker = pd["latest_speaker"]
    if speaker is None:
        return "growth"
    if speaker == "growth":
        return "cautious"
    if speaker == "cautious":
        return "balanced"
    # speaker == "balanced" → check round count, increment đã ở agent
    if pd["count"] >= max_rounds:
        return "synthesizer"
    return "growth"   # next round
```

- [ ] **Step 6.3: Run + commit**

```bash
pytest tests/unit/test_conditional_logic.py -v
git add core/meeting/conditional_logic.py tests/unit/test_conditional_logic.py
git commit -m "feat(meeting): add conditional logic for pro/con + perspective routing"
```

---

### Task 7: Synthesizer (was: Portfolio Manager)

**Files:**
- Create: `core/meeting/synthesizer.py`
- Create: `tests/unit/test_synthesizer.py`

- [ ] **Step 7.1: Write failing test**

```python
# tests/unit/test_synthesizer.py
from unittest.mock import MagicMock
from core.meeting.synthesizer import Synthesizer
from core.meeting.debate_state import new_meeting_state


def test_synthesizer_writes_final_report():
    llm = MagicMock(complete=MagicMock(return_value=(
        "## 📌 Tóm lại\nGO with revised scope.\n\n## Chi tiết\n..."
    )))
    syn = Synthesizer(llm=llm)
    state = new_meeting_state(brief="Launch", departments=["07-marketing"])
    state["perspectives"] = {"07-marketing": "OK"}
    state["pro_con_debate"]["history"] = ["PRO: GO", "CON: Risk"]
    state["perspective_debate"]["history"] = ["GROWTH: bold", "CAUTIOUS: hold", "BALANCED: pilot"]
    
    out = syn.run(state)
    assert out["final_report"] is not None
    assert "Tóm lại" in out["final_report"]
```

- [ ] **Step 7.2: Implement**

```python
# core/meeting/synthesizer.py
"""Synthesizer — tổng hợp toàn meeting → decision report cho CEO.

Adapted from TradingAgents/agents/managers/portfolio_manager.py với:
- Domain-neutral output
- RULE 4 enforce: TL;DR + định nghĩa thuật ngữ
- RULE 5 enforce: cite research findings
"""
from __future__ import annotations
from core.agents.base_agent import BaseAgent
from core.meeting.debate_state import MeetingState

SYNTHESIZER_PROMPT = """Bạn là người tổng hợp họp DN, viết báo cáo quyết định cho CEO.

## Output BẮT BUỘC theo format:

```markdown
# Báo cáo quyết định: <task>

## 📌 Tóm lại (đọc 30 giây)
- [3-5 dòng dân thường hiểu, đọc xong là biết nên làm gì]

## Khuyến nghị
[GO / GO with revisions / NO-GO / NEED_MORE_INFO]

## Điều chỉnh từ brief gốc (nếu có)
| Item | Brief gốc | Khuyến nghị | Lý do |
| ... |

## Phân tích chi tiết

### Mỗi phòng nói gì
[Tổng hợp perspectives]

### Tranh luận Pro vs Con
[Highlight key arguments]

### 3 góc nhìn (Growth/Cautious/Balanced)
[Summary]

## Việc cần làm trước khi triển khai (BLOCKERS)
[Checklist]

## KPI gates
[Cụ thể: tuần X nếu Y < Z thì pause]

## Câu hỏi cần CEO quyết
[A/B/C/D]
```

## Nguyên tắc (BẮT BUỘC)
- 🔒 RULE 4: Định nghĩa MỌI thuật ngữ chuyên ngành lần đầu xuất hiện
- 🔒 RULE 5: Cite mọi nhận định (Brain file:line, hoặc research source URL)
- Tiếng Việt 100%, đọc xong là CEO hiểu, không cần Google
- TL;DR phải đứng đầu, dân thường đọc 30 giây hiểu
"""


class Synthesizer:
    def __init__(self, llm):
        self.agent = BaseAgent(
            name_vn="Synthesizer",
            role="synthesizer",
            system_prompt=SYNTHESIZER_PROMPT,
            llm=llm,
            temperature=0.4,    # cần precise hơn
        )
    
    def run(self, state: MeetingState) -> dict:
        perspectives_text = "\n\n".join(
            f"### {dept}\n{persp}" for dept, persp in state["perspectives"].items()
        )
        pc_text = "\n".join(state["pro_con_debate"]["history"])
        pd_text = "\n".join(state["perspective_debate"]["history"])
        research_text = ""
        if state.get("research_findings"):
            research_text = "## RESEARCH\n" + str(state["research_findings"])[:3000]
        
        extra = (
            f"## GÓC NHÌN PHÒNG BAN\n{perspectives_text}\n\n"
            f"## PRO vs CON\n{pc_text}\n\n"
            f"## PERSPECTIVE DEBATE\n{pd_text}\n\n"
            f"{research_text}"
        )
        
        report = self.agent.speak(
            brief=state["brief"],
            brain_context=state["brain_context"],
            history=[],
            extra_context=extra,
        )
        return {"final_report": report}
```

- [ ] **Step 7.3: Run + commit**

```bash
pytest tests/unit/test_synthesizer.py -v
git add core/meeting/synthesizer.py tests/unit/test_synthesizer.py
git commit -m "feat(meeting): add Synthesizer (was Portfolio Manager) with TL;DR enforcement"
```

---

### Task 8: Meeting graph (LangGraph orchestrator)

**Files:**
- Create: `core/meeting/meeting_graph.py`
- Create: `core/meeting/checkpointer.py`
- Create: `tests/integration/test_meeting_graph.py`

- [ ] **Step 8.1: Implement checkpointer**

```python
# core/meeting/checkpointer.py
"""SQLite checkpointer cho LangGraph state persistence.

Adapted from TradingAgents/graph/checkpointer.py.
"""
from __future__ import annotations
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3


def make_checkpointer(db_path: Path | None = None) -> SqliteSaver:
    if db_path is None:
        db_path = Path.home() / ".vn-business-os" / "checkpoints.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return SqliteSaver(conn)
```

- [ ] **Step 8.2: Implement meeting graph**

```python
# core/meeting/meeting_graph.py
"""LangGraph orchestrator — toàn bộ meeting flow.

Adapted from TradingAgents/graph/trading_graph.py với neutral naming.
"""
from __future__ import annotations
from typing import Any, Callable
from langgraph.graph import StateGraph, END
from core.meeting.debate_state import MeetingState
from core.meeting.conditional_logic import next_pro_con_node, next_perspective_node
from core.meeting.synthesizer import Synthesizer
from core.meeting.checkpointer import make_checkpointer
from core.agents.pro_advocate import ProAdvocate
from core.agents.con_advocate import ConAdvocate
from core.agents.perspective_debators import (
    GrowthDebator, CautiousDebator, BalancedDebator,
)


class MeetingGraph:
    """Build + run LangGraph meeting flow.
    
    Flow:
      perspectives_collector → pro_con_loop → perspective_loop → synthesizer → END
    """
    
    def __init__(
        self,
        llm,
        perspectives_collector: Callable[[MeetingState], dict],
    ):
        """
        perspectives_collector: function nhận state, trả {"perspectives": {...}}.
        Sẽ implement Phase 3 từ DepartmentLoader.
        """
        self.llm = llm
        self.perspectives_collector = perspectives_collector
        self.pro = ProAdvocate(llm)
        self.con = ConAdvocate(llm)
        self.growth = GrowthDebator(llm)
        self.cautious = CautiousDebator(llm)
        self.balanced = BalancedDebator(llm)
        self.synthesizer = Synthesizer(llm)
    
    def build(self):
        graph = StateGraph(MeetingState)
        
        graph.add_node("perspectives", self.perspectives_collector)
        graph.add_node("pro", self.pro.run)
        graph.add_node("con", self.con.run)
        graph.add_node("growth", self.growth.run)
        graph.add_node("cautious", self.cautious.run)
        graph.add_node("balanced", self.balanced.run)
        graph.add_node("synthesizer", self.synthesizer.run)
        
        graph.set_entry_point("perspectives")
        graph.add_edge("perspectives", "pro")
        
        graph.add_conditional_edges("pro", next_pro_con_node, {
            "con": "con", "perspective_phase": "growth",
        })
        graph.add_conditional_edges("con", next_pro_con_node, {
            "pro": "pro", "perspective_phase": "growth",
        })
        graph.add_conditional_edges("growth", next_perspective_node, {
            "cautious": "cautious", "synthesizer": "synthesizer",
        })
        graph.add_conditional_edges("cautious", next_perspective_node, {
            "balanced": "balanced", "synthesizer": "synthesizer",
        })
        graph.add_conditional_edges("balanced", next_perspective_node, {
            "growth": "growth", "synthesizer": "synthesizer",
        })
        graph.add_edge("synthesizer", END)
        
        return graph.compile(checkpointer=make_checkpointer())
    
    def invoke(self, state: MeetingState, config: dict | None = None) -> MeetingState:
        cfg = config or {"configurable": {"thread_id": state.get("task_id", "default")}}
        return self.build().invoke(state, config=cfg)
```

- [ ] **Step 8.3: Write integration test (mocked LLM)**

```python
# tests/integration/test_meeting_graph.py
from unittest.mock import MagicMock
from core.meeting.meeting_graph import MeetingGraph
from core.meeting.debate_state import new_meeting_state


def test_meeting_runs_end_to_end_mocked():
    """Run full graph với mocked LLM (no API call)."""
    
    # LLM trả response khác nhau theo prompt content
    def fake_complete(messages, model=None):
        sys = messages[0]["content"]
        if "Pro Advocate" in sys:
            return "GO. Cơ hội rõ ràng."
        if "Con Advocate" in sys:
            return "Cảnh báo rủi ro X."
        if "TĂNG TRƯỞNG" in sys:
            return "Triển khai mạnh."
        if "THẬN TRỌNG" in sys:
            return "Có gates rõ."
        if "CÂN BẰNG" in sys:
            return "Pilot 4 tuần."
        if "tổng hợp" in sys.lower() or "Synthesizer" in sys:
            return "## 📌 Tóm lại\nGO with revisions.\n\n## Chi tiết\n..."
        return "..."
    
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = fake_complete
    
    def mock_perspectives(state):
        return {"perspectives": {
            "07-marketing": "Đề xuất triển khai",
            "03-finance": "Cẩn thận ngân sách",
        }}
    
    graph = MeetingGraph(llm=mock_llm, perspectives_collector=mock_perspectives)
    
    state = new_meeting_state(
        brief="Test campaign",
        departments=["07-marketing", "03-finance"],
        max_rounds=1,
        task_id="test-001",
    )
    
    result = graph.invoke(state)
    
    assert result["perspectives"]["07-marketing"] == "Đề xuất triển khai"
    assert len(result["pro_con_debate"]["pro_history"]) >= 1
    assert len(result["pro_con_debate"]["con_history"]) >= 1
    assert len(result["perspective_debate"]["growth_history"]) >= 1
    assert result["final_report"] is not None
    assert "Tóm lại" in result["final_report"]
```

- [ ] **Step 8.4: Run + commit**

```bash
pytest tests/integration/test_meeting_graph.py -v
git add core/meeting/meeting_graph.py core/meeting/checkpointer.py tests/integration/test_meeting_graph.py
git commit -m "feat(meeting): add LangGraph meeting orchestrator + SQLite checkpointer"
git tag phase-02-complete
```

---

## Phase 2 Done When

- [x] MeetingState (TypedDict) với Pro/Con + Perspective neutral naming
- [x] BaseAgent với brain-aware message builder
- [x] ProAdvocate + ConAdvocate (was Bull/Bear)
- [x] Growth/Cautious/Balanced debators (was risk_mgmt)
- [x] Conditional logic routing pro↔con + growth→cautious→balanced
- [x] Synthesizer xuất TL;DR + định nghĩa thuật ngữ
- [x] LangGraph compiled, SQLite checkpoint work
- [x] Mocked end-to-end test pass
- [x] Domain-neutral check: grep `bull|bear|trade|ticker|market|portfolio` trong `core/` → 0 match
