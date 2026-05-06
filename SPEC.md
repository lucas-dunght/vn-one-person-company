# VN Business OS — Design Spec

**Ngày:** 2026-05-06
**Tác giả:** Brainstorm session với CEO
**Trạng thái:** Draft — chờ user review trước khi qua writing-plans
**Slug:** `vn-business-os` (alias `vbos`)
**License:** MIT

---

## 1. Mục tiêu

Xây 1 repo open-source giúp **mọi DN nhỏ-vừa Việt Nam** vận hành theo mô hình "doanh nghiệp 1 người + đội AI agents".

CEO giao việc qua chat/CLI → hệ thống đọc dữ liệu DN → các phòng ban (AI agents) họp bàn debate → ra báo cáo tổng hợp → CEO duyệt → tự sinh kế hoạch + tài liệu (.docx/.xlsx).

Áp dụng được mọi ngành (F&B, retail, tech, edu, healthcare...). Không phải hệ thống trading.

## 2. Kiến trúc tổng (4 lớp)

```
┌─────────────────────────────────────────────────────┐
│ LỚP 1 — ENTRY (CEO chat)                            │
│ Adapters: Claude Code · Cowork · (v2: Codex/Antigrav)│
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ LỚP 2 — CORE (Python + LangGraph)                   │
│ Orchestrator · Brain · Clarifier · Translator       │
│ Meeting (Bull/Bear debate) · Tools (research) · LLM │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ LỚP 3 — STATE                                       │
│ SQLite (LangGraph checkpoint)  +  Obsidian (Git)    │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ LỚP 4 — OUTPUT                                      │
│ Markdown reports · .docx/.xlsx · Decisions log      │
└─────────────────────────────────────────────────────┘
```

## 3. Quyết định kiến trúc đã chốt

| # | Quyết định |
|---|---|
| Hướng tiếp cận | Hybrid (Approach C): bóc engine debate từ TradingAgents + tự code phần còn lại |
| Stack | Python + LangGraph + SQLite + Obsidian Markdown + Git private |
| Lưu trữ | DN tự host: local + Git private repo (Github/Gitea) |
| Setup | Hybrid: clone manual hoặc wizard onboarding |
| Phòng ban | 13 core (từ business-builder.plugin) + industry packs + on-demand creator |
| MVP packs v1 | F&B + Retail + Tech-SaaS |
| Auto level | Semi-auto (2 stops) + context-aware clarification |
| Test case v1 | B — chiến dịch QC nhắm khách thu nhập 50tr+ |
| Multi-LLM | Default Claude Sonnet 4.6, fallback Gemini/GPT/Qwen/Ollama |
| Tools | Web search, VN law search, competitor research, industry benchmark, tax calc |

## 4. Sáu nguyên tắc bất di bất dịch

| # | Rule | Mô tả |
|---|---|---|
| 1 | Brain-first clarification | Không hỏi CEO khi chưa đọc Brain. Mỗi câu hỏi phải dẫn nguồn Brain. |
| 2 | Domain-neutral engine | Code copy từ TradingAgents phải rename toàn bộ — không trade/finance leak. |
| 3 | Single source of truth | Obsidian vault là sự thật. SQLite chỉ cache phục hồi. |
| 4 | CEO-friendly language | Tiếng Việt, định nghĩa thuật ngữ, có TL;DR. |
| 5 | Live research with citations | Search luật/đối thủ/benchmark khi cần. PHẢI cite nguồn. |
| 6 | BYOT (Bring Your Own Templates) | DN có thể đưa template riêng → ưu tiên dùng custom > default. |

## 5. Cấu trúc repo

```
vn-business-os/
├── core/                              # Python engine
│   ├── orchestrator/                  # router, flow_controller
│   ├── brain/                         # reader, gap_analyzer, memory
│   ├── clarifier/                     # question_generator (Brain-first)
│   ├── translator/                    # glossary, jargon, simplifier, TL;DR (RULE 4)
│   ├── meeting/                       # debate engine (reused TradingAgents)
│   ├── agents/                        # base_agent, department, registry, creator
│   ├── obsidian/                      # vault I/O, doc_writer, template_resolver
│   ├── tools/                         # web_search, vn_law, competitor, benchmark, tax (RULE 5)
│   ├── llm/                           # multi-provider abstraction
│   └── cli.py
├── departments/                       # 13 phòng core (YAML + agent .md)
├── packs/                             # F&B, Retail, Tech-SaaS
├── templates-vn/                      # 191 template từ bb-plugin (vendored)
├── vault-template/                    # Obsidian scaffold cho onboard
├── adapters/                          # claude-code, claude-cowork, codex, antigravity
├── scripts/                           # install.sh, onboard.py
├── tests/                             # unit, integration, e2e, fixtures
└── docs/                              # getting-started, architecture, how-to-create-pack
```

