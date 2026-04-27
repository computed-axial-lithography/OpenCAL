import threading
import time
from typing import final

from opencal.utils.config import Config

from .hardware_controller import HardwareController
from pathlib import Path

@final
class PrintController:
    def __init__(self, config: Config, video_playing: threading.Event):
        self.hardware = HardwareController(config)
        if not self.hardware.healthy:
            print("not all peripherals connected, some functionality may not work")
        self.video_playing = video_playing
        self.running = False

    def start_print_job(self, video_file: str):
        """Start the print job in a new thread."""
        threading.Thread(target=self.print, args=(video_file,)).start()

    def print(self, video_file: str):
        print(f"Starting print job... {video_file}")
        self.running = True

        # Start motor rotation and LED color change.
        self.hardware.stepper.start_rotation("CCW")
        self.hardware.led_manager.set_led((255, 0, 0))

        # Start video playback.
        self.video_playing.set()
        self.hardware.projector.play_video_with_mpv(Path(video_file))

        self.hardware.camera.start_recording(Path.home() / "OpenCAL/output/videos/print.h264")

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
        if not self.running:
            return
        print("Stopping print job...")
        self.running = False

        # Stop the video, motor, and clear LEDs.
        self.hardware.projector.stop_video()
        self.video_playing.clear()
        self.hardware.stepper.stop()
        self.hardware.led_manager.clear_leds()

        # Stop camera operations if a camera is available
        self.hardware.camera.stop_recording()
        self.hardware.camera.stop_all()  # Stop all camera operations

        print("Print job stopped and cleanup complete.")
