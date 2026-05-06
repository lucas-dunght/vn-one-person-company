# Decisions + Rules — VN Business OS

> Tất cả quyết định + nguyên tắc đã chốt trong session brainstorm 2026-05-05 → 2026-05-06.

---

## 🎯 5 Decisions chính (đã chốt với CEO)

### Decision 1 — Setup approach
**A + B (Hybrid open-source repo)**
- Clone repo → tự setup manual, **HOẶC**
- Clone repo → chạy wizard onboarding hỏi 30 câu

→ Repo public, hỗ trợ cả dev rành tech và CEO non-tech.

### Decision 2 — Bộ phòng ban
**A + B + D (Core + Industry packs + On-demand creator)**
- 13 phòng core (theo business-builder.plugin)
- Industry packs cho ngành đặc thù
- Cơ chế "tuyển agent mới" trong runtime khi phát hiện thiếu chuyên môn

### Decision 3 — MVP v1 scope
**C — Core 13 + 3 industry packs**
- Pack F&B (quán ăn / cafe / nhà hàng)
- Pack Retail (shop / e-commerce / D2C)
- Pack Tech-SaaS (startup phần mềm)

→ Sau v1, mở rộng các pack: Real Estate, Healthcare, Education, Beauty, Auto, Construction.

### Decision 4 — Mức độ tự động
**B — Semi-auto + Context-aware Clarification**
- Đọc Brain TRƯỚC khi hỏi CEO
- Hỏi đúng gap, có citation Brain
- 2 điểm dừng: Stop 1 (decision report duyệt), Stop 2 (execution duyệt)

### Decision 5 — Lưu trữ
**B — Local + Git private**
- Vault Obsidian local trên máy CEO
- Auto-commit (KHÔNG auto-push) lên Github private
- `.gitignore` chuẩn loại file nhạy cảm

### Decision 6 — Stack thực thi (bonus)
**D — Hybrid: Python+LangGraph + Obsidian + multi-tool adapters**
- Bóc engine debate từ TradingAgents (rename neutral)
- Tự code phần Brain / Clarifier / Tools / Translator
- Multi-tool entry: Claude Code + Cowork (v1) → Codex + Antigravity (v2)

### Decision 7 — Test case v1 (bonus)
**B + sau đó A + C — Chiến dịch QC nhắm khách thu nhập 50tr+**
- v1 chỉ ship test case B (debate flow đầy đủ)
- v1.1 thêm A (onboarding flow) + C (simple JD/contract)

### Decision 8 — Vị trí repo (bonus, 2026-05-06)
**`F:\OneDrive - www.KeyBanQuyen.VN\Documents\GitHub\26. One Company`**

---

## 🔒 6 RULES bất di bất dịch (enforce trong code)

### RULE 1 — Brain-first clarification
> KHÔNG hỏi CEO khi chưa đọc Brain. Mỗi câu hỏi PHẢI dẫn nguồn Brain (file:section).
> Nếu Brain đủ → KHÔNG hỏi, vào router luôn.

**Enforce:** `core/clarifier/question_generator.py` — `if not gaps: return []`.

### RULE 2 — Domain-neutral engine
> Code copy từ TradingAgents PHẢI rename toàn bộ. Không để trade/finance/market/ticker/Bull/Bear leak.

**Cụ thể rename:**
- `trading_graph.py` → `meeting_graph.py`
- `Bull/Bear Researcher` → `Pro/Con Advocate`
- `risk_debators` → `perspective_debators` (tăng trưởng / thận trọng / cân bằng)
- `Portfolio Manager` → `Decision Synthesizer`
- Bỏ `yfinance`, `Alpha Vantage`, `dataflows/`

**Enforce:** `scripts/dev/check-domain-neutral.sh` chạy trong CI.

### RULE 3 — Single source of truth (Obsidian)
> Obsidian vault là sự thật. SQLite chỉ cache phục hồi crash. Code KHÔNG lưu state ở chỗ thứ 3.

### RULE 4 — CEO-friendly language
> Mọi output cho CEO PHẢI:
> 1. Tiếng Việt 100%
> 2. Định nghĩa thuật ngữ lần đầu (vd: `**ROAS** (tỷ lệ doanh thu / chi phí ads, vd chi 1tr thu 4tr → ROAS=4x)`)
> 3. Có TL;DR đầu báo cáo (3-5 dòng dân thường đọc 30 giây hiểu)
> 4. Tránh từ chuyên ngành nếu có từ thường tương đương (lead → khách quan tâm, churn → khách rời bỏ)

**Enforce:** `core/translator/pipeline.py` (jargon detector → simplifier → TL;DR).

### RULE 5 — Live research with citations
> Agent có quyền search:
> - Luật VN (luật, nghị định, thông tư) — `vn_law_search`
> - Quy định địa phương — `vn_local_regulation`
> - Đối thủ cạnh tranh — `competitor_research`
> - Benchmark ngành VN — `industry_benchmark`
> - Tin tức general — `web_search`
> - Thuế VN (VAT, TNCN, TNDN, NTT) — `tax_calculator`
>
> PHẢI cite nguồn (URL + ngày truy cập). Cache 24h.

**Enforce:** `core/tools/base_tool.py` — `ToolResult.sources: list[str]` + `retrieved_at`.

### RULE 6 — BYOT (Bring Your Own Templates)
> DN có thể đưa template riêng vào vault. Thứ tự ưu tiên:
> 1. `vault/00-Templates-Custom/<dept>/` (DN custom — cao nhất)
> 2. `vault/01-Departments/<dept>/refs/` (pack templates)
> 3. `repo/templates-vn/<dept>/` (191 default từ bb-plugin — thấp nhất)
>
> Hỗ trợ: `.md`, `.docx`, `.xlsx`. PDF tuỳ chọn.

**Enforce:** `core/obsidian/template_resolver.py` — check 3 paths theo đúng thứ tự.

---

## 📊 Summary table

| # | Decision | Chốt |
|---|---|---|
| 1 | Setup | A+B Hybrid (manual + wizard) |
| 2 | Phòng ban | Core 13 + Packs + On-demand |
| 3 | MVP packs | F&B + Retail + Tech-SaaS |
| 4 | Auto level | Semi-auto + Brain-first clarification |
| 5 | Storage | Local + Git private |
| 6 | Stack | Python+LangGraph + Obsidian + multi-adapter |
| 7 | Test case | B (chiến dịch QC) cho v1 |
| 8 | Location | `F:\...\26. One Company` |

---

## ❓ Open questions (chờ CEO trả lời lúc impl)

1. **LLM provider mặc định v1** — Claude Sonnet 4.6 hardcode hay cho user chọn lúc onboard?
2. **Web search API** — Tavily (free tier 1000/mo) hay Serper ($1/1000)?
3. **Vietnamese spell-check (pyvi)** — v1 hay v1.1?
4. **BYOT có hỗ trợ PDF + OCR ngay v1?** — hay chỉ md/docx/xlsx?
5. **Auto-commit Git** — bật mặc định hay opt-in qua config?
6. **Glossary auto-grow** — bật mặc định hay manual approve mỗi term?
7. **CI cost với LLM thật** — dùng cassette/recording (VCR) hay mock thuần?
