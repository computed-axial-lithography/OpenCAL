import time
from typing import final

from pi5neo.pi5neo import Pi5Neo, EPixelType

from opencal.utils.config import LedArrayConfig

# SK6812 RGBW byte order: (G, R, B, W)
# R is driven at 180 rather than 255 to minimise W-LED crosstalk bleed.
RED   = (0, 240, 0, 0)
GREEN = (255, 0, 0, 0)
BLUE  = (0, 0, 180, 0)
WHITE = (0, 0, 0, 255)
OFF   = (0, 0, 0, 0)


@final
class LEDManager:
    def __init__(self, config: LedArrayConfig):
        self.num_led: int = config.num_led
        self.default_color: tuple[int, int, int, int] = config.default_color

        self.neo: Pi5Neo = Pi5Neo("/dev/spidev0.0", self.num_led, 800, pixel_type=EPixelType.RGBW)
        self.clear_leds()

    def set_led(
        self,
        color: tuple[int, int, int, int],
        led_index: list[int] | None = None,
        update: bool = True,
    ):
        """Set LEDs to a color. color = (G, R, B, W) per SK6812 RGBW byte order."""
        if led_index is None:
            self.neo.fill_strip(*color)
        else:
            for idx in led_index:
                _ = self.neo.set_led_color(idx, *color)
        if update:
            self.neo.update_strip()

    def clear_leds(self):
        """Turn off all LEDs."""
        self.neo.clear_strip()
        self.neo.update_strip()

    def run_start_animation(self):
        CYCLES = 5
        DELAY = 0.5
        ROWS, COLS = 8, 8

        group_1: list[int] = []
        group_2: list[int] = []

        for i in range(ROWS):
            for j in range(COLS):
                k = i // 2 + j // 2
                idx = i * COLS + j
                if k % 2 == 0:
                    group_1.append(idx)
                else:
                    group_2.append(idx)

        for _ in range(CYCLES):
            self.set_led(RED, group_1, update=False)
            self.set_led(WHITE, group_2)
            time.sleep(DELAY)

            self.set_led(WHITE, group_1, update=False)
            self.set_led(RED, group_2)
            time.sleep(DELAY)

        self.clear_leds()


if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    led_array = LEDManager(cfg.led_array)

    try:
        led_array.clear_leds()
        time.sleep(1)
        led_array.set_led(RED)
        time.sleep(10)
        led_array.clear_leds()
    except Exception as e:
        print(f"An error occurred during the test: {e}")
