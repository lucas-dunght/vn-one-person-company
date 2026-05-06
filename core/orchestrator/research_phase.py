"""Run tools parallel sau clarification, trước meeting."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core.tools.tool_router import ToolRouter, ToolCall
from core.tools.web_search import WebSearch
from core.tools.vn_law_search import VNLawSearch
from core.tools.vn_local_regulation import VNLocalRegulation
from core.tools.competitor_research import CompetitorResearch
from core.tools.industry_benchmark import IndustryBenchmark
from core.tools.tax_calculator import TaxCalculator


TOOL_REGISTRY = {
    "web_search": WebSearch,
    "vn_law_search": VNLawSearch,
    "vn_local_regulation": VNLocalRegulation,
    "competitor_research": CompetitorResearch,
    "industry_benchmark": IndustryBenchmark,
    "tax_calculator": TaxCalculator,
}


class ResearchPhase:
    def __init__(self, llm):
        self.tool_router = ToolRouter(llm)

    def run(self, brief: str, brain_summary: str, task_folder: Path) -> dict:
        plan = self.tool_router.plan(brief, brain_summary)
        results: dict[str, list] = {}

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {}
            for call in plan:
                tool_name = call["tool"]
                tool_cls = TOOL_REGISTRY.get(tool_name)
                if not tool_cls:
                    continue
                tool = tool_cls()
                for q in call.get("queries", []):
                    futures[ex.submit(tool.run, q)] = (tool_name, q)

            for fut, (tool_name, q) in futures.items():
                try:
                    r = fut.result()
                    results.setdefault(tool_name, []).append({
                        "query": q, "data": r.data,
                        "sources": r.sources, "retrieved_at": r.retrieved_at,
                    })
                except Exception as e:
                    results.setdefault(tool_name, []).append({
                        "query": q, "error": str(e),
                    })

        self._write_findings(task_folder, plan, results)
        return results

    def _write_findings(self, folder: Path, plan: list[ToolCall], results: dict):
        parts = ["---", "type: research_findings", "---", "", "# Research findings", ""]
        for tool_name, calls in results.items():
            parts.append(f"## {tool_name}")
            for c in calls:
                parts.append(f"\n### Query: `{c['query']}`")
                if "error" in c:
                    parts.append(f"Error: {c['error']}")
                else:
                    parts.append(f"**Data:**\n```yaml\n{c['data']}\n```")
                    parts.append(f"**Sources:** {', '.join(c.get('sources', []))}")
                    parts.append(f"**Retrieved:** {c.get('retrieved_at', '?')}")
        (folder / "03b-research-findings.md").write_text(
            "\n".join(parts), encoding="utf-8"
        )
