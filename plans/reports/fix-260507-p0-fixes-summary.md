# Báo cáo Fix P0 — 2026-05-07

> **Trả lời cho user:** Đã check toàn bộ repo + fix 7 lỗi P0. Tests 180 pass. Commit `a3a7638`.

---

## Lỗi user nêu — đã xác minh

### ❌ "Setup vault không hỏi Tavily/Brave API key"
**ĐÚNG.** `core/onboard.py` cũ không có chỗ nhập API key. `.vncoderc` schema không có field key. CLI wizard `scripts/onboard.py` chỉ hỏi pack + BYOT.

→ **Đã fix:**
- `onboard_vault(api_keys={...})` param mới
- CLI wizard hỏi `TAVILY_API_KEY` + `ANTHROPIC_API_KEY` (password input)
- MCP tool `vn_onboard` thêm 4 params: `tavily_api_key`, `anthropic_api_key`, `google_api_key`, `openai_api_key`
- Save vào `<vault>/.env` (auto add `.env` vào `.gitignore`)

### ❌ "Search functionality không hoạt động"
**ĐÚNG MỘT PHẦN:**
- Search ĐÃ wired vào `vn_meeting` (gọi `ResearchPhase.run()` trước meeting)
- NHƯNG 4 Tavily tools (web/luật/địa phương/đối thủ) gặp lỗi auth khi không có key → caught silently → meeting tiếp tục với findings rỗng → RULE 5 vi phạm thầm lặng
- 2 tools không cần key (`industry_benchmark`, `tax_calculator`) vẫn work

→ **Đã fix:**
- 4 Tavily tools có `is_available()` check
- Khi thiếu key: trả về `ToolResult(data={"skipped": True}, notes="Thiếu TAVILY_API_KEY...")` thay vì crash
- ToolRouter chỉ plan tools có credentials (không lãng phí LLM tokens)
- `vn_status` báo `tools_live` + `tools_skipped` để CEO biết trước

---

## 15 bugs phát hiện trong audit (xem `audit-260507-repo-completeness.md`)

### P0 (7 bugs) — ĐÃ FIX trong commit này

| # | File | Bug | Fix |
|---|---|---|---|
| 1 | `flow_controller.py:167` | `departments_root` trỏ REPO thay vì vault → BYOT meeting broken | Đổi thành `vault.root / "01-Departments"` |
| 2 | `flow_controller.py:approve_decision` | Stub "(TODO Phase 6)" | LLM-generated execution plan thật, có tasks/risks/KPIs/templates table |
| 3 | `flow_controller.py:execute` | Stub README placeholder | Parse template table → TemplateResolver → DocWriter render .docx/.xlsx → save vào `03-Outputs/` |
| 4 | 4 Tavily tools | Crash khi thiếu key, silent failure | `is_available()` + `skipped_result()` graceful |
| 5 | `core/onboard.py` | Không hỏi API keys | `api_keys` param mới + save vào `<vault>/.env` |
| 6 | `core/install_mcp.py` | Không inject env vào mcpServers | `--vault` flag đọc `<vault>/.env` → inject `env: {TAVILY_API_KEY: ...}` |
| 7 | `tool_router.py` | Plan tools không credential | `available_tools` filter |

### P1 (5 bugs) — Pending phase tiếp theo

- `PerspectivesCollector` ignores per-agent enriched prompts (vẫn dùng generic template)
- 12 dept dirs nhưng plan/router prompt nói "13 core" — off-by-one
- `MCPSamplingProvider` không retry/timeout trên rate limit
- LangGraph `checkpointer=False` hardcoded → crash mid-meeting unrecoverable
- `GitSync` swallow exceptions silently

### P2 (3 bugs) — Polish sau

- Multi-turn `vn_onboard` qua MCP elicitation
- Router JSON-mode cho deterministic parse
- `tool_cache.db` per-vault (hiện là `~/.vn-business-os/`)

---

## Files thay đổi (38 files, +11148 lines)

