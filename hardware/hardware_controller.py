from camera_controller import CameraController

class HardwareController:
    def __init__(self):
        self.camera = CameraController(camera_index=0)

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