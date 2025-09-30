# mypy: allow-untyped-defs
"""Utilities for assertion debugging."""

from __future__ import annotations


__all__ = ["_diff_text", "assertrepr_compare", "format_explanation"]

from collections.abc import Callable
import os
from typing import Literal

from _pytest.assertion._compare_eq import _diff_text
from _pytest.assertion.assertrepr_compare import assertrepr_compare
from _pytest.assertion.format_explanation import format_explanation
from _pytest.config import Config


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


def dummy_highlighter(source: str, lexer: Literal["diff", "python"] = "python") -> str:
    """Dummy highlighter that returns the text unprocessed.

    Needed for _notin_text, as the diff gets post-processed to only show the "+" part.
    """
    return source


def running_on_ci() -> bool:
    """Check if we're currently running on a CI system."""
    env_vars = ["CI", "BUILD_NUMBER"]
    return any(var in os.environ for var in env_vars)
