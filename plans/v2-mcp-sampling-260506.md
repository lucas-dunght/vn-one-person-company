# v0.2.0 — MCP Sampling Architecture

> **Ngày ship:** 2026-05-06
> **Tag:** `v0.2.0` + `phase-07-mcp-sampling`
> **Goal:** Cho phép vn-business-os chạy qua Claude Desktop / Code subscription, KHÔNG cần ANTHROPIC_API_KEY

## Câu trả lời cho CEO

Trước câu hỏi: "Làm sao giữ 100% v1, chỉ thay LLM call mechanism dùng subscription?"

→ **MCP Sampling protocol**: MCP server không tự gọi LLM, mà request host (Claude Desktop) tạo completion. Host dùng subscription user → Anthropic. Trả response về server.

## Thay đổi: 4 files mới, 0 file core sửa

| File | Vai trò |
|---|---|
| `core/llm/providers.py` (extend) | `MCPSamplingProvider` class — route complete() qua MCP `session.create_message()` |
| `core/mcp_server.py` (mới) | FastMCP server expose 7 tools: vn_run, vn_resume, vn_meeting, vn_approve, vn_execute, vn_status, vn_onboard |
| `core/install_mcp.py` (mới) | Auto-edit Claude Desktop `claude_desktop_config.json` (cross-platform: Win/Mac/Linux) |
| `adapters/claude-code/skill.md` (rewrite) | Skill file dùng 7 MCP tools thay subprocess CLI |

## v1 code KHÔNG đổi

- `core/agents/` (BaseAgent, Department, Pro/Con, Perspective debators)
- `core/brain/` (Schema, Reader, Memory, GapAnalyzer)
- `core/clarifier/` (QuestionGenerator, ClarificationIO)
- `core/meeting/` (MeetingState, ConditionalLogic, Synthesizer, MeetingGraph với LangGraph)
- `core/obsidian/` (Vault, TemplateResolver, DocWriter, GitSync)
- `core/orchestrator/` (Router, FlowController, PerspectivesCollector, ResearchPhase)
- `core/tools/` (6 tools: web_search, vn_law, competitor, benchmark, tax, local_reg)
- `core/translator/` (Glossary, JargonDetector, Simplifier, TLDR, Pipeline)
- `core/cli.py` (CLI mode dùng API key vẫn work — fallback)

→ **103 v1 tests vẫn pass nguyên + 23 tests mới = 126 tests passing.**

## Cách hoạt động

```
User chat tiếng Việt trong Claude Desktop
  ↓
Skill `vn-business-os` activate
  ↓
Claude (subscription) gọi MCP tool: vn_run(brief, vault)
  ↓ qua MCP protocol
core/mcp_server.py:vn_run handler
  ↓ instantiate
FlowController(vault_root, llm=MCPSamplingProvider(ctx.session))
  ↓ run pipeline (Router, GapAnalyzer, ...)
  ↓ when LLM call needed:
LLMProvider.complete(messages)  →  MCPSamplingProvider.complete()
  ↓ async session.create_message()
  ↓ qua MCP protocol back to host
Claude Desktop (subscription)
  ↓ thinks
  ↓ returns response
back through stack to FlowController
  ↓ continues pipeline
  ↓ writes vault/02-Tasks/<ts>-<slug>/03-clarification.md
returns to MCP tool
  ↓ result dict back to Claude session
Claude shows CEO summary in Vietnamese
```

## CEO setup 1 lần

```bash
pip install vn-business-os         # hoặc pipx install vn-business-os
vn-os install-mcp                  # auto-edit claude_desktop_config.json
# Restart Claude Desktop
bash adapters/claude-code/install.sh    # cài skill (optional)
```

Sau đó: chat tiếng Việt tự nhiên trong Claude Desktop, skill auto-active.

## Caveats

1. **Subscription rate limit**: Pro ~45 msg/5h → 1 task COMPLEX/5h. Max ~225 msg/5h → 6-7 task/5h.
2. **Sampling support**: Claude Desktop ✅, Claude Code ✅, Claude.ai web ❌ (không có MCP).
3. **Latency**: +1-2s/call so với API trực tiếp (qua thêm 1 hop MCP).
4. **User approval**: Default Claude Desktop hỏi mỗi sampling. Bấm "Always allow" 1 lần.
5. **Model preference**: Server hint `claude-sonnet-4-6`, host có thể trả model khác.

## Effort

3-5 ngày FT-equivalent (đã làm trong 1 session ~6 giờ thực tế).

## Tests breakdown

| File | Tests | Phase |
|---|---|---|
| test_mcp_sampling_provider.py | 5 | T1 |
| test_mcp_server_tools.py | 5 | T2 |
| test_install_mcp.py | 8 | T3 |
| test_mcp_server_e2e.py | 5 | T5 |

Total v0.2.0 mới: **23 tests**.
Full suite: **126 passed + 1 skipped** (after T5).

## Resume / debug guide

Nếu session sau gặp lỗi MCP:

1. **Verify install**: `cat ~/.config/Claude/claude_desktop_config.json` (Mac/Linux) hoặc `%APPDATA%\Claude\claude_desktop_config.json` (Windows). Phải có entry `vn-business-os`.
2. **Test server start**: `vn-os-mcp` (or `python -m core.mcp_server`) — should listen on stdio.
3. **Re-install**: `vn-os install-mcp` (idempotent).
4. **Uninstall + clean**: `vn-os uninstall-mcp` → manual edit config → restart.

## Open questions

1. Multi-DN active vault detection: skill hiện tại nhận `vault` arg explicit, có nên auto-detect từ cwd?
2. Lite mode rate limit: nên auto-fallback `max_debate_rounds=1` khi detect rate limit?
3. Browser/Web client: Claude.ai web không có MCP — có giải pháp gì?

---

## Cross-reference

- v1 ship log: `plans/session-log-260506-implementation.md`
- v2 roadmap (cron, Web UI, multi-DN): `plans/v2-roadmap.md`
- Current file: `plans/v2-mcp-sampling-260506.md`
