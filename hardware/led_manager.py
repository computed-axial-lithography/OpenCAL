import json
import time
try:
    from pi5neo import Pi5Neo # type: ignore
except ImportError as e:
    print(e)

class LEDArray:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        # Load config from json
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.num_led = config['led_array'].get("num_led")
        
        # Retrieve the pin value from config, and set it for neopixel
        self.ring_indices = config['led_array'].get("ring_indices", {})

        self.default_color = config['led_array'].get("ring_indices", [])

        # Initialize communication with pi5neo library
        self.neo = Pi5Neo('/dev/spidev0.0', self.num_led, 800) #using pin 19, GPIO 10

    def set_led(self, color_rgb, led_index = [], set_all = True):
        """
        Turns on LEDs at the specified index, or all LEDs if set_all is True.
        Args:
            color_rgb (tuple): RGB values as (R, G, B).
            led_index (list): List of LED indices to turn on.
            set_all (bool): If True, turn on all LEDs.
        """
        if set_all:
            print("Turning on all LEDs...")
            for idx in range(self.num_led):
                self.neo.set_led_color(idx, *color_rgb)
            
        else:
            print(f"Turning on LEDs at indices: {led_index}")   
            for idx in led_index:
                self.neo.set_led_color(idx, *color_rgb) 
        self.neo.update_strip()
        print("LEDs updated.")


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

        print("Turning on all LEDs to red for 10 seconds...")
        led_array.set_led((255, 0, 0), set_all = True)   
        time.sleep(10)

        print("Clearing LEDs...")
        led_array.clear_leds()

    except Exception as e:
        print(f"An error occurred during the test: {e}")
