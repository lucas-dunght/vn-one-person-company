"""LLM quyết định tool nào cần chạy cho task."""
from __future__ import annotations
import json
import re
from typing import TypedDict


class ToolCall(TypedDict):
    tool: str
    queries: list[str]


ROUTER_PROMPT = """Bạn là Tool Router. Quyết định tool nào cần chạy cho task DN VN.

## Tools available
- web_search: general web search
- vn_law_search: luật/nghị định/thông tư VN
- vn_local_regulation: quy định địa phương VN (tỉnh/TP)
- competitor_research: đối thủ cạnh tranh ngành VN
- industry_benchmark: KPI ngành VN (saas_b2b, ecommerce_d2c_vn, restaurant_casual_vn, retail_offline_vn)
- tax_calculator: tính VAT/TNCN/TNDN/NTT (cần con số cụ thể)

## Output JSON BẮT BUỘC
```json
{
  "tools": [
    {"tool": "<name>", "queries": ["<q1>", ...]}
  ]
}
```

## Nguyên tắc
- Brief có claim/quảng cáo → vn_law_search
- Brief có địa phương cụ thể → vn_local_regulation (kèm province)
- Brief có competitor reference hoặc cần định vị → competitor_research
- Brief có metric/KPI → industry_benchmark
- Brief có số tiền/thuế → tax_calculator
- KHÔNG run tool nào nếu Brain đủ
- Tối đa 4 tools/task
"""


class ToolRouter:
    def __init__(self, llm):
        self.llm = llm

    def plan(self, brief: str, brain_summary: str) -> list[ToolCall]:
        messages = [
            {"role": "system", "content": ROUTER_PROMPT},
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
        data = json.loads(m.group(0))
        return data.get("tools", [])