LoC ước: ~4800 dòng Python core + ~150-200 file YAML/MD config + ~1000 dòng test.

## 6. Cấu trúc vault DN

```
~/<dn>-vault/
├── 00-Brain/                          # AI đọc bắt buộc trước mọi việc
│   ├── strategy.md                    # tầm nhìn, ICP, mục tiêu năm
│   ├── products.md                    # SP đang có + giá + margin
│   ├── budget.md                      # ngân sách quý + còn lại
│   ├── headcount.md                   # phòng nào, agent nào active
│   ├── laws.md                        # luật DN, lao động, kế toán, QC
│   ├── decisions-log.md               # append-only quyết định
│   ├── state.md                       # giai đoạn, KPI hiện tại
│   └── glossary.md                    # auto-grown từ outputs
├── 00-Templates-Custom/               # 🆕 RULE 6: DN tự đưa template
├── 01-Departments/                    # clone từ /departments + pack
├── 02-Tasks/                          # CEO bỏ brief vào đây
│   └── YYYY-MM-DD-<slug>/
│       ├── 00-brief.md
│       ├── 01-routing.md
│       ├── 02-context.md
│       ├── 03-clarification.md
│       ├── 03b-research-findings.md   # 🆕 RULE 5
│       ├── 04-meeting-r1-perspectives.md
│       ├── 05-meeting-r2-debate.md
│       ├── 06-meeting-r3-perspectives.md
│       ├── 07-decision-report.md      # CEO duyệt ở đây (Stop 1)
│       └── 08-execution-plan.md       # CEO duyệt execute (Stop 2)
├── 03-Outputs/                        # docx/xlsx chính thức (10 folder chuẩn bb-plugin)
└── 99-Archive/
```

## 7. Data flow (Test case B)

```
CEO brief
   ↓
Brain reader   → load 7 file 00-Brain/
   ↓
Router         → SIMPLE/COMPLEX/STRATEGIC + dept list
   ↓
Gap analyzer   → so brief vs Brain
   ↓
Clarifier      → hỏi CEO (Brain-first, có citation) — chỉ hỏi nếu thiếu
   ↓
🆕 Research    → tools chạy parallel (luật + đối thủ + benchmark)
   ↓
Meeting R1     → mỗi phòng phát biểu (parallel)
   ↓
Meeting R2     → Pro Advocate vs Con Advocate (2-3 lượt)
   ↓
Meeting R3     → Perspective Debators (Tăng trưởng/Thận trọng/Cân bằng)
   ↓
Synthesizer    → 07-decision-report.md
   ↓
=== STOP 1: CEO duyệt báo cáo ===
   ↓
Execution Dispatcher → 08-execution-plan.md
   ↓
=== STOP 2: CEO duyệt execute ===
   ↓
Doc Writer     → sinh .docx/.xlsx vào 03-Outputs/
Memory         → append decisions-log.md
Git sync       → auto-commit
```

Timing: 15-25 phút/task COMPLEX. CEO ngồi máy ~10 phút.
Cost: ~$0.5-1.5/task (Claude Sonnet 4.6).

## 8. Định nghĩa Department + Agent

### Department (`departments/<code>/department.yaml`)
```yaml
code: "07-marketing"
name_vn: "Marketing & Thương hiệu"
tier: 3
agents: [brand-manager, content-creator, ads-specialist, seo-specialist]
default_speaker: brand-manager
routing_rules: [keyword-based agent selection]
refs_folder: refs/
depends_on: ["02-strategy", "08-customer", "03-finance"]
debate_role: { default: pro, override: { cost_cutting: con } }
```

### Agent (`departments/<code>/agents/<id>.md`)
```yaml
---
id: ads-specialist
name_vn: "Chuyên viên Quảng cáo"
department: 07-marketing
expertise: [...]
required_refs: [...]
required_tools: [vn_law_search, industry_benchmark]
deliverables: [...]
llm_override: { model: claude-sonnet-4-6, temperature: 0.3 }
---
[System prompt tiếng Việt]
```

