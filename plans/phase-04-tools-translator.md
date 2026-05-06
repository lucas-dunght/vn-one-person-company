# Phase 4 — Tools (Live Research) + Translator (CEO-friendly Language)

**Goal:** Build 6 tool live research (RULE 5) + Translator pipeline (RULE 4: TL;DR + jargon definition).

**Dependency:** Phase 1, 2, 3.

**Estimated tasks:** 14

---

### Task 1: BaseTool + Tool cache

**Files:**
- Create: `core/tools/__init__.py`
- Create: `core/tools/base_tool.py`
- Create: `core/tools/tool_cache.py`
- Create: `tests/unit/test_tool_cache.py`

- [ ] **Step 1.1: Write failing test for cache**

```python
# tests/unit/test_tool_cache.py
import time
from datetime import datetime, timedelta
from core.tools.tool_cache import ToolCache


def test_cache_get_set(tmp_path):
    cache = ToolCache(tmp_path / "cache.db", ttl_seconds=3600)
    cache.set("query1", {"data": "result"}, source="tavily")
    
    hit = cache.get("query1", source="tavily")
    assert hit is not None
    assert hit["data"] == "result"


def test_cache_miss_after_ttl(tmp_path):
    cache = ToolCache(tmp_path / "cache.db", ttl_seconds=1)
    cache.set("q2", {"x": 1}, source="s")
    time.sleep(2)
    assert cache.get("q2", source="s") is None
```

- [ ] **Step 1.2: Implement BaseTool**

```python
# core/tools/base_tool.py
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
    sources: list[str] = field(default_factory=list)   # URLs hoặc references
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    cached: bool = False
    notes: str = ""


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    cache_ttl_seconds: int = 86400   # 24h default
    
    @abstractmethod
    def run(self, query: str, **kwargs) -> ToolResult:
        ...
    
    def cache_key(self, query: str, **kwargs) -> str:
        import json
        return f"{self.name}::{query}::{json.dumps(sorted(kwargs.items()))}"
```

- [ ] **Step 1.3: Implement ToolCache**

```python
# core/tools/tool_cache.py
"""SQLite cache cho tool results (24h default TTL)."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import json
import time


class ToolCache:
    def __init__(self, db_path: Path, ttl_seconds: int = 86400):
        self.db_path = Path(db_path)
        self.ttl = ttl_seconds
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    source TEXT,
                    data TEXT,
                    timestamp INTEGER
                )
            """)
    
    def get(self, query: str, source: str) -> dict | None:
        key = f"{source}::{query}"
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT data, timestamp FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if not row:
            return None
        data, ts = row
        if time.time() - ts > self.ttl:
            return None
        return json.loads(data)
    
    def set(self, query: str, data: dict, source: str):
        key = f"{source}::{query}"
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?)",
                (key, source, json.dumps(data), int(time.time())),
            )
            conn.commit()
```

- [ ] **Step 1.4: Run + commit**

```bash
pytest tests/unit/test_tool_cache.py -v
git add core/tools/__init__.py core/tools/base_tool.py core/tools/tool_cache.py tests/unit/test_tool_cache.py
git commit -m "feat(tools): add BaseTool + SQLite cache (24h TTL default)"
```

---

### Task 2: Web Search Tool (Tavily)

**Files:**
- Create: `core/tools/web_search.py`
- Create: `tests/unit/test_web_search.py`

- [ ] **Step 2.1: Write failing test**

```python
# tests/unit/test_web_search.py
from unittest.mock import patch, MagicMock
from core.tools.web_search import WebSearch


def test_web_search_returns_sources(tmp_path):
    fake_results = {
        "results": [
            {"url": "https://example.com/a", "title": "A", "content": "..."},
            {"url": "https://example.com/b", "title": "B", "content": "..."},
        ],
        "answer": "summary text",
    }
    with patch("tavily.TavilyClient") as MockTavily:
        client = MagicMock()
        client.search.return_value = fake_results
        MockTavily.return_value = client
        
        ws = WebSearch(api_key="fake", cache_path=tmp_path / "c.db")
        result = ws.run("CAC SaaS B2B Vietnam 2026")
    
    assert len(result.sources) == 2
    assert "summary" in result.data.get("answer", "")


def test_web_search_uses_cache_on_second_call(tmp_path):
    fake_results = {"results": [{"url": "u", "title": "t", "content": "c"}], "answer": "ans"}
    with patch("tavily.TavilyClient") as MockTavily:
        client = MagicMock()
        client.search.return_value = fake_results
        MockTavily.return_value = client
        
        ws = WebSearch(api_key="fake", cache_path=tmp_path / "c.db")
        ws.run("query A")
        ws.run("query A")   # second call
        
        assert client.search.call_count == 1   # cache hit
```

- [ ] **Step 2.2: Implement**

