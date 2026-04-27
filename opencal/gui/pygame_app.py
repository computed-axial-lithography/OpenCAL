import queue
import threading
import time
from typing import final

import pygame
from opencal.utils.config import PygameConfig


@final
class PygameApp:
    def __init__(
        self,
        config: PygameConfig,
        encoder_q: queue.Queue[int],
        pygame_q: queue.Queue[tuple[str, str]],
        stop_event: threading.Event,
        video_playing: threading.Event,
        fps: int = 30,
    ):
        self.active = config.active
        self.encoder_q = encoder_q
        self.pygame_q = pygame_q
        self.stop_event = stop_event
        self.video_playing = video_playing
        self.fps = fps
        self._running = False
        self.rect_height = 100
        self.width = 1920
        self.height = 1080

    def run(self):
        if not self.active:
            print("WARNING: PyGame deactivated from config, skipping PyGame init.")
            return

        while not self.stop_event.is_set():
            # FIXME: Do we need the result of pygame.init()?
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

                while not self.encoder_q.empty():
                    try:
                        delta = self.encoder_q.get_nowait()
                        self.on_encoder_delta(delta)
                    except queue.Empty:
                        break

                _ = screen.fill((0, 0, 0))
                self.on_frame(screen)
                pygame.display.flip()
                _ = clock.tick(self.fps)

            pygame.quit()

            if not self._running or self.stop_event.is_set():
                break

            while self.video_playing.is_set():
                if self.stop_event.is_set():
                    return
                time.sleep(0.1)

    def on_encoder_delta(self, delta: int):
        """Called when the rotary encoder turns while pygame mode is active. Override to respond."""
        self.rect_height = max(0, self.rect_height + delta)

    def on_frame(self, surf: pygame.Surface):
        """Called once per frame. Override to draw visuals."""

        rect_width = 1000
        left = self.width / 2 - rect_width / 2
        top = self.height / 2 - self.rect_height / 2
        pygame.draw.rect(surf, "white", (left, top, rect_width, self.rect_height))

    def send_to_gui(self, key: str, value: str):
        """Publish a key-value pair to the GUI thread."""
        self.pygame_q.put((key, value))

    def signal_done(self, result: dict | None = None):
        """Signal LCDGui that this pygame screen is finished.

        LCDGui will call the PyGameMenu's on_exit_callback with result, then
        pop the PyGameMenu off the stack, returning control to the LCD menu.
        """
        self.pygame_q.put(("done", result or {}))

    def stop(self):
        self._running = False
