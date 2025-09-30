from __future__ import annotations

from collections.abc import Sequence
import pprint
from typing import Any
from unicodedata import normalize

from _pytest import outcomes
import _pytest._code
from _pytest._io.saferepr import saferepr
from _pytest._io.saferepr import saferepr_unlimited
from _pytest.assertion._compare_eq import _compare_eq_dict
from _pytest.assertion._compare_eq import _compare_eq_iterable
from _pytest.assertion._compare_eq import _compare_eq_sequence
from _pytest.assertion._compare_eq import _diff_text
from _pytest.assertion._compare_eq import has_default_eq
from _pytest.assertion._compare_set import SET_COMPARISON_FUNCTIONS
from _pytest.assertion._isx import isattrs
from _pytest.assertion._isx import isdatacls
from _pytest.assertion._isx import isiterable
from _pytest.assertion._isx import isnamedtuple
from _pytest.assertion._notin_text import _notin_text
from _pytest.assertion._typing import _HighlightFunc
from _pytest.config import Config


def assertrepr_compare(
    config: Config, op: str, left: Any, right: Any, use_ascii: bool = False
) -> list[str] | None:
    """Return specialised explanations for some operators/operands."""
    verbose = config.get_verbosity(Config.VERBOSITY_ASSERTIONS)

    # Strings which normalize equal are often hard to distinguish when printed; use ascii() to make this easier.
    # See issue #3246.
    use_ascii = (
        isinstance(left, str)
        and isinstance(right, str)
        and normalize("NFD", left) == normalize("NFD", right)
    )

    if verbose > 1:
        left_repr = saferepr_unlimited(left, use_ascii=use_ascii)
        right_repr = saferepr_unlimited(right, use_ascii=use_ascii)
    else:
        # XXX: "15 chars indentation" is wrong
        #      ("E       AssertionError: assert "); should use term width.
        maxsize = (
            80 - 15 - len(op) - 2
        ) // 2  # 15 chars indentation, 1 space around op

        left_repr = saferepr(left, maxsize=maxsize, use_ascii=use_ascii)
        right_repr = saferepr(right, maxsize=maxsize, use_ascii=use_ascii)

    summary = f"{left_repr} {op} {right_repr}"
    highlighter = config.get_terminal_writer()._highlight
    explanation: list[str] | None
    try:
        match (left, op, right):
            case (
                set() | frozenset(),
                "==" | "!=" | ">=" | "<=" | ">" | "<",
                set() | frozenset(),
            ):
                explanation = SET_COMPARISON_FUNCTIONS[op](
                    left, right, highlighter, verbose
                )
            case (_, "==", _):
                explanation = _compare_eq_any(left, right, highlighter, verbose)
            case (str(), "not in", str()):
                explanation = _notin_text(left, right, verbose)
            case _:
                explanation = None
    except outcomes.Exit:
        raise
    except Exception:
        repr_crash = _pytest._code.ExceptionInfo.from_current()._getreprcrash()
        explanation = [
            f"(pytest_assertion plugin: representation of details failed: {repr_crash}.",
            " Probably an object has a faulty __repr__.)",
        ]

    if not explanation:
        return None

    if explanation[0] != "":
        explanation = ["", *explanation]
    return [summary, *explanation]


def _compare_eq_any(
    left: Any, right: Any, highlighter: _HighlightFunc, verbose: int = 0
) -> list[str]:
    from _pytest.python_api import ApproxBase

    explanation: list[str] = []
    match (left, right):
        case (str(), str()):
            return _diff_text(left, right, highlighter, verbose)
        case (_, ApproxBase() as approx_side):
            explanation = approx_side._repr_compare(left)
        case (ApproxBase() as approx_side, _):
            explanation = approx_side._repr_compare(right)
        case (tuple(), _) if getattr(left, "_fields", None) is not None:
            explanation = _compare_eq_cls(left, right, highlighter, verbose)
        case (Sequence(), Sequence()):
            explanation = _compare_eq_sequence(left, right, highlighter, verbose)
        case (dict(), dict()):
            explanation = _compare_eq_dict(left, right, highlighter, verbose)
        case _ if type(left) is type(right) and (
            getattr(left, "__dataclass_fields__", None) is not None
            or getattr(left, "__attrs_attrs__", None) is not None
        ):
            explanation = _compare_eq_cls(left, right, highlighter, verbose)
        case _:
            explanation = []

    if isiterable(left) and isiterable(right):
        expl = _compare_eq_iterable(left, right, highlighter, verbose)
        explanation.extend(expl)
    return explanation


def _compare_eq_cls(
    left: Any, right: Any, highlighter: _HighlightFunc, verbose: int
) -> list[str]:
    if not has_default_eq(left):
        return []
    if isdatacls(left):
        import dataclasses

        all_fields = dataclasses.fields(left)
        fields_to_check = [info.name for info in all_fields if info.compare]
    elif isattrs(left):
        all_fields = left.__attrs_attrs__
        fields_to_check = [field.name for field in all_fields if getattr(field, "eq")]
    elif isnamedtuple(left):
        fields_to_check = left._fields
    else:
        assert False

    indent = "  "
    same = []
    diff = []
    for field in fields_to_check:
        if getattr(left, field) == getattr(right, field):
            same.append(field)
        else:
            diff.append(field)

    explanation = []
    if same or diff:
        explanation += [""]
    if same and verbose < 2:
        explanation.append(f"Omitting {len(same)} identical items, use -vv to show")
    elif same:
        explanation += ["Matching attributes:"]
        explanation += highlighter(pprint.pformat(same)).splitlines()
    if diff:
        explanation += ["Differing attributes:"]
        explanation += highlighter(pprint.pformat(diff)).splitlines()
        for field in diff:
            field_left = getattr(left, field)
            field_right = getattr(right, field)
            explanation += [
                "",
                f"Drill down into differing attribute {field}:",
                f"{indent}{field}: {highlighter(repr(field_left))} != {highlighter(repr(field_right))}",
            ]
            explanation += [
                indent + line
                for line in _compare_eq_any(
                    field_left, field_right, highlighter, verbose
                )
            ]
    return explanation
