import os
# Force Qt to use the "xcb" platform instead of "wayland"
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import numpy as np

class Projector:
    def __init__(self, screen_width, screen_height):
        self.window_name = "ProjectorDisplay"
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Create a resizable window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        # Move the window to the projector (x=1920, y=0)
        cv2.moveWindow(self.window_name, 1920, 0)
        # Set the window to fullscreen
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def display(self, frame, rotation_angle=0):
        if frame is None:
            print("Error: Received empty frame.")
            return False
        
        # Optionally rotate the frame if needed:
        frame = self.rotate_frame(frame, rotation_angle)
        
        # Get frame dimensions
        frame_h, frame_w = frame.shape[:2]
        
        # Compute scale factors to fit the frame within the projector resolution (only scale down)
        scale_w = self.screen_width / frame_w
        scale_h = self.screen_height / frame_h
        scale = min(scale_w, scale_h, 1.0)
        
        # Resize frame if it's larger than the screen
        if scale < 1.0:
            new_w = int(frame_w * scale)
            new_h = int(frame_h * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            frame_h, frame_w = frame.shape[:2]
        
        # Create a black background of projector dimensions
        background = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        
        # Calculate offsets to center the video frame on the background
        x_offset = (self.screen_width - frame_w) // 2
        y_offset = (self.screen_height - frame_h) // 2
        # Place the frame on the background
        background[y_offset:y_offset+frame_h, x_offset:x_offset+frame_w] = frame
        
        # Display the final image
        cv2.imshow(self.window_name, background)
        
        # Wait 33ms; exit if 'q' is pressed.
        if cv2.waitKey(33) & 0xFF == ord('q'):
            return False
        return True

    def rotate_frame(self, frame, angle):
        """Rotate the frame by the specified angle (in degrees)."""
        (h, w) = frame.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(frame, M, (w, h))
        return rotated

def main():
    video_path = "/media/opencal/UBOOKSTORE/PEGDA700_starship_rebinned_36degps_intensity11x.mp4"
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return
    
    # Define projector resolution (1920x1080)
    screen_width = 1920
    screen_height = 1080
    projector = Projector(screen_width, screen_height)
    
    rotation_angle = 0  # Change this if you need a rotated output

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video
        
        if not projector.display(frame, rotation_angle):
            break  # Exit if 'q' is pressed

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
