import queue
import threading

import pygame


class PygameApp:
    def __init__(
        self,
        encoder_q: queue.Queue,
        pygame_q: queue.Queue,
        stop_event: threading.Event,
        width: int = 1280,
        height: int = 720,
        fps: int = 60,
    ):
        self.encoder_q = encoder_q
        self.pygame_q = pygame_q
        self.stop_event = stop_event
        self.width = width
        self.height = height
        self.fps = fps
        self._running = False

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        clock = pygame.time.Clock()
        self._running = True

        while self._running and not self.stop_event.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False

            while not self.encoder_q.empty():
                try:
                    delta = self.encoder_q.get_nowait()
                    self.on_encoder_delta(delta)
                except queue.Empty:
                    break

            screen.fill((0, 0, 0))
            self.on_frame(screen)
            pygame.display.flip()
            clock.tick(self.fps)

        pygame.quit()

    def on_encoder_delta(self, delta: int):
        """Called when the rotary encoder turns while pygame mode is active. Override to respond."""
        pass

    def on_frame(self, surface: pygame.Surface):
        """Called once per frame. Override to draw visuals."""
        pass

    def send_to_gui(self, key: str, value):
        """Publish a key-value pair to the GUI thread (stored in LCDGui.pygame_values)."""
        self.pygame_q.put((key, value))

    def stop(self):
        self._running = False
