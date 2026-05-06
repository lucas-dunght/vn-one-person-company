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
