import os
from typing import IO

from ..notes.metadata import MetaData
from ..notes.score import Score
from ..notes.timescale import TimeScaleGroup, TimeScalePoint
from .builders import build_note, collect_body_ranges
from .decode import decode_document, read_source
from .errors import AwadoriFormatError
from .events import build_events
from .timing import TICKS_PER_BEAT


def _time_scale_group() -> TimeScaleGroup:
    group = TimeScaleGroup()
    group.append(TimeScalePoint(beat=0.0, timeScale=1.0))
    return group


def _to_score(
    document: dict, guide_traces: bool, trace_ends: bool, flick_body_collide: bool
) -> Score:
    section = document.get("score")
    if not isinstance(section, dict):
        raise AwadoriFormatError("score: expected an object")
    raw_notes = section.get("notes", [])
    if not isinstance(raw_notes, list):
        raise AwadoriFormatError("score.notes: expected an array")
    body_ranges = collect_body_ranges(raw_notes) if flick_body_collide else ()
    notes = build_events(section.get("events"))
    notes.append(_time_scale_group())
    for index, raw in enumerate(raw_notes):
        notes.extend(
            build_note(
                raw, f"score.notes[{index}]", guide_traces, trace_ends, body_ranges
            )
        )
    metadata = MetaData(
        title="",
        artist="",
        designer="",
        waveoffset=0,
        requests=[f"ticks_per_beat {TICKS_PER_BEAT}"],
    )
    score = Score(metadata=metadata, notes=notes)
    score.sort_by_beat()
    return score


def load(
    source: os.PathLike | IO[bytes] | bytes | str,
    *,
    guide_traces: bool = True,
    trace_ends: bool = True,
    flick_body_collide: bool = True,
) -> Score:
    return loads(
        read_source(source),
        guide_traces=guide_traces,
        trace_ends=trace_ends,
        flick_body_collide=flick_body_collide,
    )


def loads(
    data: bytes | str,
    *,
    guide_traces: bool = True,
    trace_ends: bool = True,
    flick_body_collide: bool = True,
) -> Score:
    return _to_score(
        decode_document(data), guide_traces, trace_ends, flick_body_collide
    )
