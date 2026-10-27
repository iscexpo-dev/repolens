"""Small, dependency-free unified-diff parser for changed new-file lines.

The parser is intentionally conservative. Production integration should add
fixtures for binary patches, quoted paths, submodules, malformed diffs, and
all Git provider edge cases before using its output for inline comments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_GIT_FILE_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")


@dataclass(frozen=True, slots=True)
class ChangedLine:
    path: str
    new_line: int
    content: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_changed_lines(diff_text: str) -> list[ChangedLine]:
    """Return added lines with their line number in the new file.

    Deletions are not returned because they have no valid new-file line number.
    File headers are handled conservatively; `/dev/null` additions are resolved
    from the `+++ b/...` line when available.
    """
    if not isinstance(diff_text, str):
        raise TypeError("diff_text must be a string")

    result: list[ChangedLine] = []
    current_path: str | None = None
    new_line: int | None = None

    for raw in diff_text.splitlines():
        if raw.startswith("diff --git "):
            match = _GIT_FILE_RE.match(raw)
            current_path = match.group(2) if match else None
            new_line = None
            continue

        if raw.startswith("+++ "):
            path = raw[4:].strip()
            if path == "/dev/null":
                current_path = None
            elif path.startswith("b/"):
                current_path = path[2:]
            else:
                current_path = path
            continue

        if raw.startswith("--- "):
            continue

        hunk = _HUNK_RE.match(raw)
        if hunk:
            new_line = int(hunk.group(1))
            continue

        if new_line is None or current_path is None:
            continue

        if raw.startswith("\\ No newline at end of file"):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            result.append(ChangedLine(current_path, new_line, raw[1:]))
            new_line += 1
        elif raw.startswith(" "):
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            # A removed line advances only the old-file position.
            continue
        else:
            # Unknown hunk content invalidates the active line cursor so that
            # malformed input cannot silently create incorrect anchors.
            new_line = None

    return result
