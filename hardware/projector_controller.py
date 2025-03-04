import cv2
import time

class Projector:
    def __init__(self):
        self.window_name = "ImageWindow"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.window_name, 1920, 0)

    def display(self, frame):
        if frame is None:
            print("Error: Received empty frame.")
            return
        
        cv2.imshow(self.window_name, frame)

        # Wait briefly to simulate frame rate (e.g., 30 FPS -> ~33ms delay)
        if cv2.waitKey(33) & 0xFF == ord('q'):
            return False  # Signal to exit
        return True

if __name__ == "__main__":
    video_path = "/home/opencal/opencal/OpenCAL/hardware/sample_video.mp4"
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        exit()

    projector = Projector()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        if not projector.display(frame):
            break  # Stop if 'q' is pressed

    cap.release()
    cv2.destroyAllWindows()
