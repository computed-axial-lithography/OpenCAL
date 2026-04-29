from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from opencal.gui.modes.base import BasePygameMode

if TYPE_CHECKING:
    from opencal.gui.pygame_app import PygameApp


class VialWidthMode(BasePygameMode):
    """Interactive vial-width measurement mode.

    The rotary encoder adjusts the height of a centered white rectangle.
    Pressing the button confirms the measurement and exits with
    {"vial_width": <rect_height>}.
    """

    SCROLL_RATIO = 2
    RECT_WIDTH = 1000
    INITIAL_HEIGHT = 100

    def __init__(self, app: "PygameApp") -> None:
        super().__init__(app)
        self.rect_height: int = self.INITIAL_HEIGHT

    def on_activate(self) -> None:
        self.rect_height = self.INITIAL_HEIGHT

    def on_encoder_delta(self, delta: int) -> None:
        self.rect_height = max(0, self.rect_height + delta * self.SCROLL_RATIO)

    def on_button(self) -> None:
        self.app.signal_done({"vial_width": self.rect_height})

    def on_frame(self, surf: pygame.Surface) -> None:
        w, h = surf.get_size()
        left = w / 2 - self.RECT_WIDTH / 2
        top = h / 2 - self.rect_height / 2
        pygame.draw.rect(surf, "white", (left, top, self.RECT_WIDTH, self.rect_height))
