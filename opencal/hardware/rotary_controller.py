from typing import final
from gpiozero import RotaryEncoder, Button

from opencal.utils.config import RotaryConfig


@final
class RotaryEncoderHandler:
    def __init__(self, config: RotaryConfig):
        """
        Rotary Encoder Driver using GPIOZero
        :param config_file: Path to the configuration JSON file
        """
        # Load configuration from the specified JSON file

        # Retrieve GPIO pin assignments from the configuration
        self.clk_pin = config.clk_pin
        self.dt_pin = config.dt_pin
        self.btn_pin = config.btn_pin

        # Initialize the rotary encoder and button
        self.encoder = RotaryEncoder(self.clk_pin, self.dt_pin)
        self.button = Button(self.btn_pin, bounce_time=0.05)

    def get_steps(self) -> int:
        """Get current encoder position"""
        return self.encoder.steps  # Return the current position of the encoder

    def was_button_pressed(self) -> bool:
        """Check if button was pressed (for polling-based use)"""
        return self.button.is_active


if __name__ == "__main__":
    # Example usage
    from opencal.utils.config import Config

    cfg = Config()
    encoder = RotaryEncoderHandler(cfg.rotary_encoder)
    try:
        print("Rotary Encoder Test. Press Ctrl+C to exit.")
        while True:
            pass  # Keep the program running to listen for events
    except KeyboardInterrupt:
        print("Exiting...")  # Log exit message on keyboard interrupt
