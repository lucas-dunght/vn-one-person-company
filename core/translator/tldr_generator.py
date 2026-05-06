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
        if "## 📌 Tóm lại" in full_text:
            return full_text
        tldr = self.generate(full_text)
        return tldr + "\n\n---\n\n" + full_text
