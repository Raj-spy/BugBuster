"""Typed contracts between BugBuster pipeline stages."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    tool: str
    rule_id: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    message: str
    path: str | None = None
    line: int | None = None
    evidence: str | None = None


class IngestedChange(BaseModel):
    source: str
    diff: str
    changed_files: list[str] = Field(default_factory=list)
    root: Path = Path(".")


class Verification(BaseModel):
    red: bool = False
    green: bool = False
    regression: bool = False
    mutation: bool = False
    details: list[str] = Field(default_factory=list)
