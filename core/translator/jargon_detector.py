"""Phát hiện thuật ngữ Eng/abbrev trong text VN."""
from __future__ import annotations
import re
from core.translator.glossary import Glossary


JARGON_RE = re.compile(r"\b([A-Z]{2,}|[A-Z][a-z]+(?:[A-Z][a-z]+)+)\b")


class JargonDetector:
    def __init__(self, glossary: Glossary | None = None):
        self.glossary = glossary or Glossary()

    def detect(self, text: str) -> list[tuple[str, str | None]]:
        terms = set(JARGON_RE.findall(text))
        ignore = {"DN", "VN", "MM", "AM", "PM", "TP", "Q", "T", "CEO", "OK"}
        terms -= ignore
        return [(t, self.glossary.lookup(t)) for t in sorted(terms)]
