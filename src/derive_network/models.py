from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Sequence

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    UNCHECKED = "unchecked"
    CAS = "cas"
    FORMAL = "formal"


class Statement(BaseModel):
    id: str
    latex_variants: List[str] = Field(default_factory=list)
    sympy_srepr: str
    assumptions: List[str] = Field(default_factory=list)
    units: Dict[str, float] = Field(default_factory=dict)
    regime: List[str] = Field(default_factory=list)
    field_tags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNCHECKED

    model_config = {
        "frozen": True,
        "populate_by_name": True,
    }


class Derivation(BaseModel):
    id: str
    rule_tags: List[str] = Field(default_factory=list)
    exact: bool = True
    error_bound: Optional[str] = None
    script_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assumptions: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True,
        "populate_by_name": True,
    }


class DerivationCreate(BaseModel):
    inputs: Sequence[str]
    outputs: Sequence[str]
    rule_tags: Sequence[str] = Field(default_factory=list)
    exact: bool = True
    error_bound: Optional[str] = None
    script_ref: Optional[str] = None
    assumptions: Sequence[str] = Field(default_factory=list)
    sources: Sequence[str] = Field(default_factory=list)


class StatementCreate(BaseModel):
    latex: Optional[str] = None
    sympy: Optional[str] = None
    assumptions: Sequence[str] = Field(default_factory=list)
    regime: Sequence[str] = Field(default_factory=list)
    field_tags: Sequence[str] = Field(default_factory=list)
    sources: Sequence[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNCHECKED

    model_config = {
        "extra": "allow"
    }


class PathResponse(BaseModel):
    path: List[str]
    nodes: Dict[str, Dict[str, object]]
