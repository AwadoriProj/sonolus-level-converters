from .nodes import Ease, Node

BOARD_UNITS = 24.0
SCORE_UNITS = 12.0
SCALE = SCORE_UNITS / BOARD_UNITS


def to_lane(left: float, width: float) -> float:
    return round((left + width / 2.0 - BOARD_UNITS / 2.0) * SCALE, 6)


def to_size(width: float) -> float:
    return round(width * SCALE / 2.0, 6)


def eased(progress: float, ease: Ease) -> float:
    if ease == "in":
        return progress * progress
    if ease == "out":
        return progress * (2.0 - progress)
    return progress


def interpolate(before: Node, after: Node, tick: int) -> tuple[float, float]:
    span = after.tick - before.tick
    progress = (tick - before.tick) / span if span > 0 else 0.0
    left = before.left + eased(progress, before.ease_left) * (after.left - before.left)
    before_right = before.left + before.width
    after_right = after.left + after.width
    right = before_right + eased(progress, before.ease_right) * (
        after_right - before_right
    )
    return left, right - left


def resolve_auto(nodes: list[Node]) -> None:
    last = len(nodes) - 1
    for index, node in enumerate(nodes):
        if not node.auto:
            continue
        if index == 0 or index == last:
            node.left, node.width = nodes[0].left, nodes[0].width
            continue
        before = index
        while before > 0 and nodes[before].auto:
            before -= 1
        after = index
        while after < last and nodes[after].auto:
            after += 1
        node.left, node.width = interpolate(nodes[before], nodes[after], node.tick)


COLLIDE_TICK_TOLERANCE = 4


def ranges_overlap(
    a_left: float, a_width: float, b_left: float, b_width: float
) -> bool:
    return max(a_left, b_left) < min(a_left + a_width, b_left + b_width)
