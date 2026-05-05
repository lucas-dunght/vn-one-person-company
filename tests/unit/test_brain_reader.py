from pathlib import Path
import pytest
from core.brain.reader import BrainReader

FIXTURE = Path(__file__).parent.parent / "fixtures" / "demo-vault"


def test_read_strategy_returns_vision():
    reader = BrainReader(FIXTURE)
    ctx = reader.load()
    assert "TechCo" in ctx.strategy.vision


def test_read_products_returns_three():
    reader = BrainReader(FIXTURE)
    ctx = reader.load()
    assert len(ctx.products) == 3
    assert ctx.products[2].code == "PRE"
    assert ctx.products[2].price_vnd == 20_000_000


def test_missing_brain_raises():
    with pytest.raises(FileNotFoundError):
        BrainReader(Path("/nonexistent")).load()
