from dataclasses import dataclass, field
from typing import List


@dataclass
class DiffHunk:
    file: str = ""
    old_code: str = ""
    new_code: str = ""
    line_start: int = 0


@dataclass
class ParsedDiff:
    files_changed: List[str] = field(default_factory=list)
    hunks: List[DiffHunk] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0


@dataclass
class LogicChange:
    file: str = ""
    summary: str = ""
    impact: str = ""
    old_logic: str = ""
    new_logic: str = ""


@dataclass
class LogicAnalysis:
    logic_changes: List[LogicChange] = field(default_factory=list)


@dataclass
class CodeIssue:
    file: str = ""
    line: int = 0
    severity: str = ""
    issue: str = ""
    fix: str = ""


@dataclass
class QualityAnalysis:
    issues: List[CodeIssue] = field(default_factory=list)


@dataclass
class PerfIssue:
    file: str = ""
    line: int = 0
    severity: str = ""
    issue: str = ""
    fix: str = ""


@dataclass
class PerfAnalysis:
    issues: List[PerfIssue] = field(default_factory=list)
