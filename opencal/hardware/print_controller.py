<<<<<<<< HEAD:opencal/print_controller.py
========
import time
from hardware.hardware_controller import HardwareController
>>>>>>>> db4c355be1655af2d4b351feb87c9fed20a314f9:opencal/hardware/print_controller.py
import threading
import time

from .hardware.hardware_controller import HardwareController


class PrintController:
    def __init__(self, hardware: HardwareController | None = None):
        self.hardware = hardware or HardwareController()
        if not self.hardware.healthy:
            print("not all peripherals connected, some functionality may not work")
        self.running = False

    def start_print_job(self, video_file):
        """Start the print job in a new thread."""
        threading.Thread(target=self.print, args=(video_file,)).start()

    def print(self, video_file):
        print(f"Starting print job... {video_file}")
        self.running = True

        # Start motor rotation and LED color change.
        self.hardware.stepper.start_rotation("CCW")
        self.hardware.led_array.set_led((255, 0, 0))

        # Start video playback.
        # self.hardware.projector.stop_video()
        self.hardware.projector.play_video_with_mpv(video_file)

        # Handle camera operations if a camera is available
        if self.hardware.camera:
            self.hardware.camera.start_camera(preview=False)  # Start the camera
            self.hardware.camera.start_record()  # Start recording

        try:
            # Keep the job running until self.running is set to False externally.
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Print job interrupted by user.")
        finally:
            self.stop()
            print("Print job complete.")

    def stop(self):
        print("Stopping print job...")
        self.running = False

        # Stop the video, motor, and clear LEDs.
        self.hardware.projector.stop_video()
        self.hardware.stepper.stop()
        self.hardware.led_array.clear_leds()

        # Stop camera operations if a camera is available
        if self.hardware.camera:
            self.hardware.camera.stop_all()  # Stop all camera operations

        print("Print job stopped and cleanup complete.")