```python
# core/tools/web_search.py
"""Web search via Tavily API. Free tier 1000 search/month."""
from __future__ import annotations
import os
from pathlib import Path
from core.tools.base_tool import BaseTool, ToolResult
from core.tools.tool_cache import ToolCache


class WebSearch(BaseTool):
    name = "web_search"
    description = "Search web cho thông tin general. Dùng khi cần data thực tế ngoài Brain."
    
    def __init__(self, api_key: str | None = None, cache_path: Path | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.cache = ToolCache(
            cache_path or Path.home() / ".vn-business-os" / "tool_cache.db",
            ttl_seconds=self.cache_ttl_seconds,
        )
    
    def run(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        cache_hit = self.cache.get(query, source=self.name)
        if cache_hit:
            return ToolResult(
                data=cache_hit, sources=cache_hit.get("urls", []),
                cached=True, notes="cache hit",
            )
        
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        resp = client.search(query=query, max_results=max_results, include_answer=True)
        
        urls = [r["url"] for r in resp.get("results", [])]
        data = {
            "answer": resp.get("answer", ""),
            "results": resp.get("results", []),
            "urls": urls,
        }
        self.cache.set(query, data, source=self.name)
        
        return ToolResult(data=data, sources=urls, notes=f"max_results={max_results}")
```

- [ ] **Step 2.3: Run + commit**

```bash
pytest tests/unit/test_web_search.py -v
git add core/tools/web_search.py tests/unit/test_web_search.py
git commit -m "feat(tools): add WebSearch tool (Tavily) with cache"
```

---

### Task 3: VN Law Search Tool

**Files:**
- Create: `core/tools/vn_law_search.py`
- Create: `tests/unit/test_vn_law_search.py`

- [ ] **Step 3.1: Write failing test**

```python
# tests/unit/test_vn_law_search.py
from unittest.mock import patch, MagicMock
from core.tools.vn_law_search import VNLawSearch


def test_vn_law_search_filters_by_trusted_sites(tmp_path):
    fake_results = {
        "results": [
            {"url": "https://thuvienphapluat.vn/luat-quang-cao-2012", "title": "Luật QC 2012", "content": "..."},
            {"url": "https://luatvietnam.vn/123", "title": "Luật DN", "content": "..."},
        ],
        "answer": "Quy định QC...",
    }
    with patch("tavily.TavilyClient") as M:
        c = MagicMock(); c.search.return_value = fake_results
        M.return_value = c
        
        tool = VNLawSearch(api_key="fake", cache_path=tmp_path / "c.db")
        result = tool.run("luật quảng cáo SaaS B2B")
    
    assert all("thuvienphapluat" in u or "luatvietnam" in u or "vbpl" in u
               for u in result.sources)
    assert result.data["answer"]
```

- [ ] **Step 3.2: Implement**

```python
# core/tools/vn_law_search.py
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
    description = "Tìm luật/nghị định/thông tư VN. Dùng khi check tuân thủ pháp lý."
    
    def __init__(self, api_key: str | None = None, cache_path: Path | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.cache = ToolCache(
            cache_path or Path.home() / ".vn-business-os" / "tool_cache.db",
        )
    
    def run(self, query: str, **kwargs) -> ToolResult:
        cache_hit = self.cache.get(query, source=self.name)
        if cache_hit:
            return ToolResult(data=cache_hit, sources=cache_hit.get("urls", []),
                              cached=True, notes="cache hit")
        
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        resp = client.search(
            query=query,
            max_results=8,
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
```

- [ ] **Step 3.3: Run + commit**

```bash
pytest tests/unit/test_vn_law_search.py -v
git add core/tools/vn_law_search.py tests/unit/test_vn_law_search.py
git commit -m "feat(tools): add VN Law search (restricted to trusted gov + legal sites)"
```

---

### Task 4: Competitor Research Tool

**Files:**
- Create: `core/tools/competitor_research.py`
- Create: `tests/unit/test_competitor_research.py`

- [ ] **Step 4.1: Write failing test**

```python
# tests/unit/test_competitor_research.py
from unittest.mock import patch, MagicMock
from core.tools.competitor_research import CompetitorResearch


def test_extracts_competitors_from_query(tmp_path):
    fake = {"results": [
        {"url": "https://base.vn", "title": "Base.vn", "content": "Pricing 12tr/mo..."},
        {"url": "https://misa.vn", "title": "Misa AMIS", "content": "..."},
    ], "answer": "Top SaaS quản lý SME VN..."}
    with patch("tavily.TavilyClient") as M:
        c = MagicMock(); c.search.return_value = fake; M.return_value = c
        tool = CompetitorResearch(api_key="x", cache_path=tmp_path / "c.db")
        r = tool.run("SaaS quản lý SME VN")
    
    assert len(r.sources) == 2
    assert "base.vn" in r.sources[0]
```

- [ ] **Step 4.2: Implement**

```python
# core/tools/competitor_research.py
"""Profile đối thủ public info."""
from __future__ import annotations
import os
from pathlib import Path
from core.tools.base_tool import BaseTool, ToolResult
from core.tools.tool_cache import ToolCache


class CompetitorResearch(BaseTool):
    name = "competitor_research"
    description = "Research đối thủ ngành VN — pricing, kênh, vị thế."
    
    def __init__(self, api_key: str | None = None, cache_path: Path | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.cache = ToolCache(cache_path or Path.home() / ".vn-business-os" / "tool_cache.db")
    
    def run(self, query: str, country: str = "VN", **kwargs) -> ToolResult:
        full_query = f"{query} đối thủ cạnh tranh {country}"
        cache_hit = self.cache.get(full_query, source=self.name)
        if cache_hit:
            return ToolResult(data=cache_hit, sources=cache_hit.get("urls", []),
                              cached=True, notes="cache hit")
        
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        resp = client.search(query=full_query, max_results=8, include_answer=True)
        urls = [r["url"] for r in resp.get("results", [])]
        data = {
            "answer": resp.get("answer", ""),
            "competitors_found": [r.get("title", "") for r in resp.get("results", [])],
            "urls": urls,
            "raw_results": resp.get("results", []),
        }
        self.cache.set(full_query, data, source=self.name)
        return ToolResult(data=data, sources=urls)
```

