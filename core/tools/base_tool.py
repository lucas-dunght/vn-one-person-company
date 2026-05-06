"""Base class cho mọi tool live research.

🔒 RULE 5: Mọi ToolResult PHẢI có sources + retrieved_at để cite.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ToolResult:
    data: Any
    sources: list[str] = field(default_factory=list)
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cached: bool = False
    notes: str = ""


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    cache_ttl_seconds: int = 86400

    @abstractmethod
    def run(self, query: str, **kwargs) -> ToolResult:
        ...

    def is_available(self) -> bool:
        """Check tool có credentials/dependencies cần thiết không.

        Default: True. Tools cần API key override để check key presence.
        """
        return True

    def skipped_result(self, reason: str) -> ToolResult:
        """Helper trả về ToolResult chỉ rõ tool đã skip vì lý do gì.

        Caller (ResearchPhase) thấy `data["skipped"]=True` thì biết tool không
        chạy thật, RULE 5 vẫn được respect (không silently violate).
        """
        return ToolResult(
            data={"skipped": True, "reason": reason},
            sources=[],
            notes=f"SKIPPED: {reason}",
        )

    def cache_key(self, query: str, **kwargs) -> str:
        import json
        return f"{self.name}::{query}::{json.dumps(sorted(kwargs.items()))}"
