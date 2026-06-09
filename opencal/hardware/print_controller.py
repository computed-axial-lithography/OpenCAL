import threading
import time
from typing import final
from pathlib import Path

from opencal.utils.config import Config
from .hardware_controller import HardwareController

_RECORDING_DIR = Path.home() / "OpenCAL/output/videos"


@final
class PrintController:
    def __init__(self, config: Config, video_playing: threading.Event):
        self.hardware = HardwareController(config)
        if not self.hardware.healthy:
            print("not all peripherals connected, some functionality may not work")
        self.video_playing = video_playing
        self.running = False
        self.ui_config = config.ui
        self.recording_path: Path | None = None
        self.vial_width_px: int = 200

    def start_print_job(self, video_file: Path):
        """Start the print job in a new thread."""
        threading.Thread(target=self.print, args=(video_file,)).start()

    def print(self, video_file: Path):
        print(f"Starting print job... {video_file}")
        self.running = True

        self.recording_path = _RECORDING_DIR / f"{video_file.stem}_recording.h264"
        self.recording_path.parent.mkdir(parents=True, exist_ok=True)

        self.hardware.stepper.start_rotation("CCW")
        self.hardware.led_manager.set_led((0, 240, 0, 0))

        self.video_playing.set()
        self.hardware.projector.play_video_with_vlc(video_file)
        self.hardware.camera.start_recording(self.recording_path)

        try:
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

        self.hardware.stepper.stop()
        self.hardware.led_manager.clear_leds()

        self.hardware.projector.stop_video()
        self.video_playing.clear()
        self.hardware.camera.stop_recording()
        self.hardware.camera.stop_camera()

        print("Print job stopped and cleanup complete.")