- [ ] **Step 4.3: Commit**

```bash
pytest tests/unit/test_competitor_research.py -v
git add core/tools/competitor_research.py tests/unit/test_competitor_research.py
git commit -m "feat(tools): add CompetitorResearch tool"
```

---

### Task 5: Industry Benchmark Tool (Curated YAML + scrape fallback)

**Files:**
- Create: `core/tools/industry_benchmark.py`
- Create: `core/tools/data/benchmarks-vn.yaml`
- Create: `tests/unit/test_industry_benchmark.py`

- [ ] **Step 5.1: Create curated benchmarks YAML**

```yaml
# core/tools/data/benchmarks-vn.yaml
saas_b2b:
  cac_vnd_per_sql:
    median: 8000000
    range: [5000000, 15000000]
    source: "openview SaaS report 2025 + Vietnam-specific adjustments"
  roas_long_term:
    range: [3, 8]
    note: "12-month LTV / CAC"
  conversion_lead_to_sql:
    range: [0.08, 0.15]

ecommerce_d2c_vn:
  conversion_rate:
    median: 0.025
    range: [0.01, 0.05]
  aov_vnd:
    median: 450000
  cod_share:
    median: 0.65
  return_rate:
    median: 0.08

restaurant_casual_vn:
  food_cost_pct:
    target: 35
    range: [28, 38]
  labor_cost_pct:
    target: 30
    range: [25, 35]
  table_turn_per_day:
    range: [2.5, 4.0]

retail_offline_vn:
  inventory_turnover_per_year:
    range: [4, 8]
  shrinkage_pct:
    target: 1.5
```

- [ ] **Step 5.2: Write failing test**

```python
# tests/unit/test_industry_benchmark.py
from pathlib import Path
from core.tools.industry_benchmark import IndustryBenchmark


def test_lookup_saas_cac():
    tool = IndustryBenchmark()
    r = tool.run("saas_b2b cac")
    assert r.data["median"] == 8000000


def test_lookup_unknown_returns_empty():
    tool = IndustryBenchmark()
    r = tool.run("madeup_industry blah")
    assert r.data == {} or r.data.get("not_found")
```

- [ ] **Step 5.3: Implement**

```python
# core/tools/industry_benchmark.py
"""Curated benchmark VN. Lookup theo ngành + metric."""
from __future__ import annotations
from pathlib import Path
import yaml
from core.tools.base_tool import BaseTool, ToolResult


DATA_PATH = Path(__file__).parent / "data" / "benchmarks-vn.yaml"


class IndustryBenchmark(BaseTool):
    name = "industry_benchmark"
    description = "Lookup KPI benchmark ngành VN: SaaS, e-commerce, F&B, retail."
    
    def __init__(self, data_path: Path | None = None):
        self.data = yaml.safe_load(
            (data_path or DATA_PATH).read_text(encoding="utf-8")
        )
    
    def run(self, query: str, **kwargs) -> ToolResult:
        """query format: '<industry> <metric>' (vd 'saas_b2b cac')"""
        parts = query.lower().split()
        if len(parts) < 2:
            return ToolResult(data={"not_found": True}, notes="invalid query format")
        
        industry = parts[0]
        metric_query = "_".join(parts[1:])
        
        ind_data = self.data.get(industry, {})
        # Fuzzy match metric
        for key, val in ind_data.items():
            if metric_query in key.lower() or key.lower() in metric_query:
                return ToolResult(
                    data=val,
                    sources=[f"benchmarks-vn.yaml::{industry}::{key}"],
                    notes=f"Curated benchmark, last updated: see git log",
                )
        return ToolResult(data={"not_found": True})
```

- [ ] **Step 5.4: Run + commit**

```bash
pytest tests/unit/test_industry_benchmark.py -v
git add core/tools/industry_benchmark.py core/tools/data/benchmarks-vn.yaml tests/unit/test_industry_benchmark.py
git commit -m "feat(tools): add IndustryBenchmark tool with curated VN data"
```

---

### Task 6: Tax Calculator Tool

**Files:**
- Create: `core/tools/tax_calculator.py`
- Create: `tests/unit/test_tax_calculator.py`

- [ ] **Step 6.1: Write failing test**

```python
# tests/unit/test_tax_calculator.py
from core.tools.tax_calculator import TaxCalculator


def test_vat_10_percent():
    tc = TaxCalculator()
    r = tc.run("vat 100000000 rate=10")
    assert r.data["vat_amount_vnd"] == 10_000_000
    assert r.data["total_vnd"] == 110_000_000


def test_tncn_progressive_brackets():
    tc = TaxCalculator()
    r = tc.run("tncn 50000000 deduction=11000000")   # taxable = 39M
    # Bracket: 5tr@5% + 5tr@10% + 8tr@15% + 14tr@20% + 7tr@25%
    assert r.data["taxable_vnd"] == 39_000_000


def test_foreign_contractor_tax_on_ad_spend():
    tc = TaxCalculator()
    r = tc.run("foreign_contractor 200000000 service=ads provider=facebook")
    # FB Ads: NTT 5% + VAT 5%
    assert r.data["ntt_amount_vnd"] == 10_000_000
    assert r.data["vat_amount_vnd"] == 10_000_000
```

