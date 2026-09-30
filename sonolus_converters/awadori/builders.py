from dataclasses import replace
from typing import Iterator, Literal

from ..notes.guide import Guide, GuidePoint
from ..notes.single import Single
from ..notes.slide import Slide, SlideEndPoint, SlideRelayPoint, SlideStartPoint
from .geometry import (
    COLLIDE_TICK_TOLERANCE,
    ranges_overlap,
    resolve_auto,
    to_lane,
    to_size,
)
from .nodes import Node, read_line, read_node, read_type
from .timing import tick_to_beat

Judge = Literal["normal", "trace", "none"]


def _judge(node: Node) -> Judge:
    if not node.visible:
        return "none"
    if node.kind == "trace":
        return "trace"
    return "normal"


def _end_judge(node: Node, trace_ends: bool) -> Judge:
    if not node.visible:
        return "none"
    if trace_ends or node.kind == "trace":
        return "trace"
    return "normal"


def _collides(node: Node, ranges: tuple[tuple[int, float, float], ...]) -> bool:
    return any(
        abs(node.tick - tick) <= COLLIDE_TICK_TOLERANCE
        and ranges_overlap(node.left, node.width, left, width)
        for tick, left, width in ranges
    )


def _single(
    node: Node, trace_flick_ranges: tuple[tuple[int, float, float], ...] = ()
) -> Single:
    trace = node.kind == "trace" or (
        node.kind == "flick" and _collides(node, trace_flick_ranges)
    )
    return Single(
        beat=tick_to_beat(node.tick),
        critical=node.critical,
        lane=to_lane(node.left, node.width),
        size=to_size(node.width),
        timeScaleGroup=0,
        trace=trace,
        direction=node.direction if node.kind == "flick" else None,
    )


def _slide(nodes: list[Node], trace_ends: bool) -> Slide:
    resolve_auto(nodes)
    critical = any(node.critical for node in nodes)
    last = len(nodes) - 1
    slide = Slide(critical=critical)
    for index, node in enumerate(nodes):
        beat = tick_to_beat(node.tick)
        lane = to_lane(node.left, node.width)
        size = to_size(node.width)
        if index == 0:
            slide.connections.append(
                SlideStartPoint(
                    beat=beat,
                    critical=critical,
                    ease=node.ease_left,
                    judgeType=_judge(node),
                    lane=lane,
                    size=size,
                    timeScaleGroup=0,
                )
            )
        elif index == last:
            slide.connections.append(
                SlideEndPoint(
                    beat=beat,
                    critical=critical,
                    judgeType=_end_judge(node, trace_ends),
                    lane=lane,
                    size=size,
                    timeScaleGroup=0,
                    direction=node.direction if node.kind == "flick" else None,
                )
            )
        else:
            slide.connections.append(
                SlideRelayPoint(
                    beat=beat,
                    ease=node.ease_left,
                    lane=lane,
                    size=size,
                    timeScaleGroup=0,
                    type="attach" if node.auto else "tick",
                    critical=critical if node.auto or node.visible else None,
                )
            )
    slide.sort()
    return slide


def _fade(nodes: list[Node]) -> Literal["in", "out", "none"]:
    if nodes[0].alpha == "fadeIn":
        return "in"
    if nodes[-1].alpha == "fadeOut":
        return "out"
    return "none"


def _judged_guide_nodes(nodes: list[Node]) -> Iterator[Node]:
    last = len(nodes) - 1
    for index, node in enumerate(nodes):
        if index == 0:
            continue
        if index == last:
            if node.visible and node.kind == "trace":
                yield node
        elif node.auto or node.visible:
            yield node


def _guide(nodes: list[Node], guide_traces: bool) -> list[Guide | Single]:
    resolve_auto(nodes)
    guide = Guide(
        color="yellow" if any(node.critical for node in nodes) else "green",
        fade=_fade(nodes),
    )
    guide.midpoints.extend(
        GuidePoint(
            beat=tick_to_beat(node.tick),
            ease=node.ease_left,
            lane=to_lane(node.left, node.width),
            size=to_size(node.width),
            timeScaleGroup=0,
        )
        for node in nodes
    )
    guide.sort()
    items: list[Guide | Single] = [guide]
    if guide_traces:
        items.extend(
            _single(replace(node, kind="trace")) for node in _judged_guide_nodes(nodes)
        )
    return items


def collect_body_ranges(raw_notes: list) -> tuple[tuple[int, float, float], ...]:
    ranges: list[tuple[int, float, float]] = []
    for index, raw in enumerate(raw_notes):
        where = f"score.notes[{index}]"
        if read_type(raw, where) != "long":
            continue
        nodes = read_line(raw, where)
        resolve_auto(nodes)
        ranges.extend((node.tick, node.left, node.width) for node in nodes[1:])
    return tuple(ranges)


def build_note(
    raw: dict,
    where: str,
    guide_traces: bool = True,
    trace_ends: bool = True,
    trace_flick_ranges: tuple[tuple[int, float, float], ...] = (),
) -> list[Single | Slide | Guide]:
    note_type = read_type(raw, where)
    if note_type == "long":
        return [_slide(read_line(raw, where), trace_ends)]
    if note_type == "guide":
        return _guide(read_line(raw, where), guide_traces)
    return [_single(read_node(raw, where), trace_flick_ranges)]
