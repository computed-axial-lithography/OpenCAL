from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from opencal.gui.modes.base import BasePygameMode

if TYPE_CHECKING:
    from opencal.gui.pygame_app import PygameApp


class CalibrationMode(BasePygameMode):
    """Displays a calibration PNG fullscreen on the pygame surface.

    Replaces the mpv-based display_image() path for static calibration images.
    Pressing the button exits with no result payload.
    """

    def __init__(self, app: "PygameApp", image_path: str | Path) -> None:
        super().__init__(app)
        self._image_path = Path(image_path)
        self._surface: pygame.Surface | None = None

    def on_activate(self) -> None:
        raw = pygame.image.load(str(self._image_path)).convert()
        self._surface = pygame.transform.scale(raw, (self.app.width, self.app.height))

    def on_deactivate(self) -> None:
        self._surface = None

    def on_frame(self, surf: pygame.Surface) -> None:
        if self._surface is not None:
            surf.blit(self._surface, (0, 0))