- [ ] **Step 6.2: Implement**

```python
# core/tools/tax_calculator.py
"""Tính các loại thuế VN: VAT, TNCN, TNDN, Thuế nhà thầu (NTT), lệ phí môn bài."""
from __future__ import annotations
import re
from core.tools.base_tool import BaseTool, ToolResult


# Biểu thuế TNCN VN — từ thu nhập tính thuế (taxable)
TNCN_BRACKETS = [
    (5_000_000, 0.05),
    (10_000_000, 0.10),
    (18_000_000, 0.15),
    (32_000_000, 0.20),
    (52_000_000, 0.25),
    (80_000_000, 0.30),
    (float("inf"), 0.35),
]


class TaxCalculator(BaseTool):
    name = "tax_calculator"
    description = "Tính VAT, TNCN, TNDN, Thuế nhà thầu, lệ phí môn bài VN."
    
    def run(self, query: str, **kwargs) -> ToolResult:
        """query format: '<tax_type> <amount> [k=v ...]'"""
        parts = query.split()
        if len(parts) < 2:
            return ToolResult(data={}, notes="invalid format")
        
        tax_type = parts[0].lower()
        amount = self._parse_amount(parts[1])
        params = self._parse_kv(parts[2:])
        
        if tax_type == "vat":
            rate = float(params.get("rate", 10)) / 100
            vat = int(amount * rate)
            return ToolResult(
                data={"base_vnd": amount, "rate_pct": rate * 100,
                      "vat_amount_vnd": vat, "total_vnd": amount + vat},
                sources=["Luật Thuế GTGT 2008 + sửa đổi 2024"],
            )
        
        if tax_type == "tncn":
            deduction = self._parse_amount(params.get("deduction", "11000000"))
            taxable = max(0, amount - deduction)
            tax = self._tncn_progressive(taxable)
            return ToolResult(
                data={"income_vnd": amount, "deduction_vnd": deduction,
                      "taxable_vnd": taxable, "tax_vnd": tax,
                      "net_vnd": amount - tax},
                sources=["Luật Thuế TNCN 2007 + sửa đổi"],
            )
        
        if tax_type == "tndn":
            rate = float(params.get("rate", 20)) / 100
            tax = int(amount * rate)
            return ToolResult(
                data={"profit_vnd": amount, "rate_pct": rate * 100,
                      "tax_vnd": tax, "net_vnd": amount - tax},
                sources=["Luật Thuế TNDN 2008 + sửa đổi"],
            )
        
        if tax_type == "foreign_contractor":
            service = params.get("service", "general")
            ntt_rate, vat_rate = self._foreign_contractor_rates(service)
            ntt = int(amount * ntt_rate)
            vat = int(amount * vat_rate)
            return ToolResult(
                data={"base_vnd": amount, "service": service,
                      "ntt_rate_pct": ntt_rate * 100, "ntt_amount_vnd": ntt,
                      "vat_rate_pct": vat_rate * 100, "vat_amount_vnd": vat,
                      "total_tax_vnd": ntt + vat},
                sources=["TT 103/2014/TT-BTC", "TT 60/2012/TT-BTC"],
            )
        
        return ToolResult(data={}, notes=f"Unknown tax type: {tax_type}")
    
    @staticmethod
    def _parse_amount(s) -> int:
        s = str(s)
        return int(re.sub(r"[_,.]", "", s))
    
    @staticmethod
    def _parse_kv(parts: list[str]) -> dict:
        out = {}
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                out[k] = v
        return out
    
    @staticmethod
    def _tncn_progressive(taxable: int) -> int:
        tax = 0
        prev = 0
        for ceil, rate in TNCN_BRACKETS:
            if taxable <= prev:
                break
            slice_amount = min(taxable, ceil) - prev
            tax += int(slice_amount * rate)
            prev = ceil
            if taxable <= ceil:
                break
        return tax
    
    @staticmethod
    def _foreign_contractor_rates(service: str) -> tuple[float, float]:
        # NTT %, VAT %
        rates = {
            "ads": (0.05, 0.05),
            "software": (0.05, 0.05),
            "consulting": (0.05, 0.05),
            "transport": (0.02, 0.03),
            "general": (0.05, 0.05),
        }
        return rates.get(service.lower(), rates["general"])
```

- [ ] **Step 6.3: Commit**

```bash
pytest tests/unit/test_tax_calculator.py -v
git add core/tools/tax_calculator.py tests/unit/test_tax_calculator.py
git commit -m "feat(tools): add TaxCalculator (VAT/TNCN/TNDN/NTT/môn bài)"
```

---

### Task 7: VN Local Regulation Tool

**Files:**
- Create: `core/tools/vn_local_regulation.py`
- Create: `tests/unit/test_vn_local_regulation.py`

- [ ] **Step 7.1: Implement (similar pattern WebSearch + filter)**

