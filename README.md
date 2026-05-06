# VN Business OS

> AI Operating System cho doanh nghiệp Việt Nam — CEO chat, agents (phòng ban) họp bàn debate, sinh tài liệu .docx/.xlsx tuân thủ luật VN.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/built_on-LangGraph-purple.svg)](https://github.com/langchain-ai/langgraph)

## Vấn đề

DN nhỏ-vừa VN cần hệ thống vận hành chuẩn nhưng:
- Không đủ HR để xây 192 tài liệu vận hành
- AI generic không hiểu luật VN, ngữ cảnh DN cụ thể
- Plugin kiểu prompt chỉ ra tài liệu, không debate / kiểm chéo

## Giải pháp

VN Business OS là **engine debate giữa các phòng ban AI agents** + **knowledge base tài liệu chuẩn VN** + **tuân thủ luật VN**:

```
CEO chat → Router phân loại task → Đọc Brain DN → Phát hiện gap (Brain-first)
        → Hỏi CEO clarification (có citation) → Research live (luật, đối thủ)
        → Họp Pro/Con + 3 góc nhìn → Báo cáo có TL;DR
        → CEO duyệt → Sinh .docx/.xlsx → Lưu Obsidian + Git
```

## Kiến trúc

- **Engine debate**: Python + LangGraph (bóc từ TradingAgents, rename neutral)
- **Knowledge base**: 192 template tiếng Việt từ business-builder.plugin
- **Storage**: Obsidian Markdown + Git private repo
- **Multi-tool entry**: Claude Code / Cowork / Codex / Antigravity

## Quick Start

```bash
pip install -e .
export ANTHROPIC_API_KEY=...
vn-os onboard --vault ~/my-company-vault
vn-os run --brief "Tạo chiến dịch QC..." --vault ~/my-company-vault
```

Xem chi tiết: [docs/getting-started.md](docs/getting-started.md)

## Industry Packs

- **F&B** — kitchen, food-safety, food cost tracking
- **Retail** — warehouse, logistics, marketplace integration
- **Tech-SaaS** — engineering, product-design, data, growth

## 6 Rules

| # | Rule |
|---|---|
| 1 | Brain-first clarification — không hỏi khi chưa đọc Brain |
| 2 | Domain-neutral — engine không leak trading/finance |
| 3 | Single source of truth — Obsidian là sự thật |
| 4 | CEO-friendly language — tiếng Việt + jargon defined + TL;DR |
| 5 | Live research with citations — luật/đối thủ/benchmark |
| 6 | BYOT — template DN > pack > default |

## Đóng góp

PR welcome. Đặc biệt cần:
- Pack mới: Real Estate, Healthcare, Education, Beauty
- Việt hoá thêm agency-agents roles
- Test coverage

## License

MIT — © 2026 ltuananhsd@gmail.com

**Credits:**
- 192 template tiếng Việt trong `templates-vn/` adapted from `business-builder.plugin`
- Engine debate pattern adapted from [TradingAgents](https://github.com/TauricResearch/TradingAgents)
- Role definitions reference from [agency-agents](https://github.com/msitarzewski/agency-agents)
