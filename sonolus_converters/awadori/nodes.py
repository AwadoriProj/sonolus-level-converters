import math
from dataclasses import dataclass
from typing import Any, Literal

from .errors import AwadoriFormatError

Kind = Literal["tap", "flick", "trace"]
Ease = Literal["linear", "in", "out"]
Direction = Literal["left", "up", "right"]
Alpha = Literal["none", "fadeIn", "fadeOut"]

NOTE_TYPES = ("tap", "flick", "trace", "long", "guide", "node")
EASES = ("linear", "in", "out")
DIRECTIONS = ("left", "up", "right")
ALPHAS = ("none", "fadeIn", "fadeOut")
DEFAULT_WIDTH = 6.0
AUTO = "auto"


@dataclass
class Node:
    tick: int
    kind: Kind
    left: float
    width: float
    critical: bool
    visible: bool
    auto: bool
    ease_left: Ease
    ease_right: Ease
    direction: Direction
    alpha: Alpha


def read_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AwadoriFormatError(f"{where}: expected a number")
    if not math.isfinite(value):
        raise AwadoriFormatError(f"{where}: expected a finite number")
    return float(value)


def read_tick(value: Any, where: str) -> int:
    number = read_number(value, where)
    if number < 0 or number != int(number):
        raise AwadoriFormatError(f"{where}: expected a non-negative integer")
    return int(number)


def read_boolean(value: Any, default: bool, where: str) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise AwadoriFormatError(f"{where}: expected a boolean")
    return value


def read_choice(value: Any, allowed: tuple[str, ...], default: str, where: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or value not in allowed:
        raise AwadoriFormatError(f"{where}: expected one of {', '.join(allowed)}")
    return value


def read_eases(value: Any, where: str) -> tuple[Ease, Ease]:
    if isinstance(value, list):
        if len(value) != 2:
            raise AwadoriFormatError(f"{where}: expected a two element array")
        return (
            read_choice(value[0], EASES, "linear", f"{where}[0]"),
            read_choice(value[1], EASES, "linear", f"{where}[1]"),
        )
    ease = read_choice(value, EASES, "linear", where)
    return ease, ease


def read_type(raw: Any, where: str) -> str:
    if not isinstance(raw, dict):
        raise AwadoriFormatError(f"{where}: expected an object")
    return read_choice(raw.get("type"), NOTE_TYPES, "tap", f"{where}.type")


def read_node(raw: Any, where: str) -> Node:
    note_type = read_type(raw, where)
    position = raw.get("pos", 0)
    auto = position == AUTO
    left = 0.0 if auto else read_number(position, f"{where}.pos")
    width = raw.get("size", DEFAULT_WIDTH)
    ease_left, ease_right = read_eases(raw.get("ease"), f"{where}.ease")
    return Node(
        tick=read_tick(raw.get("t"), f"{where}.t"),
        kind=note_type if note_type in ("flick", "trace") else "tap",
        left=left,
        width=read_number(width, f"{where}.size"),
        critical=read_boolean(raw.get("crit"), False, f"{where}.crit"),
        visible=read_boolean(raw.get("visible"), True, f"{where}.visible"),
        auto=auto,
        ease_left=ease_left,
        ease_right=ease_right,
        direction=read_choice(raw.get("dir"), DIRECTIONS, "up", f"{where}.dir"),
        alpha=read_choice(raw.get("alpha"), ALPHAS, "none", f"{where}.alpha"),
    )


def read_line(raw: dict, where: str) -> list[Node]:
    children = raw.get("node")
    if not isinstance(children, list):
        raise AwadoriFormatError(f"{where}.node: expected an array")
    nodes = [read_node(raw, where)] if "t" in raw else []
    nodes.extend(
        read_node(child, f"{where}.node[{index}]")
        for index, child in enumerate(children)
    )
    if len(nodes) < 2:
        raise AwadoriFormatError(f"{where}: a line needs at least two nodes")
    return nodes
