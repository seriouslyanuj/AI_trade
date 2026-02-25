
import time

def now_ms() -> float:
    return time.perf_counter() * 1000.0

def epoch_ms() -> int:
    return int(time.time() * 1000)
