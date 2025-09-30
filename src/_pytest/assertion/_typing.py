from __future__ import annotations

from collections.abc import Callable
from typing import Literal
from typing import Protocol

from _pytest.config import Config


class _HighlightFunc(Protocol):  # noqa: PYI046
    def __call__(self, source: str, lexer: Literal["diff", "python"] = "python") -> str:
        """Apply highlighting to the given source."""


# The _reprcompare attribute on the util module is used by the new assertion
# interpretation code and assertion rewriter to detect this plugin was
# loaded and in turn call the hooks defined here as part of the
# DebugInterpreter.
_reprcompare: Callable[[str, object, object], str | None] | None = None

# Works similarly as _reprcompare attribute. Is populated with the hook call
# when pytest_runtest_setup is called.
_assertion_pass: Callable[[int, str, str], None] | None = None

# Config object which is assigned during pytest_runtest_protocol.
_config: Config | None = None
