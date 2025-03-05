import cv2

class Projector:
    def __init__(self):
        self.window_name = "ImageWindow"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)  # Allow manual resize
        cv2.moveWindow(self.window_name, 1920, 0)  # Move to secondary display

    def display(self, frame):
        if frame is None:
            print("Error: Received empty frame.")
            return
        
        # Set your LCD's full resolution here
        screen_width = 2840  # Change to match your external LCD width
        screen_height = 4320  # Change to match your external LCD height

        # Resize frame to match LCD
        frame = cv2.resize(frame, (screen_width, screen_height), interpolation=cv2.INTER_LINEAR)

        # Resize window to match screen (simulating fullscreen)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, screen_width, screen_height)

        cv2.imshow(self.window_name, frame)

        if cv2.waitKey(33) & 0xFF == ord('q'):
            return False  # Exit on 'q'
        return True

if __name__ == "__main__":
    video_path = "/home/opencal/opencal/OpenCAL/development/simulations/PEGDA700_starship_rebinned_36degps_intensity11x.mp4"
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
