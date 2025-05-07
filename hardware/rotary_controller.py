from gpiozero import RotaryEncoder, Button
import json
try:
    from signal import pause
except ImportError:
    pass

class RotaryEncoderHandler:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        """
        Rotary Encoder Driver using GPIOZero
        :param clk_pin: GPIO pin for the encoder CLK signal
        :param dt_pin: GPIO pin for the encoder DT signal
        :param btn_pin: GPIO pin for the encoder push button (optional)
        """
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.clk_pin = config['rotary_encoder'].get("clk_pin")
        self.dt_pin = config['rotary_encoder'].get("dt_pin")
        self.btn_pin = config['rotary_encoder'].get("btn_pin")

        self.encoder = RotaryEncoder(self.clk_pin, self.dt_pin, wrap=True, max_steps=1000)
        self.button = Button(self.btn_pin) 

        # Event Handlers
        self.encoder.when_rotated = self._rotate_callback
        if self.button:
            self.button.when_pressed = self._button_callback

    def _rotate_callback(self):
        """Callback for rotary encoder rotation"""
        print(f"Rotary Encoder Position: {self.encoder.steps}")

    def _button_callback(self):
        """Callback for encoder push button press"""
        print("Encoder Button Pressed!")

    def get_position(self):
        """Get current encoder position"""
        return self.encoder.steps

    def was_button_pressed(self):
        """Check if button was pressed (for polling-based use)"""
        return self.button.is_pressed if self.button else False

if __name__ == "__main__":
    # Example usage
    encoder = RotaryEncoderHandler()
    try:
        print("Rotary Encoder Test. Press Ctrl+C to exit.")
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting...")