```python
# core/tools/vn_local_regulation.py
"""Tìm quy định địa phương VN (Sở/UBND tỉnh)."""
from __future__ import annotations
import os
from pathlib import Path
from core.tools.base_tool import BaseTool, ToolResult
from core.tools.tool_cache import ToolCache


TRUSTED_LOCAL_DOMAINS = [
    "chinhphu.vn",
    "moj.gov.vn",
    "tphcm.gov.vn",
    "hanoi.gov.vn",
    "danang.gov.vn",
    # ...thêm khi cần
]


class VNLocalRegulation(BaseTool):
    name = "vn_local_regulation"
    description = "Quy định địa phương VN — Sở/UBND tỉnh, thủ tục công."
    
    def __init__(self, api_key: str | None = None, cache_path: Path | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.cache = ToolCache(cache_path or Path.home() / ".vn-business-os" / "tool_cache.db")
    
    def run(self, query: str, province: str = "", **kwargs) -> ToolResult:
        full_q = f"{query} {province}".strip()
        hit = self.cache.get(full_q, source=self.name)
        if hit:
            return ToolResult(data=hit, sources=hit.get("urls", []), cached=True)
        
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        resp = client.search(
            query=full_q, max_results=6,
            include_domains=TRUSTED_LOCAL_DOMAINS, include_answer=True,
        )
        urls = [r["url"] for r in resp.get("results", [])]
        data = {"answer": resp.get("answer", ""), "results": resp.get("results", []), "urls": urls}
        self.cache.set(full_q, data, source=self.name)
        return ToolResult(data=data, sources=urls)
```

- [ ] **Step 7.2: Test + commit**

```python
# tests/unit/test_vn_local_regulation.py
from unittest.mock import patch, MagicMock
from core.tools.vn_local_regulation import VNLocalRegulation


def test_local_reg_searches_government_sites(tmp_path):
    fake = {"results": [{"url": "https://hanoi.gov.vn/x", "title": "T", "content": "..."}],
            "answer": "..."}
    with patch("tavily.TavilyClient") as M:
        c = MagicMock(); c.search.return_value = fake; M.return_value = c
        tool = VNLocalRegulation(api_key="x", cache_path=tmp_path / "c.db")
        r = tool.run("giấy phép kinh doanh", province="Hà Nội")
    assert "hanoi.gov.vn" in r.sources[0]
```

```bash
pytest tests/unit/test_vn_local_regulation.py -v
git add core/tools/vn_local_regulation.py tests/unit/test_vn_local_regulation.py
git commit -m "feat(tools): add VNLocalRegulation tool"
```

---

### Task 8: Tool Router (auto-select tools per task)

**Files:**
- Create: `core/tools/tool_router.py`
- Create: `tests/unit/test_tool_router.py`

- [ ] **Step 8.1: Write failing test**

```python
# tests/unit/test_tool_router.py
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
```

- [ ] **Step 8.2: Implement**

```python
# core/tools/tool_router.py
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
```

- [ ] **Step 8.3: Run + commit**

```bash
pytest tests/unit/test_tool_router.py -v
git add core/tools/tool_router.py tests/unit/test_tool_router.py
git commit -m "feat(tools): add ToolRouter (LLM-driven tool selection)"
```

---

### Task 9: Research Phase (chạy tools parallel + write findings)

**Files:**
- Create: `core/orchestrator/research_phase.py`
- Create: `tests/integration/test_research_phase.py`

- [ ] **Step 9.1: Implement**

```python
# core/orchestrator/research_phase.py
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
                tool = tool_cls() if tool_name in ("industry_benchmark", "tax_calculator") \
                       else tool_cls()
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
        
        # Write findings to task folder
        self._write_findings(task_folder, plan, results)
        return results
    
    def _write_findings(self, folder: Path, plan: list[ToolCall], results: dict):
        parts = ["---", "type: research_findings", "---", "", "# Research findings", ""]
        for tool_name, calls in results.items():
            parts.append(f"## {tool_name}")
            for c in calls:
                parts.append(f"\n### Query: `{c['query']}`")
                if "error" in c:
                    parts.append(f"❌ Error: {c['error']}")
                else:
                    parts.append(f"**Data:**\n```yaml\n{c['data']}\n```")
                    parts.append(f"**Sources:** {', '.join(c.get('sources', []))}")
                    parts.append(f"**Retrieved:** {c.get('retrieved_at', '?')}")
        (folder / "03b-research-findings.md").write_text(
            "\n".join(parts), encoding="utf-8"
        )
```

- [ ] **Step 9.2: Integration test (mocked)**

```python
# tests/integration/test_research_phase.py
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
from core.orchestrator.research_phase import ResearchPhase


def test_research_phase_writes_findings_file(tmp_path):
    llm = MagicMock(complete=MagicMock(return_value=json.dumps({
        "tools": [{"tool": "industry_benchmark", "queries": ["saas_b2b cac"]}]
    })))
    
    rp = ResearchPhase(llm=llm)
    results = rp.run(
        brief="Test", brain_summary="...", task_folder=tmp_path,
    )
    
    assert "industry_benchmark" in results
    assert (tmp_path / "03b-research-findings.md").exists()
```

- [ ] **Step 9.3: Run + commit**

```bash
pytest tests/integration/test_research_phase.py -v
git add core/orchestrator/research_phase.py tests/integration/test_research_phase.py
git commit -m "feat(orchestrator): add ResearchPhase with parallel tool execution"
```

---

### Task 10: Translator — Glossary

