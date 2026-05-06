from unittest.mock import MagicMock
import json
from core.tools.tool_router import ToolRouter


def test_decides_tools_from_brief():
    fake = json.dumps({
        "tools": [
            {"tool": "vn_law_search", "queries": ["luật quảng cáo"]},
            {"tool": "competitor_research", "queries": ["SaaS VN"]},
            {"tool": "industry_benchmark", "queries": ["saas_b2b cac"]},
        ]
    })
    llm = MagicMock(complete=MagicMock(return_value=fake))

    router = ToolRouter(llm=llm)
    plan = router.plan(brief="Tạo chiến dịch QC SaaS B2B", brain_summary="...")

    tools = [p["tool"] for p in plan]
    assert "vn_law_search" in tools
    assert "competitor_research" in tools
