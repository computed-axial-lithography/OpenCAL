from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, override

import pygame

from opencal.gui.modes.base import BasePygameMode

if TYPE_CHECKING:
    from opencal.gui.pygame_app import PygameApp

_STEP_PX = 5  # pixels moved per encoder click (~0.45 mm at 90 µm/pixel)


@final
class AlignmentMode(BasePygameMode):
    """Displays the alignment tool image with live vertical translation.

    Rotate encoder up/down to shift the image transversely.
    Press button to exit.
    """

    def __init__(self, app: "PygameApp", image_path: str | Path) -> None:
        super().__init__(app)
        self._image_path = Path(image_path)
        self._surface: pygame.Surface | None = None
        self._y_offset: int = 0

    @override
    def on_activate(self) -> None:
        self._y_offset = 0
        raw = pygame.image.load(str(self._image_path)).convert()
        # Image is portrait (1080×1920); rotate 90° CCW so it fills the
        # landscape pygame surface — compositor Transform 270 (90° CW) undoes this.
        rotated = pygame.transform.rotate(raw, 90)
        self._surface = pygame.transform.scale(rotated, (self.app.width, self.app.height))

    @override
    def on_deactivate(self) -> None:
        self._surface = None

    @override
    def on_encoder_delta(self, delta: int) -> None:
        self._y_offset += delta * _STEP_PX

    @override
    def on_button(self) -> None:
        self.app.signal_done()

    @override
    def on_frame(self, surf: pygame.Surface) -> None:
        surf.fill((0, 0, 0))
        if self._surface is not None:
            _ = surf.blit(self._surface, (0, self._y_offset))
