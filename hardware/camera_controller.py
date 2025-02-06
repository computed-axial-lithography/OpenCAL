import cv2
import json

class CameraController:
    def __init__(self, config_file="utils/config.json" ):
 
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.camera_index = config['camera'].get("index", 0)

        
    def start_camera(self):
        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            raise IOError(f"Error: could not open camera {self.camera_index}")
        

    def read_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            raise IOError("Error: could not read frame from camera")
        return frame
    
    def stop_camera(self):
        """Release the camera resource."""
        if self.capture is not None:
            self.capture.release()
            print("Camera released.")


#Test to open webcam and stream image
if __name__ == "__main__":
    camera = CameraController()
    try:
        # Start the camera
        camera.start_camera()
        print("Press 'q' to quit.")

        # Stream video
        while True:
            frame = camera.read_frame()  # Capture a frame
            cv2.imshow("Camera Feed", frame)  # Display the frame
            
            # Break the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(e)

    finally:
        # Stop the camera and close windows
        camera.stop_camera()
        cv2.destroyAllWindows()
