# mypy: allow-untyped-defs
"""Utilities for assertion debugging."""

from __future__ import annotations

import os


def running_on_ci() -> bool:
    """Check if we're currently running on a CI system."""
    env_vars = ["CI", "BUILD_NUMBER"]
    return any(var in os.environ for var in env_vars)