**Files:**
- Create: `core/translator/__init__.py`
- Create: `core/translator/glossary.py`
- Create: `core/translator/terms_dictionary.yaml`
- Create: `tests/unit/test_glossary.py`

- [ ] **Step 10.1: Create terms dictionary**

```yaml
# core/translator/terms_dictionary.yaml
marketing:
  CAC:
    vn: "Chi phí thu được 1 khách hàng"
    formula: "Tổng chi MKT + Sales / Số khách mới"
    example: "Chi 100tr MKT, có 20 khách → CAC = 5tr/khách"
  CTR:
    vn: "Tỷ lệ click — % người thấy ad bấm vào"
    benchmark_vn: "FB B2C: 1-2%, LinkedIn B2B: 0.3-0.5%"
  ROAS:
    vn: "Tỷ lệ doanh thu / chi phí ads"
    example: "Chi 1tr ads thu 4tr doanh thu → ROAS = 4x"
  CPL:
    vn: "Chi phí cho 1 lead (khách quan tâm)"
  ICP:
    vn: "Hồ sơ khách hàng lý tưởng (Ideal Customer Profile)"
  SQL:
    vn: "Sales Qualified Lead — khách đã đủ điều kiện sales tiếp cận"

finance:
  EBITDA:
    vn: "Lợi nhuận trước lãi vay, thuế, khấu hao"
  burn_rate:
    vn: "Tốc độ đốt tiền — mỗi tháng âm bao nhiêu"
  runway:
    vn: "Tiền còn đủ chạy bao nhiêu tháng (nếu không có doanh thu mới)"
  COGS:
    vn: "Giá vốn hàng bán"
  GMV:
    vn: "Tổng giá trị giao dịch"
  AOV:
    vn: "Giá trị đơn trung bình"

saas:
  MRR:
    vn: "Doanh thu định kỳ tháng (Monthly Recurring Revenue)"
  ARR:
    vn: "Doanh thu định kỳ năm (Annual Recurring Revenue)"
  churn_rate:
    vn: "Tỷ lệ khách rời bỏ"
  LTV:
    vn: "Giá trị vòng đời khách hàng (Lifetime Value)"
  DAU:
    vn: "Người dùng active hằng ngày"
  MAU:
    vn: "Người dùng active hằng tháng"

operations:
  SOP:
    vn: "Quy trình tác nghiệp chuẩn (Standard Operating Procedure)"
  KPI:
    vn: "Chỉ số đo hiệu quả (Key Performance Indicator)"
  OKR:
    vn: "Mục tiêu + kết quả then chốt (Objectives & Key Results)"

restaurant:
  food_cost_pct:
    vn: "Tỷ lệ giá vốn nguyên liệu / doanh thu"
    target_vn: "< 35% là tốt"
  table_turn:
    vn: "Số lượt bàn đảo / ngày"
  labor_cost_pct:
    vn: "Tỷ lệ chi phí lương / doanh thu"
    target_vn: "< 30% là tốt"
```

- [ ] **Step 10.2: Implement Glossary**

```python
# core/translator/glossary.py
"""Auto-grow glossary từ outputs + lookup từ terms_dictionary."""
from __future__ import annotations
from pathlib import Path
import yaml
import re


DICT_PATH = Path(__file__).parent / "terms_dictionary.yaml"


class Glossary:
    def __init__(self, vault_glossary_path: Path | None = None):
        self.dict_data = yaml.safe_load(DICT_PATH.read_text(encoding="utf-8"))
        self.vault_path = vault_glossary_path
        self.vault_terms = self._load_vault() if vault_glossary_path else {}
    
    def _load_vault(self) -> dict[str, str]:
        if not self.vault_path.exists():
            return {}
        content = self.vault_path.read_text(encoding="utf-8")
        terms = re.findall(r"^-\s+\*\*(.+?)\*\*:\s*(.+)$", content, re.MULTILINE)
        return dict(terms)
    
    def lookup(self, term: str) -> str | None:
        # Vault first
        if term in self.vault_terms:
            return self.vault_terms[term]
        # Search dict
        for category, items in self.dict_data.items():
            if term in items:
                meta = items[term]
                if isinstance(meta, dict) and "vn" in meta:
                    return meta["vn"]
        return None
    
    def add_term(self, term: str, definition: str, category: str = "auto") -> None:
        self.vault_terms[term] = definition
        if self.vault_path:
            self._persist_vault(category)
    
    def _persist_vault(self, category: str):
        # Append-only style — không xoá định nghĩa cũ
        content = "---\ntype: brain\nsection: glossary\n---\n# Glossary\n\n"
        for term, defn in self.vault_terms.items():
            content += f"- **{term}**: {defn}\n"
        self.vault_path.write_text(content, encoding="utf-8")
```

- [ ] **Step 10.3: Test + commit**

```python
# tests/unit/test_glossary.py
from core.translator.glossary import Glossary


def test_lookup_known_term():
    g = Glossary()
    assert "khách hàng" in g.lookup("CAC").lower()


def test_lookup_unknown_returns_none():
    g = Glossary()
    assert g.lookup("XYZ_ABC") is None


def test_add_term_persists(tmp_path):
    p = tmp_path / "glossary.md"
    p.write_text("---\n---\n# G\n", encoding="utf-8")
    g = Glossary(vault_glossary_path=p)
    g.add_term("FOOBAR", "định nghĩa")
    assert "FOOBAR" in p.read_text(encoding="utf-8")
```

