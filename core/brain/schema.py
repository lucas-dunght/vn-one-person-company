"""Pydantic schemas cho Brain layer (00-Brain/*.md)."""
from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class Strategy(BaseModel):
    vision: str
    mission: Optional[str] = None
    icp: str = Field(description="Ideal Customer Profile")
    icp_details: Optional[str] = None
    yearly_goals: dict[str, str] = Field(default_factory=dict)
    positioning: Optional[str] = None


class Product(BaseModel):
    code: str
    name: str
    price_vnd: int
    margin_pct: float = Field(ge=0, le=100)
    status: str = "active"
    features: list[str] = Field(default_factory=list)


class BudgetLine(BaseModel):
    department: str
    allocated_vnd: int
    spent_vnd: int = 0

    @property
    def remaining_vnd(self) -> int:
        return self.allocated_vnd - self.spent_vnd


class Budget(BaseModel):
    total_year_vnd: int
    spent_year_vnd: int = 0
    by_department: list[BudgetLine] = Field(default_factory=list)
    mkt_quarter_remaining_vnd: int = 0


class Headcount(BaseModel):
    active_departments: list[str] = Field(default_factory=list)
    active_agents: dict[str, list[str]] = Field(default_factory=dict)
    expertise_gaps: list[str] = Field(default_factory=list)


class LawReference(BaseModel):
    name: str
    code: Optional[str] = None
    scope: str = "general"  # general | industry | local
    note: Optional[str] = None


class DecisionEntry(BaseModel):
    date: date
    slug: str
    owner: str
    decision: str
    reason: str
    task_ref: Optional[str] = None


class BrainContext(BaseModel):
    """Assembled view of toan bo 00-Brain/ — passed vao moi agent."""
    strategy: Strategy
    products: list[Product]
    budget: Budget
    headcount: Headcount
    laws: list[LawReference]
    decisions: list[DecisionEntry]
    state: str
    glossary: dict[str, str]
