import time
import os
from hardware.hardware_controller import HardwareController
import threading


class PrintController:
    def __init__(self, hardware=HardwareController()):
        self.hardware = hardware
        self.running = False

    def start_print_job(self, video_file):
            """Start the print job in a new thread."""
            threading.Thread(target=self.print, args=(video_file,)).start()


    def print(self, video_file):
        print(f"Starting print job... {video_file}")
        self.running = True

        # Start motor rotation and LED color change.
        self.hardware.stepper.start_rotation("CCW")
        self.hardware.led_array.set_led((255, 0, 0), set_all=True)

        # Start video playback.
        # This now delegates thread management to the projector.
        self.hardware.projector.stop_video()
        self.hardware.projector.play_video_with_mplayer(video_file)

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
        # Below begins a black 5-min video upon completion of the print or upon print termination
        #self.hardware.projector.start_video_thread("/home/opencal/opencal/OpenCAL/tmp/black.mp4")

        # Remove the preprocessed video file if it exists.
        video_path = "/tmp/processed_video.avi"
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
                print(f"Deleted video file: {video_path}")
            except Exception as e:
                print(f"Error deleting video file: {e}")
        else:
            print("No video file to delete.")

        print("Print job stopped and cleanup complete.")
