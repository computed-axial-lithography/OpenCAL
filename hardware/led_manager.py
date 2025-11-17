import json
import time
from pi5neo import Pi5Neo


class LEDArray:
    def __init__(self, config_file=None):
        """
        Initialize the LED array using configuration from a JSON file.
        :param config_file: Path to the configuration JSON file
        """
        
        with open(config_file) as f:
            config = json.load(f)

        self.num_led = config['led_array'].get("num_led")
        self.ring_indices = config['led_array'].get("ring_indices", {})
        self.default_color = config['led_array'].get("default_color", [])
        self.pixels = Pi5Neo(num_leds=self.num_led)

    def set_led(self, color: tuple[int], led_index: list[int] | None = None):
        """
        Set the specified LEDs to a given RGB color.
        
        :param color: (G, R, B)
        :param led_index: List of indices to update (or all LEDs if not specified)
        """
        # TODO: implement logging

        print("Turning on all LEDs...")
        if led_index is None:
            self.pixels.fill_strip(*color)
        else:
            for i in led_index:
                self.pixels.set_led_color(i, *color)

        self.pixels.update_strip()
        print("LEDs updated.")

    def clear_leds(self):
        """Turn off all LEDs."""
        print("Clearing all LEDs...")
        self.pixels.clear_strip()
        self.pixels.update_strip()

if __name__ == "__main__":
    led_array = LEDArray(config_file="/home/opencal/opencal/OpenCAL/utils/config.json")

    try:
        led_array.clear_leds()
        time.sleep(1)
        print("Turning on all LEDs to red for 10 seconds...")
        led_array.set_led((0, 255, 0), set_all=True)
        time.sleep(3)
        #led_array.clear_leds()
    except Exception as e:
        print(f"An error occurred: {e}")
