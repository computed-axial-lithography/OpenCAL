import threading
import time
from typing import final

from opencal.utils.config import Config

from .hardware_controller import HardwareController
from pathlib import Path

VIDEO_SAVE_PATH = Path.home() / "OpenCAL/output/videos/print.h264"


@final
class PrintController:
    def __init__(self, config: Config, video_playing: threading.Event):
        self.hardware = HardwareController(config)
        if not self.hardware.healthy:
            print("not all peripherals connected, some functionality may not work")
        self.video_playing = video_playing
        self.running = False
        self.ui_config = config.ui

    def start_print_job(self, video_file: Path):
        """Start the print job in a new thread."""
        threading.Thread(target=self.print, args=(video_file,)).start()

    def print(self, video_file: Path):
        print(f"Starting print job... {video_file}")
        self.running = True

        # Start motor rotation and LED color change.
        self.hardware.stepper.start_rotation("CCW")
        self.hardware.led_manager.set_led((0, 240, 0, 0))  # red (GRBW order, reduced to minimise W bleed)

        # Start video playback.
        self.video_playing.set()
        self.hardware.projector.play_video_with_vlc(video_file)

        VIDEO_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.hardware.camera.start_recording(VIDEO_SAVE_PATH)

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

        # Stop motor and LEDs first so hardware responds immediately.
        self.hardware.stepper.stop()
        self.hardware.led_manager.clear_leds()

        # Stop video and camera (these may block briefly).
        self.hardware.projector.stop_video()
        self.video_playing.clear()
        self.hardware.camera.stop_recording()
        self.hardware.camera.stop_camera()

        print("Print job stopped and cleanup complete.")