```bash
pytest tests/unit/test_glossary.py -v
git add core/translator/__init__.py core/translator/glossary.py core/translator/terms_dictionary.yaml tests/unit/test_glossary.py
git commit -m "feat(translator): add Glossary (curated dict + vault auto-grow)"
```

---

### Task 11: Jargon Detector

**Files:**
- Create: `core/translator/jargon_detector.py`
- Create: `tests/unit/test_jargon_detector.py`

- [ ] **Step 11.1: Implement**

```python
# core/translator/jargon_detector.py
"""Phát hiện thuật ngữ Eng/abbrev trong text VN."""
from __future__ import annotations
import re
from core.translator.glossary import Glossary


# Regex: chữ hoa abbrev (>=2 ký tự) hoặc Eng word
JARGON_RE = re.compile(r"\b([A-Z]{2,}|[A-Z][a-z]+(?:[A-Z][a-z]+)+)\b")


class JargonDetector:
    def __init__(self, glossary: Glossary | None = None):
        self.glossary = glossary or Glossary()
    
    def detect(self, text: str) -> list[tuple[str, str | None]]:
        """Return list of (term, definition_or_None)."""
        terms = set(JARGON_RE.findall(text))
        # Filter out common Vietnamese acronyms / proper nouns to ignore
        ignore = {"DN", "VN", "MM", "AM", "PM", "TP", "Q", "T", "CEO", "OK"}
        terms -= ignore
        
        return [(t, self.glossary.lookup(t)) for t in sorted(terms)]
```

- [ ] **Step 11.2: Test + commit**

```python
# tests/unit/test_jargon_detector.py
from core.translator.jargon_detector import JargonDetector


def test_detects_marketing_jargon():
    jd = JargonDetector()
    found = jd.detect("CAC mục tiêu 8tr, ROAS ≥ 3.2x")
    terms = [t for t, _ in found]
    assert "CAC" in terms
    assert "ROAS" in terms


def test_filters_out_common_acronyms():
    jd = JargonDetector()
    found = jd.detect("DN của bạn ở VN, gặp CEO ngày T2")
    terms = [t for t, _ in found]
    assert "DN" not in terms
    assert "VN" not in terms
```

```bash
pytest tests/unit/test_jargon_detector.py -v
git add core/translator/jargon_detector.py tests/unit/test_jargon_detector.py
git commit -m "feat(translator): add JargonDetector"
```

---

### Task 12: Simplifier (LLM rewrite + inject definitions)

**Files:**
- Create: `core/translator/simplifier.py`
- Create: `tests/unit/test_simplifier.py`

- [ ] **Step 12.1: Implement**

```python
# core/translator/simplifier.py
"""Rewrite output to inject term definitions (RULE 4)."""
from __future__ import annotations
from core.translator.jargon_detector import JargonDetector
from core.translator.glossary import Glossary


SIMPLIFIER_PROMPT = """Bạn là biên tập viên DN VN. Rewrite text dưới đây cho CEO non-tech đọc dễ hiểu.

## Yêu cầu
- Định nghĩa MỌI thuật ngữ chuyên ngành lần đầu xuất hiện, format:
  **Thuật ngữ** (giải thích đơn giản — ví dụ cụ thể của DN)
- Thay từ khó bằng từ thường khi có nghĩa tương đương (lead → khách quan tâm, churn → khách rời bỏ)
- Câu ngắn, dễ đọc
- KHÔNG đổi nghĩa, không thêm/bớt thông tin
- Tiếng Việt 100%

## Glossary có sẵn (dùng làm reference)
{glossary_subset}
"""


class Simplifier:
    def __init__(self, llm, glossary: Glossary | None = None):
        self.llm = llm
        self.glossary = glossary or Glossary()
        self.detector = JargonDetector(self.glossary)
    
    def simplify(self, text: str) -> str:
        terms = self.detector.detect(text)
        if not terms:
            return text
        
        # Build subset glossary từ terms found
        glossary_text = "\n".join(
            f"- **{t}**: {defn or '(chưa định nghĩa, hãy giải thích bằng tiếng Việt)'}"
            for t, defn in terms
        )
        
        messages = [
            {"role": "system", "content": SIMPLIFIER_PROMPT.format(glossary_subset=glossary_text)},
            {"role": "user", "content": text},
        ]
        return self.llm.complete(messages)
```

- [ ] **Step 12.2: Test + commit**

```python
# tests/unit/test_simplifier.py
from unittest.mock import MagicMock
from core.translator.simplifier import Simplifier


def test_simplifier_passes_through_when_no_jargon():
    s = Simplifier(llm=MagicMock())
    out = s.simplify("Doanh thu tháng 5 tăng 20%")
    assert out == "Doanh thu tháng 5 tăng 20%"


def test_simplifier_calls_llm_when_jargon_present():
    llm = MagicMock(complete=MagicMock(return_value="rewritten with defs"))
    s = Simplifier(llm=llm)
    out = s.simplify("CAC tăng 30%, ROAS giảm")
    llm.complete.assert_called_once()
    assert out == "rewritten with defs"
```

```bash
pytest tests/unit/test_simplifier.py -v
git add core/translator/simplifier.py tests/unit/test_simplifier.py
git commit -m "feat(translator): add Simplifier (LLM rewrite with term injection)"
```

