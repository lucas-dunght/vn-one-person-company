"""LLM quyết định tool nào cần chạy cho task."""
from __future__ import annotations
import json
import re
from typing import TypedDict


class ToolCall(TypedDict):
    tool: str
    queries: list[str]


ROUTER_PROMPT_TEMPLATE = """Bạn là Tool Router. Quyết định tool nào cần chạy cho task DN VN.

## Tools available (đã filter — chỉ tools có credentials)
{tools_list}

## Output JSON BẮT BUỘC
```json
{{
  "tools": [
    {{"tool": "<name>", "queries": ["<q1>", ...]}}
  ]
}}
```

## Nguyên tắc
- Brief có claim/quảng cáo → vn_law_search (nếu available)
- Brief có địa phương cụ thể → vn_local_regulation (nếu available, kèm province trong query)
- Brief có competitor reference hoặc cần định vị → competitor_research (nếu available)
- Brief có metric/KPI → industry_benchmark
- Brief có số tiền/thuế → tax_calculator
- KHÔNG run tool nào nếu Brain đủ
- Tối đa 4 tools/task
- CHỈ chọn tool TRONG DANH SÁCH AVAILABLE phía trên
"""


_FULL_TOOL_DESCRIPTIONS = {
    "web_search": "general web search (cần TAVILY_API_KEY)",
    "vn_law_search": "luật/nghị định/thông tư VN (cần TAVILY_API_KEY)",
    "vn_local_regulation": "quy định địa phương VN (cần TAVILY_API_KEY)",
    "competitor_research": "đối thủ cạnh tranh ngành VN (cần TAVILY_API_KEY)",
    "industry_benchmark": "KPI ngành VN (saas_b2b, ecommerce_d2c_vn, restaurant_casual_vn, retail_offline_vn)",
    "tax_calculator": "tính VAT/TNCN/TNDN/NTT (cần con số cụ thể)",
}


class ToolRouter:
    def __init__(self, llm, available_tools: list[str] | None = None):
        """
        Args:
            llm: LLM provider
            available_tools: Tool names được phép plan. Nếu None → all 6 (legacy).
                            Caller (ResearchPhase) inject filtered list dựa trên
                            BaseTool.is_available() để Router không plan tool sẽ skip.
        """
        self.llm = llm
        self.available_tools = available_tools

    def _build_prompt(self) -> str:
        names = self.available_tools or list(_FULL_TOOL_DESCRIPTIONS.keys())
        lines = []
        for n in names:
            desc = _FULL_TOOL_DESCRIPTIONS.get(n, "(no description)")
            lines.append(f"- {n}: {desc}")
        return ROUTER_PROMPT_TEMPLATE.format(tools_list="\n".join(lines))

    def plan(self, brief: str, brain_summary: str) -> list[ToolCall]:
        if self.available_tools is not None and not self.available_tools:
            # Không có tool nào credentialed — skip planning entirely.
            return []

        messages = [
            {"role": "system", "content": self._build_prompt()},
            {"role": "user", "content": (
                f"## BRIEF\n{brief}\n\n"
                f"## BRAIN SUMMARY\n{brain_summary[:2000]}\n\n"
                "Output JSON tool plan."
            )},
        ]
        raw = self.llm.complete(messages)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
        plan = data.get("tools", [])
        # Defensive filter: drop tools không trong available list
        if self.available_tools is not None:
            plan = [t for t in plan if t.get("tool") in self.available_tools]
        return plan
