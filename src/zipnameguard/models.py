"""Immutable results shared by the API and CLI."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Literal["error", "warning"]
    member: str
    entry_index: int
    message: str
    related_member: str | None = None


@dataclass(frozen=True)
class Report:
    archive: str
    entries: int
    findings: tuple[Finding, ...]

    @property
    def has_errors(self) -> bool:
        return any(item.severity == "error" for item in self.findings)
