from typing import Any

from ..notes.bpm import Bpm
from ..notes.holodorievents import HolodoriFeverEnd, HolodoriFeverStart, HolodoriSkill
from .errors import AwadoriFormatError
from .nodes import read_number, read_tick
from .timing import tick_to_beat

DEFAULT_BPM = 120.0
MIN_BPM = 0.001
MAX_BPM = 100000.0


def _section(events: dict, key: str) -> list:
    value = events.get(key, [])
    if not isinstance(value, list):
        raise AwadoriFormatError(f"score.events.{key}: expected an array")
    return value


def _bpms(events: dict) -> list[Bpm]:
    points: list[tuple[int, float]] = []
    for index, raw in enumerate(_section(events, "bpm")):
        where = f"score.events.bpm[{index}]"
        if not isinstance(raw, dict):
            raise AwadoriFormatError(f"{where}: expected an object")
        value = read_number(raw.get("bpm", DEFAULT_BPM), f"{where}.bpm")
        if not MIN_BPM <= value <= MAX_BPM:
            raise AwadoriFormatError(f"{where}.bpm: out of range")
        points.append((read_tick(raw.get("t"), f"{where}.t"), value))
    points.sort(key=lambda point: point[0])
    if not points or points[0][0] > 0:
        points.insert(0, (0, DEFAULT_BPM))
    return [Bpm(beat=tick_to_beat(tick), bpm=value) for tick, value in points]


def _skills(events: dict) -> list[HolodoriSkill]:
    return [
        HolodoriSkill(
            beat=tick_to_beat(read_tick(raw, f"score.events.skill[{index}]")),
            slot=index + 1,
        )
        for index, raw in enumerate(_section(events, "skill"))
    ]


def _fevers(events: dict) -> list[HolodoriFeverStart | HolodoriFeverEnd]:
    fevers: list[HolodoriFeverStart | HolodoriFeverEnd] = []
    for index, raw in enumerate(_section(events, "fever")):
        where = f"score.events.fever[{index}]"
        if not isinstance(raw, list) or len(raw) != 2:
            raise AwadoriFormatError(f"{where}: expected a [start, end] array")
        start = read_tick(raw[0], f"{where}[0]")
        end = read_tick(raw[1], f"{where}[1]")
        if end < start:
            raise AwadoriFormatError(f"{where}: end precedes start")
        fevers.append(HolodoriFeverStart(beat=tick_to_beat(start)))
        fevers.append(HolodoriFeverEnd(beat=tick_to_beat(end)))
    return fevers


def build_events(events: Any) -> list:
    if events is None:
        events = {}
    if not isinstance(events, dict):
        raise AwadoriFormatError("score.events: expected an object")
    return [*_bpms(events), *_skills(events), *_fevers(events)]
