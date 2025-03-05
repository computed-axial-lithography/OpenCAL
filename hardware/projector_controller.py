import cv2
import numpy as np

class Projector:
    def __init__(self):
        self.window_name = "ImageWindow"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)  # Allow manual resize
        cv2.moveWindow(self.window_name, 1920, 0)  # Move to secondary display

    def display(self, frame, rotation_angle=-90):
        if frame is None:
            print("Error: Received empty frame.")
            return
        
        # Set your LCD's full resolution here
        screen_width = 2840  # Change to match your external LCD width
        screen_height = 4320  # Change to match your external LCD height

        # Rotate frame before resizing
        frame = self.rotate_frame(frame, rotation_angle)

        # Resize frame to match LCD
        frame = cv2.resize(frame, (screen_width, screen_height), interpolation=cv2.INTER_LINEAR)

        # Resize window to match screen (simulating fullscreen)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, screen_width, screen_height)

        cv2.imshow(self.window_name, frame)

        if cv2.waitKey(33) & 0xFF == ord('q'):
            return False  # Exit on 'q'
        return True

    def rotate_frame(self, frame, angle):
        """Rotate the frame by the specified angle (in degrees)."""
        # Get the center of the image
        center = (frame.shape[1] // 2, frame.shape[0] // 2)

        # Get the rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Rotate the image
        rotated_frame = cv2.warpAffine(frame, rotation_matrix, (frame.shape[1], frame.shape[0]))

        return rotated_frame


if __name__ == "__main__":
    video_path = "/home/opencal/opencal/OpenCAL/development/simulations/PEGDA700_starship_rebinned_36degps_intensity11x.mp4"
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        exit()

    projector = Projector()

    # Set the desired rotation angle (e.g., 90, 180, 270, etc.)
    rotation_angle = 90

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        if not projector.display(frame, rotation_angle):
            break  # Stop if 'q' is pressed

    cap.release()
    cv2.destroyAllWindows()
