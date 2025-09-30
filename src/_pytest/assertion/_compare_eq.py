from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
import pprint
from typing import Any

from _pytest._io.pprint import PrettyPrinter
from _pytest._io.saferepr import saferepr
from _pytest.assertion._isx import isattrs
from _pytest.assertion._typing import _HighlightFunc
from _pytest.assertion.util import running_on_ci


def _compare_eq_sequence(
    left: Sequence[Any],
    right: Sequence[Any],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    comparing_bytes = isinstance(left, bytes) and isinstance(right, bytes)
    explanation: list[str] = []
    len_left = len(left)
    len_right = len(right)
    for i in range(min(len_left, len_right)):
        if left[i] != right[i]:
            if comparing_bytes:
                # when comparing bytes, we want to see their ascii representation
                # instead of their numeric values (#5260)
                # using a slice gives us the ascii representation:
                # >>> s = b'foo'
                # >>> s[0]
                # 102
                # >>> s[0:1]
                # b'f'
                left_value = left[i : i + 1]
                right_value = right[i : i + 1]
            else:
                left_value = left[i]
                right_value = right[i]

            explanation.append(
                f"At index {i} diff:"
                f" {highlighter(repr(left_value))} != {highlighter(repr(right_value))}"
            )
            break

    if comparing_bytes:
        # when comparing bytes, it doesn't help to show the "sides contain one or more
        # items" longer explanation, so skip it

        return explanation

    len_diff = len_left - len_right
    if len_diff:
        if len_diff > 0:
            dir_with_more = "Left"
            extra = saferepr(left[len_right])
        else:
            len_diff = 0 - len_diff
            dir_with_more = "Right"
            extra = saferepr(right[len_left])

        if len_diff == 1:
            explanation += [
                f"{dir_with_more} contains one more item: {highlighter(extra)}"
            ]
        else:
            explanation += [
                f"{dir_with_more} contains {len_diff} more items, first extra item: {highlighter(extra)}"
            ]
    return explanation


def _compare_eq_dict(
    left: Mapping[Any, Any],
    right: Mapping[Any, Any],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    explanation: list[str] = []
    set_left = set(left)
    set_right = set(right)
    common = set_left.intersection(set_right)
    same = {k: left[k] for k in common if left[k] == right[k]}
    if same and verbose < 2:
        explanation += [f"Omitting {len(same)} identical items, use -vv to show"]
    elif same:
        explanation += ["Common items:"]
        explanation += highlighter(pprint.pformat(same)).splitlines()
    diff = {k for k in common if left[k] != right[k]}
    if diff:
        explanation += ["Differing items:"]
        for k in diff:
            explanation += [
                highlighter(saferepr({k: left[k]}))
                + " != "
                + highlighter(saferepr({k: right[k]}))
            ]
    extra_left = set_left - set_right
    len_extra_left = len(extra_left)
    if len_extra_left:
        explanation.append(
            f"Left contains {len_extra_left} more item{'' if len_extra_left == 1 else 's'}:"
        )
        explanation.extend(
            highlighter(pprint.pformat({k: left[k] for k in extra_left})).splitlines()
        )
    extra_right = set_right - set_left
    len_extra_right = len(extra_right)
    if len_extra_right:
        explanation.append(
            f"Right contains {len_extra_right} more item{'' if len_extra_right == 1 else 's'}:"
        )
        explanation.extend(
            highlighter(pprint.pformat({k: right[k] for k in extra_right})).splitlines()
        )
    return explanation


def _diff_text(
    left: str, right: str, highlighter: _HighlightFunc, verbose: int = 0
) -> list[str]:
    """Return the explanation for the diff between text.

    Unless --verbose is used this will skip leading and trailing
    characters which are identical to keep the diff minimal.
    """
    from difflib import ndiff

    explanation: list[str] = []

    if verbose < 1:
        i = 0  # just in case left or right has zero length
        for i in range(min(len(left), len(right))):
            if left[i] != right[i]:
                break
        if i > 42:
            i -= 10  # Provide some context
            explanation = [
                f"Skipping {i} identical leading characters in diff, use -v to show"
            ]
            left = left[i:]
            right = right[i:]
        if len(left) == len(right):
            for i in range(len(left)):
                if left[-i] != right[-i]:
                    break
            if i > 42:
                i -= 10  # Provide some context
                explanation += [
                    f"Skipping {i} identical trailing "
                    "characters in diff, use -v to show"
                ]
                left = left[:-i]
                right = right[:-i]
    keepends = True
    if left.isspace() or right.isspace():
        left = repr(str(left))
        right = repr(str(right))
        explanation += ["Strings contain only whitespace, escaping them using repr()"]
    # "right" is the expected base against which we compare "left",
    # see https://github.com/pytest-dev/pytest/issues/3333
    explanation.extend(
        highlighter(
            "\n".join(
                line.strip("\n")
                for line in ndiff(right.splitlines(keepends), left.splitlines(keepends))
            ),
            lexer="diff",
        ).splitlines()
    )
    return explanation


def _compare_eq_iterable(
    left: Iterable[Any],
    right: Iterable[Any],
    highlighter: _HighlightFunc,
    verbose: int = 0,
) -> list[str]:
    if verbose <= 0 and not running_on_ci():
        return ["Use -v to get more diff"]
    # dynamic import to speedup pytest
    import difflib

    left_formatting = PrettyPrinter().pformat(left).splitlines()
    right_formatting = PrettyPrinter().pformat(right).splitlines()

    explanation = ["", "Full diff:"]
    # "right" is the expected base against which we compare "left",
    # see https://github.com/pytest-dev/pytest/issues/3333
    explanation.extend(
        highlighter(
            "\n".join(
                line.rstrip()
                for line in difflib.ndiff(right_formatting, left_formatting)
            ),
            lexer="diff",
        ).splitlines()
    )
    return explanation


def has_default_eq(
    obj: object,
) -> bool:
    """Check if an instance of an object contains the default eq

    First, we check if the object's __eq__ attribute has __code__,
    if so, we check the equally of the method code filename (__code__.co_filename)
    to the default one generated by the dataclass and attr module
    for dataclasses the default co_filename is <string>, for attrs class, the __eq__ should contain "attrs eq generated"
    """
    # inspired from https://github.com/willmcgugan/rich/blob/07d51ffc1aee6f16bd2e5a25b4e82850fb9ed778/rich/pretty.py#L68
    if hasattr(obj.__eq__, "__code__") and hasattr(obj.__eq__.__code__, "co_filename"):
        code_filename = obj.__eq__.__code__.co_filename

        if isattrs(obj):
            return "attrs generated " in code_filename

        return code_filename == "<string>"  # data class
    return True
