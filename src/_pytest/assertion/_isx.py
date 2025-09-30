from __future__ import annotations

import collections.abc
from typing import Any


def issequence(x: Any) -> bool:
    return isinstance(x, collections.abc.Sequence) and not isinstance(x, str)


def istext(x: Any) -> bool:
    return isinstance(x, str)


def isdict(x: Any) -> bool:
    return isinstance(x, dict)


def isnamedtuple(obj: Any) -> bool:
    return isinstance(obj, tuple) and getattr(obj, "_fields", None) is not None


def isdatacls(obj: Any) -> bool:
    return getattr(obj, "__dataclass_fields__", None) is not None


def isattrs(obj: Any) -> bool:
    return getattr(obj, "__attrs_attrs__", None) is not None


def isiterable(obj: Any) -> bool:
    try:
        iter(obj)
        return not istext(obj)
    except Exception:
        return False
