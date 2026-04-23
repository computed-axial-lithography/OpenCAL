import queue
import threading

import pygame


class PygameApp:
    def __init__(
        self,
        encoder_q: queue.Queue,
        pygame_q: queue.Queue,
        stop_event: threading.Event,
        fps: int = 30,
    ):
        self.encoder_q = encoder_q
        self.pygame_q = pygame_q
        self.stop_event = stop_event
        self.fps = fps
        self._running = False
        self.rect_height = 100
        self.width = 1920
        self.height = 1080

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = screen.get_size()
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
        self.rect_height = max(0, self.rect_height + delta)

    def on_frame(self, surf: pygame.Surface):
        """Called once per frame. Override to draw visuals."""
        rect = surf.get_bounding_rect()
        
        rect_width = 1000
        left = self.width / 2 - rect_width / 2
        top = self.height / 2 - self.rect_height / 2
        pygame.draw.rect(surf, 'white', (left, top, rect_width, self.rect_height))

    def send_to_gui(self, key: str, value):
        """Publish a key-value pair to the GUI thread (stored in LCDGui.pygame_values)."""
        self.pygame_q.put((key, value))

    def stop(self):
        self._running = False
