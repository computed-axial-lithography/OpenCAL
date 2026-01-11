from .camera_controller import CameraController
from .stepper_controller import StepperMotor
from .led_manager import LEDArray
from .lcd_display import LCDDisplay
from .rotary_controller import RotaryEncoderHandler
from .projector_controller import Projector
from .usb_manager import MP4Driver
from opencal.utils.config import Config

from pathlib import Path
from pprint import pprint
from typing import final

@final
class HardwareController:
    def __init__(self):
        # Resolve the path to the configuration file
        here = Path(__file__).resolve().parent       
        config_file = here.parent / "utils" / "config.json"

        # Check if the configuration file exists
        if not config_file.is_file():
            raise FileNotFoundError(f"Config not found at {config_file!s}")
        print(config_file)

        # Initialize error tracking and health status
        self.errors: list[str] = []  # List to store any initialization errors
        self.healthy = True  # Flag to indicate if all components are healthy

        # Attempt to initialize all hardware components
        self.initialize_hardware(config_file)

        if not self.healthy:
            pprint(self.errors)

    def initialize_hardware(self, config_file: Path):
        """Initialize all hardware components and handle any errors."""


        config = Config(config_file)
        # TODO: All this error checking needs to actually do something
        try:
            print('initializing stepper')
            self.stepper = StepperMotor(config.stepper)
        except Exception as e:
            self.errors.append(f"StepperMotor failed: {e}")
            self.healthy = False

        try:
            self.led_array = LEDArray(config.led_array)
        except Exception as e:
            self.errors.append(f"LEDArray failed: {e}")
            self.healthy = False

        try:
            self.lcd = LCDDisplay(config.lcd_display)
        except Exception as e:
            raise e
            self.errors.append(f"LCDDisplay failed: {e}")
            self.healthy = False

        try:
            self.rotary = RotaryEncoderHandler(config.rotary_encoder)   
        except Exception as e:
            self.errors.append(f"RotaryEncoderHandler failed: {e}")
            self.healthy = False

        try:
            self.projector = Projector(config.projector)
        except Exception as e:
            print(f"Projector failed: {e}") 
            self.errors.append(f"Projector failed: {e}")
            self.healthy = False

        try:
            self.usb_device = MP4Driver()
        except Exception as e:
            self.errors.append(f"USB device failed: {e}")
            self.healthy = False

        try:
            self.camera = CameraController(config.camera)  # Initialize camera controller
        except Exception as e:
            self.errors.append(f"CameraController failed: {e}")
            self.healthy = False

