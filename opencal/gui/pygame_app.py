import queue
import threading
import time
from typing import Any, final

import pygame

from opencal.gui.events import ActivateEvent, ButtonEvent, DeactivateEvent, EncoderEvent, InputEvent
from opencal.gui.modes.base import BasePygameMode
from opencal.gui.modes.vial_width import VialWidthMode
from opencal.gui.modes.calibration import CalibrationMode
from opencal.utils.config import PygameConfig


@final
class PygameApp:
    def __init__(
        self,
        config: PygameConfig,
        input_q: queue.Queue[InputEvent],
        pygame_q: queue.Queue[tuple[str, Any]],
        stop_event: threading.Event,
        video_playing: threading.Event,
        fps: int = 30,
    ):
        self.active = config.active
        self.input_q: queue.Queue[InputEvent] = input_q
        self.pygame_q = pygame_q
        self.stop_event = stop_event
        self.video_playing = video_playing
        self.fps = fps
        self._running = False
        self.width = 1920
        self.height = 1080
        self._active_mode: BasePygameMode | None = None
        self._mode_registry: dict[str, type[BasePygameMode]] = {
            "vial_width": VialWidthMode,
            "calibration": CalibrationMode,
        }

    def run(self):
        if not self.active:
            print("WARNING: PyGame deactivated from config, skipping PyGame init.")
            return

        while not self.stop_event.is_set():
            _ = pygame.init()
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.width, self.height = screen.get_size()
            clock = pygame.time.Clock()
            self._running = True

            while self._running and not self.stop_event.is_set():
                if self.video_playing.is_set():
                    break

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._running = False

                while not self.input_q.empty():
                    try:
                        msg = self.input_q.get_nowait()
                        self._dispatch(msg)
                    except queue.Empty:
                        break

                _ = screen.fill((0, 0, 0))
                if self._active_mode is not None:
                    self._active_mode.on_frame(screen)
                pygame.display.flip()
                _ = clock.tick(self.fps)

            pygame.quit()

            if not self._running or self.stop_event.is_set():
                break

            while self.video_playing.is_set():
                if self.stop_event.is_set():
                    return
                time.sleep(0.1)

    def _dispatch(self, msg: InputEvent) -> None:
        match msg:
            case EncoderEvent(delta=d):
                if self._active_mode is not None:
                    self._active_mode.on_encoder_delta(d)
            case ButtonEvent():
                if self._active_mode is not None:
                    self._active_mode.on_button()
            case ActivateEvent(mode_name=name, kwargs=kw):
                mode_cls = self._mode_registry.get(name)
                if mode_cls is None:
                    print(f"WARNING: Unknown pygame mode '{name}'")
                    return
                if self._active_mode is not None:
                    self._active_mode.on_deactivate()
                self._active_mode = mode_cls(app=self, **kw)
                self._active_mode.on_activate()
            case DeactivateEvent():
                if self._active_mode is not None:
                    self._active_mode.on_deactivate()
                self._active_mode = None

    def send_to_gui(self, key: str, value: Any):
        """Publish a key-value pair to the GUI thread."""
        self.pygame_q.put((key, value))

    def signal_done(self, result: dict | None = None):
        """Signal LCDGui that the active mode is finished.

        LCDGui will call the PyGameMenu's on_exit_callback with result, then
        pop the PyGameMenu off the stack, returning control to the LCD menu.
        """
        self.pygame_q.put(("done", result or {}))

    def stop(self):
        self._running = False
