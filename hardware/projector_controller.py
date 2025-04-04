import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2

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

        # Just show the frame directly
        cv2.imshow(self.window_name, frame)

        if cv2.waitKey(33) & 0xFF == ord('q'):
            return False
        return True

def main():
    video_path = "/media/opencal/UBOOKSTORE/PEGDA700_starship_rebinned_36degps_intensity11x.mp4"
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return

    screen_width = 1920
    screen_height = 1080
    projector = Projector(screen_width, screen_height)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if not projector.display(frame):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
