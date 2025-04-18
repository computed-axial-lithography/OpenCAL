# camera_controller.py

import cv2
import time
import json
import threading
import glob

class CameraController:
    # NEW 4/16: find camera loaction on initialization
    def __init__(self, config_file="/home/opencal/opencal/OpenCAL/utils/config.json"):
        # Load camera index from config (fallback to 0)
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.camera_index = config.get('camera', {}).get("index", 0)
        except Exception:
            self.camera_index = 0

        # NEW 4/16: added streaming and recording attributes
        self.capture       = None
        self.streaming     = False
        self.stream_thread = None
        self.recording     = False
        self.record_thread = None
        self.writer        = None
        self.record_file   = None

    def start_camera(self):
        # NEW 4/16: find device and try opening it
        """
        Scan /dev/video* nodes, extract numeric indices, and open with V4L2 backend.
        """
        devices = glob.glob("/dev/video*")
        indices = []
        for dev in devices:
            try:
                idx = int(dev.replace("/dev/video", ""))
                indices.append(idx)
            except ValueError:
                continue
        indices = sorted(set(indices))

        last_error = None
        for idx in indices:
            # Try opening with V4L2 backend explicitly
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            time.sleep(0.2)
            if cap.isOpened():
                self.capture = cap
                self.camera_index = idx
                print(f"Opened camera at index {idx} (/dev/video{idx}) with V4L2 backend")
                break
            cap.release()
            last_error = f"Error: could not open camera index {idx} with V4L2"
        else:
            raise IOError(last_error or "Error: no usable V4L2 camera found")

        # NEW 4/16: start preview thread
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
    # NEW 4/16: streaming thread for visualization (not needed during actual print process)
    def _stream_loop(self):
        """Internal: live preview until streaming disabled."""
        while self.streaming:
            ret, frame = self.capture.read()
            if not ret:
                time.sleep(0.1)
                continue
            cv2.imshow("Camera Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_camera()
                break
        cv2.destroyWindow("Camera Feed")

    def read_frame(self):
        """Grab and return a single frame."""
        if self.capture is None:
            raise RuntimeError("Camera not started. Call start_camera() first.")
        ret, frame = self.capture.read()
        if not ret:
            raise IOError("Error: could not read frame from camera")
        return frame
    
    # NEW 4/16: stop streaming and recording
    def stop_camera(self):
        """Stop preview thread and release camera."""
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1.0)
            self.stream_thread = None
        if self.capture:
            self.capture.release()
            self.capture = None
        cv2.destroyAllWindows()

    # NEW 4/16: added recording function using cv2
    def start_record(self, filename=None, fps=20.0, frame_size=None):
        """Begin recording video to disk."""
        if self.capture is None:
            self.start_camera()
        # NEW 4/16: create file for recroding
        if filename is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            filename = f"/home/pi/print_{ts}.mp4"
        self.record_file = filename

        if frame_size is None:
            w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_size = (w, h)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filename, fourcc, fps, frame_size)

        self.recording = True
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()

    # NEW 4/16: added record loop
    def _record_loop(self):
        while self.recording:
            ret, frame = self.capture.read()
            if not ret:
                break
            self.writer.write(frame)

    # NEW 4/16: added stop recording functionality
    def stop_record(self):
        """Stop recording thread and release writer."""
        self.recording = False
        if self.record_thread:
            self.record_thread.join(timeout=1.0)
            self.record_thread = None
        if self.writer:
            self.writer.release()
            self.writer = None
        if self.record_file:
            print(f"Recording saved to {self.record_file}")
        self.record_file = None

if __name__ == "__main__":
    cam = CameraController()
    try:
        cam.start_camera()
        cam.start_record()
        print("Recording... Press 'q' to stop preview.")
        while cam.streaming:
            time.sleep(0.1)
    except Exception as e:
        print(e)
    finally:
        cam.stop_record()
        cam.stop_camera()
