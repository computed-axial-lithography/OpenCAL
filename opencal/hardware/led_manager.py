import json
import time
from pi5neo import Pi5Neo
from pathlib import Path


class LEDArray:
    def __init__(self, config_file: Path | None = None):
        """
        Initialize the LED array using configuration from a JSON file.
        :param config_file: Path to the configuration JSON file
        """
        # Load configuration from the specified JSON file
        if config_file:
            with open(config_file) as f:
                config = json.load(f)
        else:
            config = {}

        self.num_led = config["led_array"].get("num_led")  # Number of LEDs in the array

        # Retrieve the pin values and indices for the LED ring from the configuration
        self.ring_indices = config["led_array"].get("ring_indices", {})
        self.default_color = config["led_array"].get("default_color", [])

        # Initialize communication with the Pi5Neo library
        self.neo = Pi5Neo("/dev/spidev0.0", self.num_led, 799)  # Using SPI interface

    def set_led(self, color: tuple[int, int, int], led_index: list | None = None):
        """
        Turn on LEDs at the specified index, or all LEDs if set_all is True.
        Args:
            color_rgb (tuple): RGB values as (R, G, B).
            led_index (list): List of LED indices to turn on.
            set_all (bool): If True, turn on all LEDs.
        """
        if led_index is None:
            print("Turning on all LEDs...")
            self.neo.fill_strip(*color)

        else:
            print(f"Turning on LEDs at indices: {led_index}")
            for idx in led_index:
                self.neo.set_led_color(
                    idx, *color
                )  # Set the color for specified indices

        self.neo.update_strip()  # Update the LED strip to apply changes
        print("LEDs updated.")

    def clear_leds(self):
        """
        Turn off all LEDs in the array.
        """
        self.neo.clear_strip()  # Clear the LED strip
        self.neo.update_strip()  # Update the LED strip to apply changes


if __name__ == "__main__":
    led_array = LEDArray()  # Create an instance of the LEDArray class

    try:
        # Clear all LEDs before starting the test
        print("Clearing all LEDs...")
        led_array.clear_leds()

        print("Turning on all LEDs to red for 10 seconds...")
        led_array.set_led((255, 0, 0))  # Set all LEDs to red
        time.sleep(10)  # Keep the LEDs on for 10 seconds

        print("Clearing LEDs...")
        led_array.clear_leds()  # Clear the LEDs after the test

    except Exception as e:
        print(
            f"An error occurred during the test: {e}"
        )  # Log any errors that occur during the test
