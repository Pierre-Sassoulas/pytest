from __future__ import annotations

from _pytest._io.saferepr import saferepr
from _pytest.assertion._compare_eq import _diff_text
from _pytest.assertion.util import dummy_highlighter


def _notin_text(term: str, text: str, verbose: int = 0) -> list[str]:
    index = text.find(term)
    head = text[:index]
    tail = text[index + len(term) :]
    correct_text = head + tail
    diff = _diff_text(text, correct_text, dummy_highlighter, verbose)
    newdiff = [f"{saferepr(term, maxsize=42)} is contained here:"]
    for line in diff:
        if line.startswith("Skipping"):
            continue
        if line.startswith("- "):
            continue
        if line.startswith("+ "):
            newdiff.append("  " + line[2:])
        else:
            newdiff.append(line)
    return newdiff
