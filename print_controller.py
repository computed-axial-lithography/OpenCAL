from hardware.hardware_controller import HardwareController
import time
import cv2
from hardware.projector_controller import Projector


class PrintController:
    def __init__(self, hardware=HardwareController()):
        self.hardware = hardware
        
        self.running = False

    def print(self, video_file):
        print(f"Starting print job... {video_file}")
        self.running = True
      
        # Open video file
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            print(f"Failed to open video file: {video_file}")
            return

        # Start hardware
        self.hardware.stepper.start_rotation("CCW") # Start stepper motor
        self.hardware.led_array.set_led((255, 0, 0), set_all=True)  # Turn on LEDs

        # Get video FPS to sync frame timing
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30  # Default to 30 FPS if unknown

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    break  # End of video
                self.hardware.projector.display(frame,-90)
                # Keep timing consistent
                time.sleep(frame_delay)

        except Exception as e:
            print(f"Error during print: {e}")

        finally:
            cap.release()
            self.hardware.stepper.stop()
            self.hardware.led_array.clear_leds()  # Turn off LEDs
            print("Print job complete.")

    def stop(self):
        print("Stopping print job...")
        self.running = False

