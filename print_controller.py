from hardware.hardware_controller import HardwareController
import time
import cv2
from hardware.projector_controller import Projector
import numpy as np


class PrintController:
    def __init__(self, hardware=HardwareController()):
        self.hardware = hardware
        
        self.running = False

        
def preprocess_video(input_path, output_path, screen_width, screen_height, rotation_angle=-90):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Failed to open video: {input_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calculate output size if rotated
    if rotation_angle in [-90, 90, 270]:
        out_w, out_h = height, width
    else:
        out_w, out_h = width, height

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (screen_width, screen_height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Rotate
        frame = rotate_frame(frame, rotation_angle)

        # Resize only if too big
        frame_h, frame_w = frame.shape[:2]
        scale = min(screen_width / frame_w, screen_height / frame_h, 1.0)
        frame = cv2.resize(frame, (int(frame_w * scale), int(frame_h * scale)), interpolation=cv2.INTER_AREA)

        # Center on black background
        background = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
        fh, fw = frame.shape[:2]
        x_offset = (screen_width - fw) // 2
        y_offset = (screen_height - fh) // 2
        background[y_offset:y_offset+fh, x_offset:x_offset+fw] = frame

        out.write(background)

    cap.release()
    out.release()
    print(f"Saved preprocessed video to: {output_path}")

    def rotate_frame(frame, angle):
        (h, w) = frame.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(frame, M, (w, h))
        return rotated


    def print(self, video_file):
        print(f"Starting print job... {video_file}")
        self.running = True

        self.preprocess_video(video_file, "/tmp/processed_video.mp4", 1920, 1080)
      
        # Open video file
        cap = cv2.VideoCapture("/tmp/processed_video.mp4")
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