### Pack (`packs/<name>/pack.yaml`)
```yaml
name: F&B Pack
adds_departments: [13-kitchen, 14-food-safety]
extends_departments:
  - target: 05-operations
    add_agents: [inventory-manager-fnb]
brain_template: brain-template/
compliance_refs: ["VSATTP NĐ 15/2018", "PCCC TCVN 5738:2021"]
```

### On-demand agent creation
Khi gap_analyzer phát hiện thiếu chuyên môn → đề xuất CEO → nếu duyệt → `creator.py` sinh file định nghĩa agent + commit vào Git → persist vĩnh viễn.

## 9. Industry Packs v1

### F&B (Quán ăn / Cafe / Nhà hàng)
- Phòng mới: 13-kitchen, 14-food-safety (~9 agent)
- Mở rộng: operations (inventory, vendor), customer (service-quality), sales (revenue mgr), finance (cogs tracker)
- Brain: table turnover, food cost %, labor cost %
- Compliance: NĐ 15/2018, PCCC

### Retail (Shop / E-commerce)
- Phòng mới: 13-warehouse, 14-logistics (~12 agent)
- Mở rộng: sales (marketplace, livestream), marketing (creative, affiliate), customer (online, returns), product-tech (ecommerce platform, pixel)
- Brain: GMV, AOV, COD %, DOH
- Tools: tích hợp Shopee/Lazada/Tiki/TikTok Shop concepts

### Tech-SaaS (Startup phần mềm)
- Phòng mới: 13-engineering, 14-product-design, 15-data (~22 agent)
- Mở rộng từ agency-agents engineering/, product/, design/
- Brain: MRR/ARR, DAU/MAU, churn, LTV/CAC, runway

Tổng v1: ~73 agent ready-to-use.

## 10. CEO-friendly language (RULE 4)

### Module `core/translator/`
- `glossary.py` — load/save vault/00-Brain/glossary.md
- `jargon_detector.py` — phát hiện thuật ngữ
- `simplifier.py` — rewrite phức tạp → đơn giản
- `tldr_generator.py` — sinh TL;DR
- `terms_dictionary.yaml` — từ điển VN + ví dụ + benchmark VN

### Output format chuẩn
```markdown
## 📌 Tóm lại (đọc 30 giây)
- [3-5 dòng dân thường hiểu]

## Chi tiết
[nội dung]

**Thuật ngữ X** (giải thích đơn giản, vd cụ thể của DN này)
```

### Pipeline
```
Agent raw output → JargonDetector → Simplifier → TLDRGenerator → CEO
```

## 11. Live research (RULE 5)

### Module `core/tools/`
| Tool | Nguồn | Khi nào dùng |
|---|---|---|
| `web_search` | Tavily/Serper/Brave | General research |
| `vn_law_search` | thuvienphapluat.vn, luatvietnam.vn, vbpl.vn | Check tuân thủ |
| `vn_local_regulation` | Cổng dịch vụ công, Sở/Bộ | Quy định địa phương |
| `competitor_research` | Web public info | Competitive analysis |
| `industry_benchmark` | Curated YAML + scrape | KPI ngành VN |
| `tax_calculator` | Code thuần | VAT, TNCN, TNDN, lệ phí môn bài |

### Research Phase (mới — chạy trước Meeting R1)
ToolRouter quét brief + Brain → quyết định cần research gì → run parallel → cache 24h → inject vào MeetingState.

### Citation bắt buộc
Mọi nhận định trong report phải có citation: URL + ngày truy cập. Ví dụ: `[cite: thuvienphapluat.vn/.../Luat-QC-2012, retrieved 2026-05-06]`.

## 12. BYOT — Bring Your Own Templates (RULE 6)

### Thứ tự ưu tiên
1. `vault/00-Templates-Custom/<dept>/` — DN tự đưa
2. `vault/01-Departments/<dept>/refs/` — pack templates đã copy vào vault
3. `repo/templates-vn/<dept>/` — 191 template default từ bb-plugin (vendored)

### Hỗ trợ format
`.md`, `.docx`, `.xlsx`. PDF tuỳ chọn (cần OCR).

### Wizard onboarding
Hỏi DN có template sẵn không → nếu có → import + LLM phân loại + sinh `_index.md` mapping.

## 13. Multi-tool adapters

| Tool | Format | v1 | v2 |
|---|---|:-:|:-:|
| Claude Code | `.md` skill | ✅ | |
| Claude Cowork | `.claude-plugin` | ✅ | |
| Codex | system prompt | | ✅ |
| Antigravity | `SKILL.md` | | ✅ |

