from gpiozero import RotaryEncoder, Button
import json
try:
    from signal import pause
except ImportError:
    pass  # Handle the case where the signal module is not available

class RotaryEncoderHandler:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        """
        Rotary Encoder Driver using GPIOZero
        :param config_file: Path to the configuration JSON file
        """
        # Load configuration from the specified JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Retrieve GPIO pin assignments from the configuration
        self.clk_pin = config['rotary_encoder'].get("clk_pin")  # GPIO pin for the encoder CLK signal
        self.dt_pin = config['rotary_encoder'].get("dt_pin")    # GPIO pin for the encoder DT signal
        self.btn_pin = config['rotary_encoder'].get("btn_pin")  # GPIO pin for the encoder push button (optional)

        # Initialize the rotary encoder and button
        self.encoder = RotaryEncoder(self.clk_pin, self.dt_pin, wrap=True, max_steps=1000)
        self.button = Button(self.btn_pin) 

        # Set up event handlers for the encoder and button
        self.encoder.when_rotated = self._rotate_callback  # Callback for rotation events
        if self.button:
            self.button.when_pressed = self._button_callback  # Callback for button press events

    def _rotate_callback(self):
        """Callback for rotary encoder rotation"""
        print(f"Rotary Encoder Position: {self.encoder.steps}")  # Log the current position of the encoder

    def _button_callback(self):
        """Callback for encoder push button press"""
        print("Encoder Button Pressed!")  # Log when the button is pressed

    def get_position(self):
        """Get current encoder position"""
        return self.encoder.steps  # Return the current position of the encoder

    def was_button_pressed(self):
        """Check if button was pressed (for polling-based use)"""
        return self.button.is_pressed if self.button else False  # Return the button state if it exists

if __name__ == "__main__":
    # Example usage
    encoder = RotaryEncoderHandler()  # Create an instance of the RotaryEncoderHandler
    try:
        print("Rotary Encoder Test. Press Ctrl+C to exit.")
        while True:
            pass  # Keep the program running to listen for events
    except KeyboardInterrupt:
        print("Exiting...")  # Log exit message on keyboard interrupt