# References

> Tài liệu nguồn để vendor / tham chiếu khi cần code lại hoặc đối chiếu pattern.

---

## 📦 Files có sẵn

### `business-builder.plugin` (~370 KB, zip archive)
- Plugin Claude tiếng Việt — 13 skill, 191 tài liệu chuẩn DN VN
- Tuân thủ ISO 9001:2015, EOS/Traction, E-Myth, McKinsey 7S, SYSTEMology
- Tuân thủ Luật DN 2020, BLLĐ 2019, Luật KT 2015
- **Mục đích:** vendor 191 template từ skill `references/` của plugin này vào `templates-vn/`
- **Script vendor:** `scripts/dev/vendor-bb-plugin.sh` (tạo trong Phase 1 Task 3)
- **Cách giải nén:**
  ```bash
  unzip references/business-builder.plugin -d /tmp/bb-plugin
  # Trong /tmp/bb-plugin/skills/bb-*/references/ có 191 .md template
  ```

---

## 🌐 Repos GitHub (clone khi cần)

### 1. TradingAgents (TauricResearch/TradingAgents)
- URL: https://github.com/TauricResearch/TradingAgents
- **Mục đích:** Reference engine debate (LangGraph + Bull/Bear + 3-tier risk)
- **Pattern lấy:** `tradingagents/graph/trading_graph.py` + `conditional_logic.py` + `checkpointer.py` + `agent_states.py`
- **Cách dùng:** clone vào `references/tradingagents/` (nhớ thêm `references/` vào `.gitignore`)

```bash
git clone --depth 1 https://github.com/TauricResearch/TradingAgents references/tradingagents
echo "references/tradingagents/" >> .gitignore
```

⚠️ **RULE 2 (Domain-neutral):** Code copy từ đây PHẢI rename hết Bull/Bear/trade/finance/ticker — không leak vào core/.

### 2. agency-agents (msitarzewski/agency-agents)
- URL: https://github.com/msitarzewski/agency-agents
- **Mục đích:** Reference 144+ role definitions (markdown). Lấy cảm hứng cho agents pack Tech-SaaS (engineering, design, product...).
- **Cách dùng:** clone tham khảo, KHÔNG vendor vào repo (chỉ adapt + Việt hoá khi cần).

```bash
git clone --depth 1 https://github.com/msitarzewski/agency-agents.git references/agency-agents
echo "references/agency-agents/" >> .gitignore
```

---

## 🔒 Lưu ý quan trọng

- Folder `references/` này chỉ chứa file local hoặc clone tham khảo — **KHÔNG vendor vào package distributed**
- Khi public repo, thêm `references/` vào `.gitignore` để không upload các fork third-party
- Mọi credit / license của tài liệu nguồn được note tại `LICENSE` / `NOTICE` của repo chính

---

## 🛠️ Khi nào dùng folder này?

| Tình huống | Hành động |
|---|---|
| Phase 1 Task 3: vendor 191 template | Run `bash scripts/dev/vendor-bb-plugin.sh references/business-builder.plugin` |
| Phase 2: bóc engine debate | `git clone TradingAgents` → đọc graph/* → adapt |
| Phase 5: cần thêm role inspirations | `git clone agency-agents` → adapt từng agent |
| Có update bb-plugin version mới | Copy file mới đè lên `references/business-builder.plugin` rồi re-run vendor script |