Pattern: 1 core Python + nhiều adapter mỏng gọi CLI qua Bash tool.

## 14. Error handling

| Lớp | Loại | Action |
|---|---|---|
| A | LLM (timeout/rate/filter) | Retry x3 → failover provider → reframe |
| B | Tool (API down) | Cache fallback → mark UNVERIFIED |
| C | State recovery | LangGraph checkpoint → `vn-os resume <task>` |
| D | Validation | Pause + ask CEO bổ sung |
| E | User input | Spell check + intent confirm |

## 15. Testing strategy

```
tests/
├── unit/        ~70%  (router, brain, gap, clarifier, translator, tools)
├── integration/ ~20%  (meeting graph, BYOT, research phase)
├── e2e/         🎯    (test_b campaign, test_a onboard, test_c simple JD)
└── fixtures/    (techco-vault, fnb-vault, retail-vault demo data)
```

### Test case B — acceptance criteria (key items)
- task_class == COMPLEX
- ≥ 5 phòng triệu tập
- ≥ 3 research findings (law + competitor + benchmark)
- All clarifications có citation (RULE 1)
- Decision report có TL;DR + jargon defined (RULE 4)
- Decision report có law citations + competitor data (RULE 5)
- 2 file output (.docx + .xlsx) đúng folder
- < 100k tokens, < $2/task, < 25 phút

## 16. Roadmap v1 (~6 tuần FT-equivalent)

| Tuần | Phase | Output |
|------|-------|--------|
| 1 | Foundation | Repo skeleton + Brain + 13 phòng + vendor 191 template |
| 2 | Engine bóc tách | meeting_graph từ TradingAgents → rename neutral + checkpoint |
| 3 | Orchestrator + Brain-first | Router + Gap + Clarifier + Flow controller (2 stops) |
| 4 | Tools + Translator | 6 tool + glossary + simplifier + TL;DR + research phase |
| 5 | Departments + Pack + BYOT | 13 phòng full agents + 3 pack + template resolver + doc writer |
| 6 | Adapter + E2E + Onboard | Claude Code/Cowork adapter + wizard + test B pass |

v1.1: test A (onboard) + C (simple JD), Codex/Antigravity stubs.
v2: auto-loop cron, web UI, multi-DN, packs mới (Real Estate, Healthcare, Edu).

## 17. Risks

| Risk | P | I | Mitigation |
|---|:-:|:-:|---|
| LangGraph version churn | M | H | Pin version, isolate trong meeting/ |
| LLM cost overrun | H | M | Token counter + budget guard |
| Tool API down | M | M | Cache 24h + UNVERIFIED mode |
| Tiếng Việt LLM yếu | L | H | Default Claude Sonnet 4.6, A/B test |
| BYOT format lạ | M | L | Support 3 format chuẩn |
| Vault corruption | L | H | Git auto-commit |
| Onboard quá dài | M | H | Max 30 câu, skip optional |
| Multi-pack conflict | M | L | Merge logic + test combo |
| Maintainer bandwidth | H | M | Doc tốt + contribution guide |

## 18. Definition of Done v1

- [ ] Repo public, README tiếng Việt đầy đủ
- [ ] `pip install -e .` work Win/Mac/Linux
- [ ] Wizard sinh vault valid
- [ ] Test case B chạy E2E < 25 phút, < $2
- [ ] 13 phòng core có agents thật
- [ ] 3 pack chạy được test riêng
- [ ] BYOT demo work
- [ ] 6 RULES enforced trong code
- [ ] Claude Code + Cowork adapter E2E
- [ ] `getting-started.md` cho non-tech CEO

## 19. Open questions

1. LLM provider mặc định v1 — Claude Sonnet 4.6 (mạnh tiếng Việt) hay cho user chọn lúc onboard?
2. Web search API: Tavily (free tier 1000/mo) hay Serper ($1/1000)? Default cái nào?
3. Có cần Vietnamese spell-check (pyvi) ngay v1 không, hay v1.1?
4. BYOT có hỗ trợ PDF + OCR ngay v1 không (cần thư viện thêm), hay chỉ md/docx/xlsx?
5. Auto-commit Git: bật mặc định hay opt-in qua config?
6. Brain glossary auto-grow: bật mặc định hay manual approve mỗi term?
7. Test cost với LLM thật trong CI: dùng cassette/recording (như VCR) hay mock thuần?
