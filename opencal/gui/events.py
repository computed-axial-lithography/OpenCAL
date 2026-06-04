from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EncoderEvent:
    delta: int


@dataclass(frozen=True)
class ButtonEvent:
    pass


@dataclass(frozen=True)
class ActivateEvent:
    mode_name: str
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeactivateEvent:
    pass


InputEvent = EncoderEvent | ButtonEvent | ActivateEvent | DeactivateEvent