### Code
- `core/utils/config.py` — `load_vault_env`, `save_vault_env`, `apply_vault_env_to_os`
- `core/tools/base_tool.py` — `is_available()` + `skipped_result()` helpers
- `core/tools/{web_search,vn_law_search,vn_local_regulation,competitor_research}.py` — graceful skip
- `core/tools/tool_router.py` — filter by available_tools
- `core/orchestrator/research_phase.py` — `list_available_tools` / `list_skipped_tools`
- `core/orchestrator/flow_controller.py` — departments_root + approve_decision + execute (real impl)
- `core/orchestrator/execution_planner.py` — NEW (LLM generates 08-execution-plan.md)
- `core/orchestrator/document_executor.py` — NEW (DocWriter + TemplateResolver wired)
- `core/onboard.py` — api_keys param
- `core/mcp_server.py` — vn_onboard 4 key params, vn_status tool availability, _make_fc auto-load env
- `core/install_mcp.py` — vault_path env injection
- `core/cli.py` — install-mcp --vault flag
- `scripts/onboard.py` — interactive API key prompts (password input)

### Tests (+34 mới)
- `tests/unit/test_env_and_tool_skip.py` — 11 tests
- `tests/unit/test_execution_planner.py` — 9 tests
- `tests/unit/test_document_executor.py` — 9 tests
- `tests/unit/test_install_mcp.py` — 2 mới (env injection)
- `tests/e2e/test_b_campaign_high_income.py` — 4 mới + mock updates

---

## Cách dùng (cập nhật)

### Setup vault mới (qua Claude Desktop)
```
Trong chat: "Setup vault cho công ty XYZ tại đường dẫn F:/.../my-company.
Cài pack F&B. Tavily API key của tôi: tvly-xxx"
```
→ Claude gọi `vn_onboard(vault=..., packs=["fnb"], tavily_api_key="tvly-xxx")`
→ Key save vào `<vault>/.env`, `.gitignore` exclude file

### Sau onboard, inject env vào MCP server
**Bước quan trọng:** sau khi save key, phải re-install MCP để Claude Desktop launch với env:
```bash
vn-os install-mcp --vault "F:/.../my-company"
```
→ Đọc `<vault>/.env` → inject `env: {TAVILY_API_KEY: ...}` vào `claude_desktop_config.json`
→ Restart Claude Desktop

### Verify
Trong chat: "vn_status vault F:/.../my-company"
→ Trả về `tools_live: [web_search, vn_law_search, ...]` (nếu có key)
→ Hoặc `tools_skipped: [{name: web_search, reason: Missing TAVILY_API_KEY}]` nếu thiếu

---

## Tests

**Trước:** 146 passed + 1 skipped
**Sau:** 180 passed + 1 skipped (+34 mới, 0 regression)

```
$ python -m pytest tests/ -q
180 passed, 1 skipped in 14.33s
```

---

## RULES Compliance Matrix (cập nhật sau fix)

| RULE | Trước | Sau |
|---|---|---|
| 1. Brain-first | ✓ | ✓ |
| 2. Domain-neutral | ✓ | ✓ |
| 3. Single source of truth | Partial | ✓ (departments từ vault) |
| 4. CEO-friendly language | Partial | Partial (P1.6) |
| 5. Live research with citations | **DEGRADED** | ✓ (graceful skip + status report) |
| 6. BYOT | **BROKEN** | ✓ (meeting + execute đều respect vault) |

---

## Bước tiếp theo cho user

1. **Restart Claude Desktop** để load MCP server mới (8 tools với fixes)
2. **Test setup vault mới** với syntax: "Setup vault... TAVILY key của tôi là..."
3. **Re-install MCP với --vault** để env inject:
   ```
   vn-os install-mcp --vault "F:/path/to/vault"
   ```
4. **Verify với vn_status** xem `tools_live` có bao nhiêu

## Pending (P1 + P2 — phase tiếp theo)

Xem `audit-260507-repo-completeness.md` section "Priority Fix List". Có thể mở phase-07 để dọn nốt:
- Per-agent prompts wiring vào PerspectivesCollector
- 13th department resolution
- Retry/timeout trong MCPSamplingProvider
- Re-enable LangGraph checkpointer
- Multi-turn onboard qua MCP elicitation
- Citation validator
