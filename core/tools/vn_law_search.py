"""Search luật/nghị định/thông tư VN — restrict trusted sites."""
from __future__ import annotations
import os
from pathlib import Path
from core.tools.base_tool import BaseTool, ToolResult
from core.tools.tool_cache import ToolCache


TRUSTED_DOMAINS = [
    "thuvienphapluat.vn",
    "luatvietnam.vn",
    "vbpl.vn",
    "moj.gov.vn",
    "chinhphu.vn",
]


class VNLawSearch(BaseTool):
    name = "vn_law_search"
    description = "Tìm luật/nghị định/thông tư VN."

    def __init__(self, api_key: str | None = None, cache_path: Path | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.cache = ToolCache(
            cache_path or Path.home() / ".vn-business-os" / "tool_cache.db",
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def run(self, query: str, **kwargs) -> ToolResult:
        if not self.is_available():
            return self.skipped_result(
                "Thiếu TAVILY_API_KEY — không tra được luật/nghị định online"
            )

        cache_hit = self.cache.get(query, source=self.name)
        if cache_hit:
            return ToolResult(data=cache_hit, sources=cache_hit.get("urls", []),
                              cached=True, notes="cache hit")

        try:
            from tavily import TavilyClient
        except ImportError:
            return self.skipped_result("Package 'tavily-python' chưa cài")

        client = TavilyClient(api_key=self.api_key)
        resp = client.search(
            query=query, max_results=8,
            include_answer=True,
            include_domains=TRUSTED_DOMAINS,
        )
        urls = [r["url"] for r in resp.get("results", [])]
        data = {
            "answer": resp.get("answer", ""),
            "results": resp.get("results", []),
            "urls": urls,
        }
        self.cache.set(query, data, source=self.name)
        return ToolResult(data=data, sources=urls)
