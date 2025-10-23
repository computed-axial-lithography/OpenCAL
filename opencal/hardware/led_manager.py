import json
import time
try:
    from pi5neo import Pi5Neo  # Import the Pi5Neo library for controlling NeoPixel LEDs
except ImportError as e:
    print(e)  # Print an error message if the library is not available

class LEDArray:
    def __init__(self, config_file=None):
        """
        Initialize the LED array using configuration from a JSON file.
        :param config_file: Path to the configuration JSON file
        """
        # Load configuration from the specified JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.num_led = config['led_array'].get("num_led")  # Number of LEDs in the array
        
        # Retrieve the pin values and indices for the LED ring from the configuration
        self.ring_indices = config['led_array'].get("ring_indices", {})
        self.default_color = config['led_array'].get("default_color", [])

        # Initialize communication with the Pi5Neo library
        self.neo = Pi5Neo('/dev/spidev0.0', self.num_led, 799)  # Using SPI interface

    def set_led(self, color_rgb, led_index=[], set_all=True):
        """
        Turn on LEDs at the specified index, or all LEDs if set_all is True.
        Args:
            color_rgb (tuple): RGB values as (R, G, B).
            led_index (list): List of LED indices to turn on.
            set_all (bool): If True, turn on all LEDs.
        """
        if set_all:
            print("Turning on all LEDs...")
            for idx in range(self.num_led):
                self.neo.set_led_color(idx, *color_rgb)  # Set the color for each LED
                print(*color_rgb)
            
        else:
            print(f"Turning on LEDs at indices: {led_index}")   
            for idx in led_index:
                self.neo.set_led_color(idx, *color_rgb)  # Set the color for specified indices
        
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
        led_array.set_led((255, 0, 0), set_all=True)  # Set all LEDs to red
        time.sleep(10)  # Keep the LEDs on for 10 seconds

        print("Clearing LEDs...")
        led_array.clear_leds()  # Clear the LEDs after the test

    except Exception as e:
        print(f"An error occurred during the test: {e}")  # Log any errors that occur during the test