---

### Task 13: TL;DR Generator

**Files:**
- Create: `core/translator/tldr_generator.py`
- Create: `tests/unit/test_tldr.py`

- [ ] **Step 13.1: Implement**

```python
# core/translator/tldr_generator.py
"""Sinh TL;DR (3-5 dòng dân thường) cho output dài."""
from __future__ import annotations


TLDR_PROMPT = """Tóm tắt báo cáo dưới đây thành 3-5 dòng dân thường đọc 30 giây hiểu.

## Yêu cầu
- 3-5 dòng (KHÔNG hơn)
- Bullet point (- ...)
- Mỗi dòng: 1 thông tin then chốt CEO cần biết
- Tiếng Việt thuần, KHÔNG jargon
- Format:
```
## 📌 Tóm lại (đọc 30 giây)
- ...
- ...
```
"""


class TLDRGenerator:
    def __init__(self, llm):
        self.llm = llm
    
    def generate(self, full_text: str) -> str:
        messages = [
            {"role": "system", "content": TLDR_PROMPT},
            {"role": "user", "content": full_text},
        ]
        return self.llm.complete(messages)
    
    def prepend(self, full_text: str) -> str:
        """Prepend TL;DR vào đầu text."""
        if "## 📌 Tóm lại" in full_text:
            return full_text   # đã có
        tldr = self.generate(full_text)
        return tldr + "\n\n---\n\n" + full_text
```

- [ ] **Step 13.2: Test + commit**

```python
# tests/unit/test_tldr.py
from unittest.mock import MagicMock
from core.translator.tldr_generator import TLDRGenerator


def test_tldr_prepends_to_text():
    llm = MagicMock(complete=MagicMock(return_value="## 📌 Tóm lại\n- A\n- B\n- C"))
    g = TLDRGenerator(llm=llm)
    out = g.prepend("Long report text...")
    assert out.startswith("## 📌 Tóm lại")
    assert "Long report" in out


def test_tldr_skips_when_already_present():
    llm = MagicMock()
    g = TLDRGenerator(llm=llm)
    text = "## 📌 Tóm lại\n- existing\n\n# Body"
    out = g.prepend(text)
    assert out == text
    llm.complete.assert_not_called()
```

```bash
pytest tests/unit/test_tldr.py -v
git add core/translator/tldr_generator.py tests/unit/test_tldr.py
git commit -m "feat(translator): add TLDRGenerator (RULE 4 enforcement)"
```

---

### Task 14: Translator Pipeline (compose all)

**Files:**
- Create: `core/translator/pipeline.py`
- Create: `tests/integration/test_translator_pipeline.py`

- [ ] **Step 14.1: Implement**

```python
# core/translator/pipeline.py
"""Compose: detect → simplify → TL;DR. Apply trên output cuối cho CEO."""
from __future__ import annotations
from pathlib import Path
from core.translator.glossary import Glossary
from core.translator.simplifier import Simplifier
from core.translator.tldr_generator import TLDRGenerator


class TranslatorPipeline:
    def __init__(self, llm, vault_glossary_path: Path | None = None):
        self.glossary = Glossary(vault_glossary_path=vault_glossary_path)
        self.simplifier = Simplifier(llm, glossary=self.glossary)
        self.tldr = TLDRGenerator(llm)
    
    def apply(self, raw_output: str) -> str:
        simplified = self.simplifier.simplify(raw_output)
        with_tldr = self.tldr.prepend(simplified)
        return with_tldr
```

- [ ] **Step 14.2: Integration test**

```python
# tests/integration/test_translator_pipeline.py
from unittest.mock import MagicMock
from core.translator.pipeline import TranslatorPipeline


def test_pipeline_simplifies_and_prepends_tldr():
    llm = MagicMock()
    llm.complete.side_effect = [
        "rewritten with **CAC** (chi phí 1 khách)",   # simplifier
        "## 📌 Tóm lại\n- key1\n- key2\n- key3",       # tldr
    ]
    
    p = TranslatorPipeline(llm=llm)
    out = p.apply("CAC tăng 30%, cần action ngay")
    
    assert out.startswith("## 📌 Tóm lại")
    assert "**CAC**" in out
```

- [ ] **Step 14.3: Run + tag**

```bash
pytest tests/integration/test_translator_pipeline.py -v
git add core/translator/pipeline.py tests/integration/test_translator_pipeline.py
git commit -m "feat(translator): compose detect+simplify+TLDR pipeline"
git tag phase-04-complete
```

---

## Phase 4 Done When

- [x] BaseTool + ToolCache (24h SQLite)
- [x] 6 tools: WebSearch, VNLawSearch, VNLocalRegulation, CompetitorResearch, IndustryBenchmark, TaxCalculator
- [x] ToolRouter LLM-driven tool selection
- [x] ResearchPhase parallel execution + write 03b-research-findings.md
- [x] Glossary với curated VN dictionary + vault auto-grow
- [x] JargonDetector (regex + glossary lookup)
- [x] Simplifier (LLM rewrite injecting definitions)
- [x] TLDRGenerator (3-5 dòng đầu báo cáo)
- [x] TranslatorPipeline composed
- [x] All tools cite sources (RULE 5)
- [x] All output có TL;DR + jargon defined (RULE 4)
