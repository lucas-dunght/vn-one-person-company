from unittest.mock import MagicMock
from core.translator.simplifier import Simplifier


def test_simplifier_passes_through_when_no_jargon():
    s = Simplifier(llm=MagicMock())
    out = s.simplify("Doanh thu tháng 5 tăng 20%")
    assert out == "Doanh thu tháng 5 tăng 20%"


def test_simplifier_calls_llm_when_jargon_present():
    llm = MagicMock(complete=MagicMock(return_value="rewritten with defs"))
    s = Simplifier(llm=llm)
    out = s.simplify("CAC tăng 30%, ROAS giảm")
    llm.complete.assert_called_once()
    assert out == "rewritten with defs"
