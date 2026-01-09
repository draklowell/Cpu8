from dataclasses import dataclass
from enum import StrEnum


class State(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"
    FLOATING = "FLOATING"
    CONFLICT = "CONFLICT"


class LogLevel(StrEnum):
    INFO = "INFO"
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class WaveformChunk:
    network_drivers: dict[str, list[str]]
    network_states: dict[str, State]
    logs: list[tuple[LogLevel, str, str]]
    tick: int
    clock: bool
    wait: bool
    reset: bool
    halt: bool
