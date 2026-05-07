from .camera_controller import CameraController
from .stepper import StepperMotorInterface, create_stepper
from .led_manager import LEDManager
from .lcd_display import LCDDisplay
from .rotary_controller import RotaryEncoderHandler
from .projector_controller import Projector
from .usb_manager import MP4Driver
from opencal.utils.config import Config

from pprint import pprint
from typing import final


@final
class HardwareController:
    def __init__(self, config: Config):
        # Initialize error tracking and health status
        self.errors: list[str] = []  # List to store any initialization errors
        self.healthy = True  # Flag to indicate if all components are healthy

        # Attempt to initialize all hardware components
        self.initialize_hardware(config)

        if not self.healthy:
            pprint(self.errors)

    def initialize_hardware(self, config: Config):
        """Initialize all hardware components and handle any errors."""

        # TODO: All this error checking needs to actually do something
        self.stepper: StepperMotorInterface
        try:
            print("initializing stepper")
            self.stepper = create_stepper(config.stepper)
        except Exception as e:
            self.errors.append(f"StepperMotor failed: {e}")
            self.healthy = False

        try:
            self.led_manager = LEDManager(config.led_array)
        except Exception as e:
            self.errors.append(f"LEDArray failed: {e}")
            self.healthy = False

        try:
            self.lcd = LCDDisplay(config.lcd_display)
        except Exception as e:
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
            self.camera = CameraController(config.camera)
        except Exception as e:
            self.errors.append(f"CameraController failed: {e}")
            self.healthy = False
