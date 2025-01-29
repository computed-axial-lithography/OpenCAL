import json
import time
from pi5neo import Pi5Neo # type: ignore

class LEDArray:
    def __init__(self, config_file="utils/config.json"):
        # Load config from json
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.num_led = config['led_array'].get("num_led")
        
        # Retrieve the pin value from config, and set it for neopixel
        self.ring_indices = config['led_array'].get("ring_indices", {})

        # Initialize communication with pi5neo library
        self.neo = Pi5Neo('/dev/spidev0.0', self.num_led, 800)

    def set_led(self, color_rgb, led_index = [], by_ring = True):
        """
        Turns on all LEDs in the specified ring and preceding rings.
        Args:
            color_rgb (tuple): RGB values as (R, G, B).
            ring_num (int): The ring number to turn on (1-indexed).
        """
        if led_index < 0 or led_index > self.num_leds:
            print(f"Invalid led index number: {led_index}")
            return

        # Turn on LEDs for the specified ring and all preceding rings
        if by_ring:
            for r in range(1, led_index + 1):
                indices = self.ring_indices.get(str(r), [])
                for idx in indices:
                    self.neo.set_led_color(idx, color_rgb)
        else:
            for idx in led_index:
                self.neo.set_led_color(idx, color_rgb)
            
        
        # Update the LEDs by writing the changes
        self.neo.update_strip()

    def clear_leds(self):
        """
        Turns off all LEDs in the array.
        """
        self.neo.clear_strip()
        self.neo.update_strip()

if __name__ == "__main__":
    led_array = LEDArray()

    try:
        # Clear all LEDs before starting the test
        print("Clearing all LEDs...")
        led_array.clear_leds()

        # Turn on each led to blue
        for i in range(led_array.num_led):
            print(f"turning on led {i}")
            led_array.set_led((0, 0, 255), [i], by_ring = False)
            time.sleep(0.1)
            led_array.clear_leds()

        # Set rings 1-9 to red
        for i in range(9):
            print(f"turning on ring {i}")
            led_array.set_led((255, 0, 0), [i], by_ring = True)
            time.sleep(1)

        # Keep the LEDs on for a while for observation
        time.sleep(5)

        # Clear LEDs after the test
        print("Clearing LEDs...")
        led_array.clear_leds()

    except Exception as e:
        print(f"An error occurred during the test: {e}")
