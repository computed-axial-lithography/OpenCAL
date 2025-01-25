import cv2
import numpy as np
import time

def resize_with_aspect_ratio(image, target_width, target_height):
    h, w = image.shape[:2]
    aspect = w / h

    if aspect > target_width / target_height:
        new_w = target_width
        new_h = int(new_w / aspect)
    else:
        new_h = target_height
        new_w = int(new_h * aspect)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    y_offset = (target_height - new_h) // 2
    x_offset = (target_width - new_w) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas

class VideoFile:
    def __init__(self, path):
        self.path = path
        self.capture = cv2.VideoCapture(path)
        if not self.capture.isOpened():
            raise IOError(f"Error: Could not open video file {path}")

    def read_frame(self):
        ret, frame = self.capture.read()
        flipped_frame = cv2.flip(frame, 1)
        if not ret:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.capture.read()
        return frame, flipped_frame

    def release(self):
        self.capture.release()

class CameraImage:
    def __init__(self, index=0):
        self.capture = cv2.VideoCapture(index)
        if not self.capture.isOpened():
            raise IOError("Error: Could not open camera")

    def read_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            raise IOError("Error: Could not read frame from camera")
        return frame

    def release(self):
        self.capture.release()



class DifferenceImage:
    def __init__(self):
        pass

    def compute(self, camera_frame, video_frame):
        gray_camera = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2GRAY)
        gray_video = cv2.cvtColor(video_frame, cv2.COLOR_BGR2GRAY)

        difference = cv2.absdiff(gray_camera, gray_video)
        # mask = gray_video > 0
        # masked_difference = np.zeros_like(difference)
        # masked_difference[mask] = difference[mask]

        return difference


def main():
    video_path = 'camera_integration\LVUDMA_robo_rebinned_54degps_intensity2xarray1final.mp4'
    try:
        video = VideoFile(video_path)
        camera = CameraImage()
        difference_calculator = DifferenceImage()

        while True:
            # Capture frames
            video_frame, flipped_video = video.read_frame()
            camera_frame = camera.read_frame()

            # Process camera frame
            red_filtered_frame = camera_frame.copy()
            red_filtered_frame[:, :, 0] = 0
            red_filtered_frame[:, :, 1] = 0

            # Resize video frame to match camera dimensions
            video_frame = resize_with_aspect_ratio(video_frame, camera_frame.shape[1], camera_frame.shape[0])
            flipped_video_frame = resize_with_aspect_ratio(flipped_video, camera_frame.shape[1], camera_frame.shape[0])

            # Compute difference
            difference_frame = difference_calculator.compute(camera_frame, flipped_video_frame)

            # Convert grayscale to RGB for visualization
            gray_camera_rgb = cv2.cvtColor(cv2.cvtColor(camera_frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            difference_frame_rgb = cv2.cvtColor(difference_frame, cv2.COLOR_GRAY2BGR)

            # Display results
            cv2.imshow('Original MP4', video_frame)
            cv2.imshow('Red-filtered Streaming', red_filtered_frame)
            cv2.imshow('Grayscale Streaming', gray_camera_rgb)
            cv2.imshow('Grayscale Difference', difference_frame_rgb)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.05)

    except IOError as e:
        print(e)

    finally:
        if 'video' in locals():
            video.release()
        if 'camera' in locals():
            camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
