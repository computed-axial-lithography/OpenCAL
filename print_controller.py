from hardware.hardware_controller import HardwareController
import time
import cv2
import preprocess
import os


class PrintController:
    def __init__(self, hardware=HardwareController()):
        self.hardware = hardware
        
        self.running = False

            
    def print(self, video_file):
        print(f"Starting print job... {video_file}")
        print("preprocessing video...")
        self.running = True

        preprocess.preprocess_video_ffmpeg(video_file, "/tmp/processed_video.avi", 1920, 1080)
      
        # Open video file
        cap = cv2.VideoCapture("/tmp/processed_video.avi")
        if not cap.isOpened():
            print(f"Failed to open processed video file: {video_file}")
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
                self.hardware.projector.display(frame)
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
        
        # Remove the preprocessed video file if it exists
        video_path = "/tmp/processed_video.avi"
        if os.path.exists(video_path):
            try:
                os.remove(video_path)  # Delete the video file
                print(f"Deleted video file: {video_path}")
            except Exception as e:
                print(f"Error deleting video file: {e}")
        else:
            print("No video file to delete.")

        # Optionally, ensure other hardware-related cleanup is done
        self.hardware.stepper.stop()
        self.hardware.led_array.clear_leds()  # Turn off LEDs
        print("Print job stopped and cleanup complete.")
