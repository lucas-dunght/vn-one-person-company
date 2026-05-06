from unittest.mock import MagicMock
import json
from core.brain.gap_analyzer import GapAnalyzer, Gap, Severity
from core.brain.schema import BrainContext, Strategy, Product, Budget, Headcount


def _brain():
    return BrainContext(
        strategy=Strategy(vision="V", icp="SME 5-50 NV (chủ DN)"),
        products=[
            Product(code="STR", name="Starter", price_vnd=1_000_000, margin_pct=60),
            Product(code="PRE", name="Premium", price_vnd=20_000_000, margin_pct=75),
        ],
        budget=Budget(total_year_vnd=1_200_000_000, mkt_quarter_remaining_vnd=800_000_000),
        headcount=Headcount(
            active_departments=["07-marketing"],
            active_agents={"07-marketing": ["brand-manager", "ads-specialist"]},
        ),
        laws=[], decisions=[], state="growth", glossary={},
    )


def test_gap_detects_icp_mismatch():
    fake = json.dumps([
        {"field": "ICP", "severity": "CRITICAL",
         "current_value": "SME (chủ DN)",
         "brief_value": "cá nhân thu nhập 50tr+",
         "reason": "Brief lệch khỏi strategy ICP", "citation": "00-Brain/strategy.md"}
    ])
    llm = MagicMock(complete=MagicMock(return_value=fake))
    g = GapAnalyzer(llm=llm)
    gaps = g.analyze(brief="QC nhắm khách thu nhập 50tr+", brain=_brain())
    assert len(gaps) == 1
    assert gaps[0].severity == Severity.CRITICAL
    assert "ICP" in gaps[0].field


def test_gap_empty_when_brain_sufficient():
    llm = MagicMock(complete=MagicMock(return_value="[]"))
    g = GapAnalyzer(llm=llm)
    gaps = g.analyze(brief="Soạn JD kế toán", brain=_brain())
    assert gaps == []
