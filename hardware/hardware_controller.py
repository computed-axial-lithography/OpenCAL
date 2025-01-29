from .camera_controller import CameraController
from .stepper_controller import StepperMotor
from .led_manager import LEDArray

class HardwareController:
    def __init__(self):
        self.camera = CameraController()
        self.stepper = StepperMotor()
        self.led_array = LEDArray()

    def start_all(self):
        """Start all hardware components."""
        print("Starting all hardware...")
        self.camera.start_camera()

    def stop_all(self):
        """Stop all hardware components."""
        print("Stopping all hardware...")
        self.camera.stop_camera()

    def capture_frame(self):
        """Capture and process a frame from the camera."""
        return self.camera.read_frame()