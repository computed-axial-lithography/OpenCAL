import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import time

class Projector:
    def __init__(self, screen_width, screen_height):
        self.window_name = "ProjectorDisplay"
        self.screen_width = screen_width
        self.screen_height = screen_height
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.window_name, 1920, 0)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def display(self, frame):
        if frame is None:
            print("Error: Received empty frame.")
            return False

        cv2.imshow(self.window_name, frame)
        # Use a minimal wait to allow OpenCV to process window events.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False
        return True

def main():
    video_path = "/home/opencal/opencal/output.mp4"
    screen_width = 1920
    screen_height = 1080
    projector = Projector(screen_width, screen_height)
    
    # Option 1: Default VideoCapture
    #cap = cv2.VideoCapture(video_path)
    
    # Option 2: If you have GStreamer installed, you can try a hardware-accelerated pipeline:
    pipeline = (
    f"filesrc location={video_path} ! qtdemux ! h264parse ! avdec_h264 ! videoconvert ! "
    f"video/x-raw, format=BGR, width={screen_width}, height={screen_height} ! appsink sync=false"
    )
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return

 

    desired_fps = 36
    desired_frame_time = 1.0 / desired_fps  # Approximately 0.0278 seconds

    while cap.isOpened():
        start_time = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            break

        if not projector.display(frame):
            break

        elapsed = time.perf_counter() - start_time
        remaining = desired_frame_time - elapsed
        if remaining > 0:
            time.sleep(remaining)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
