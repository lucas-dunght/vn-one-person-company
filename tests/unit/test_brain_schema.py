import pytest
from core.brain.schema import (
    Strategy, Product, Budget, Headcount, BrainContext
)

def test_strategy_minimal():
    s = Strategy(vision="VN SME OS", icp="SME 5-50 NV")
    assert s.vision == "VN SME OS"

def test_product_with_price():
    p = Product(code="PRO", name="Premium", price_vnd=20_000_000, margin_pct=70)
    assert p.price_vnd == 20_000_000

def test_brain_context_assembly():
    ctx = BrainContext(
        strategy=Strategy(vision="V", icp="I"),
        products=[Product(code="A", name="X", price_vnd=1000, margin_pct=50)],
        budget=Budget(total_year_vnd=1_000_000_000, mkt_quarter_remaining_vnd=800_000_000),
        headcount=Headcount(active_departments=["07-marketing"]),
        laws=[],
        decisions=[],
        state="growth",
        glossary={},
    )
    assert ctx.products[0].name == "X"
    assert ctx.budget.mkt_quarter_remaining_vnd == 800_000_000

def test_invalid_margin_rejected():
    with pytest.raises(ValueError):
        Product(code="A", name="X", price_vnd=1000, margin_pct=150)
