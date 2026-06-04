from __future__ import annotations

import abc
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from opencal.gui.pygame_app import PygameApp


class BasePygameMode(abc.ABC):
    """Base class for a single interactive pygame mode.

    Subclasses override on_frame() (required), and optionally on_encoder_delta(),
    on_button(), on_activate(), and on_deactivate().

    Modes signal completion by calling self.app.signal_done(result), which puts
    ("done", result) on pygame_q and causes LCDGui to fire the exit callback and
    pop the PyGameMenu.
    """

    def __init__(self, app: "PygameApp") -> None:
        self.app = app

    def on_activate(self) -> None:
        """Called once when this mode becomes the active mode. Reset per-run state here."""
        pass

    def on_deactivate(self) -> None:
        """Called once when this mode is torn down. Release resources here."""
        pass

    def on_encoder_delta(self, delta: int) -> None:
        """Called each time the rotary encoder turns while this mode is active."""
        pass

    def on_button(self) -> None:
        """Called when the encoder button is pressed. Default: exit the mode."""
        self.app.signal_done()

    @abc.abstractmethod
    def on_frame(self, surf: pygame.Surface) -> None:
        """Called once per frame after the surface is cleared to black. Draw here."""
        ...
