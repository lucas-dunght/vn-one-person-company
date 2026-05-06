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

        glossary_text = "\n".join(
            f"- **{t}**: {defn or '(chưa định nghĩa, hãy giải thích bằng tiếng Việt)'}"
            for t, defn in terms
        )

        messages = [
            {"role": "system", "content": SIMPLIFIER_PROMPT.format(glossary_subset=glossary_text)},
            {"role": "user", "content": text},
        ]
        return self.llm.complete(messages)
