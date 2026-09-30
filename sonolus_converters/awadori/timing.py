TICKS_PER_BEAT = 480


def tick_to_beat(tick: int) -> float:
    return round(tick / TICKS_PER_BEAT, 6)
