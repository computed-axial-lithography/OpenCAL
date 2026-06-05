from __future__ import annotations

from typing import TYPE_CHECKING, final, override

import pygame

from opencal.gui.modes.base import BasePygameMode

if TYPE_CHECKING:
    from opencal.gui.pygame_app import PygameApp


@final
class VialWidthMode(BasePygameMode):
    """Interactive vial-width measurement mode.

    The rotary encoder adjusts the width of a centered white vertical bar.
    The bar spans the full screen height and its pixel width is shown as
    an overlay so the user can read the value before confirming.
    Pressing the button confirms and exits with {"vial_width": <px_width>}.
    """

    SCROLL_RATIO = 2
    INITIAL_WIDTH = 200

    def __init__(self, app: "PygameApp") -> None:
        super().__init__(app)
        self.rect_width: int = self.INITIAL_WIDTH
        self._font: pygame.font.Font | None = None

    @override
    def on_activate(self) -> None:
        self.rect_width = self.INITIAL_WIDTH
        self._font = pygame.font.Font(None, 60)

    @override
    def on_deactivate(self) -> None:
        self._font = None

    @override
    def on_encoder_delta(self, delta: int) -> None:
        self.rect_width = max(0, self.rect_width + delta * self.SCROLL_RATIO)

    @override
    def on_button(self) -> None:
        self.app.signal_done({"vial_width": self.rect_width})

    @override
    def on_frame(self, surf: pygame.Surface) -> None:
        surf.fill((0, 0, 0))
        w, h = surf.get_size()

        # Vertical bar: full height, adjustable width, centred
        left = w // 2 - self.rect_width // 2
        pygame.draw.rect(surf, "white", (left, 0, self.rect_width, h))

        # Pixel count overlay (yellow so it's visible against the white bar)
        if self._font:
            label = self._font.render(f"{self.rect_width} px", True, (255, 255, 0))
            surf.blit(label, (10, 10))
