import time
from typing import final

from pi5neo import Pi5Neo

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
        self.neo: Pi5Neo = Pi5Neo(
            "/dev/spidev0.0", self.num_led, 799
        )  # Using SPI interface

    def set_led(self, color: tuple[int, int, int], led_index: list[int] | None = None):
        """
        Set the specified LEDs to a given RGB color.

        :param color: (G, R, B)
        :param led_index: List of indices to update (or all LEDs if not specified)
        """
        if led_index is None:
            print("Turning on all LEDs...")
            self.neo.fill_strip(*color)

        else:
            print(f"Turning on LEDs at indices: {led_index}")
            for idx in led_index:
                _ = self.neo.set_led_color(
                    idx, *color
                )  # Set the color for specified indices

        self.neo.update_strip()  # Update the LED strip to apply changes
        print("LEDs updated.")

    def clear_leds(self):
        """Turn off all LEDs."""
        print("Clearing all LEDs...")
        self.neo.clear_strip()
        self.neo.update_strip()


if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    led_array = LEDArray(cfg.led_array)

    try:
        led_array.clear_leds()
        time.sleep(1)
        print("Turning on all LEDs to red for 10 seconds...")
        led_array.set_led((255, 0, 0))  # Set all LEDs to red
        time.sleep(10)  # Keep the LEDs on for 10 seconds

        print("Clearing LEDs...")
        led_array.clear_leds()  # Clear the LEDs after the test

    except Exception as e:
        print(
            f"An error occurred during the test: {e}"
        )  # Log any errors that occur during the test
