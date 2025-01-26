import cv2

class CameraController:
    def __init__(self, camera_index=0, resolution=(640,480), fps = 30):
        self.camera_index = camera_index
        self.resolution = resolution
        self.fps = fps
        
    def start_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise ValueError("help me im dying")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)


    def stop_camera(self):
        """Release the camera resource."""
        if self.cap is not None:
            self.cap.release()
            print("Camera released.")