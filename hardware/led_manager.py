import board
import neopixel
import json
import time

class LEDArray:
    def __init__(self, config_file="utils\\config.json"):
        # Load config from json
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.num_led = config['led_array'].get("num_led")
        
        # Retrieve the pin value from config, and set it for neopixel
        self.led_pin = getattr(board, config['led_array'].get("led_pin"))
        self.ring_indices = config['led_array'].get("ring_indices", {})

        # Initialize communication with neopixel library
        self.pixels = neopixel.NeoPixel(self.led_pin, self.num_led, brightness=0.5, auto_write=False)

    def set_led(self, color_rgb, ring_num):
        """
        Turns on all LEDs in the specified ring and preceding rings.
        Args:
            color_rgb (tuple): RGB values as (R, G, B).
            ring_num (int): The ring number to turn on (1-indexed).
        """
        if ring_num < 1 or ring_num > len(self.ring_indices):
            print(f"Invalid ring number: {ring_num}. Must be between 1 and {len(self.ring_indices)}.")
            return

        # Turn on LEDs for the specified ring and all preceding rings
        for r in range(1, ring_num + 1):
            indices = self.ring_indices.get(str(r), [])
            for idx in indices:
                self.pixels[idx] = color_rgb
        
        # Update the LEDs by writing the changes
        self.pixels.show()

    def clear_leds(self):
        """
        Turns off all LEDs in the array.
        """
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

if __name__ == "__main__":
    led_array = LEDArray()

    try:
        # Clear all LEDs before starting the test
        print("Clearing all LEDs...")
        led_array.clear_leds()

        # Set rings 1-3 to red
        print("Turning on rings 1-3 with red color...")
        led_array.set_led((255, 0, 0), 3)  # Ring 3 will include rings 1 and 2

        # Keep the LEDs on for a while for observation
        time.sleep(5)

        # Clear LEDs after the test
        print("Clearing LEDs...")
        led_array.clear_leds()

    except Exception as e:
        print(f"An error occurred during the test: {e}")
