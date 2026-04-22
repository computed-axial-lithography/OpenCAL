import time
from typing import final

from pi5neo.pi5neo import Pi5Neo, EPixelType

from opencal.utils.config import LedArrayConfig


@final
class LEDArray:
    def __init__(self, config: LedArrayConfig):
        """
        Initialize the LED array using configuration from a JSON file.
        :param config_file: Path to the configuration JSON file
        """
        # Load configuration from the specified JSON file

        self.num_led: int = config.num_led  # Number of LEDs in the array

        # Retrieve the pin values and indices for the LED ring from the configuration
        self.ring_indices = config.ring_indices
        self.default_color = config.default_color

        # Initialize communication with the Pi5Neo library
        self.neo: Pi5Neo = Pi5Neo("/dev/spidev0.0", self.num_led, 800, pixel_type=EPixelType.RGBW)

    def set_led(
        self, color: tuple[int, int, int], led_index: list[int] | None = None, update: bool = True
    ):
        """
        Set the specified LEDs to a given RGB color.

        :param color: (G, R, B)
        :param led_index: List of indices to update (or all LEDs if not specified)
        """
        if led_index is None:
            self.neo.fill_strip(*color)

        else:
            for idx in led_index:
                _ = self.neo.set_led_color(idx, *color)  # Set the color for specified indices
        if update:
            self.neo.update_strip()  # Update the LED strip to apply changes

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
            self.set_led((255, 255, 0), group_1, update=False)
            self.set_led((0, 0, 255), group_2)
            time.sleep(DELAY)

            self.set_led((0, 0, 255), group_1, update=False)
            self.set_led((255, 255, 0), group_2)
            time.sleep(DELAY)

        self.clear_leds()


if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    led_array = LEDArray(cfg.led_array)

    try:
        led_array.clear_leds()
        time.sleep(1)
        led_array.set_led((255, 0, 0))  # Set all LEDs to red
        time.sleep(10)  # Keep the LEDs on for 10 seconds

        led_array.clear_leds()  # Clear the LEDs after the test

    except Exception as e:
        print(f"An error occurred during the test: {e}")
