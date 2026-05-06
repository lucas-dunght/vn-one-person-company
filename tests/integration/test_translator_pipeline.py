from unittest.mock import MagicMock
from core.translator.pipeline import TranslatorPipeline


def test_pipeline_simplifies_and_prepends_tldr():
    llm = MagicMock()
    llm.complete.side_effect = [
        "rewritten with **CAC** (chi phí 1 khách)",
        "## 📌 Tóm lại\n- key1\n- key2\n- key3",
    ]

    p = TranslatorPipeline(llm=llm)
    out = p.apply("CAC tăng 30%, cần action ngay")

    assert out.startswith("## 📌 Tóm lại")
    assert "**CAC**" in out
