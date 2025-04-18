# camera_controller.py

import cv2
import time
import json
import threading
import glob
import signal
import sys

class CameraController:
    def __init__(self, config_file="/home/opencal/opencal/OpenCAL/utils/config.json"):
        # load preferred camera index (fallback to 0)
        try:
            with open(config_file, 'r') as f:
                cfg = json.load(f)
            self.camera_index = cfg.get('camera', {}).get('index', 0)
        except Exception:
            self.camera_index = 0

        self.capture       = None
        self.streaming     = False
        self.stream_thread = None
        self.recording     = False
        self.record_thread = None
        self.writer        = None
        self.record_file   = None

    def _find_and_open(self):
        """Scan /dev/video* and open first working device."""
        devices = glob.glob("/dev/video*")
        indices = sorted({int(d.replace("/dev/video","")) for d in devices if d.replace("/dev/video","").isdigit()})

        last_err = None
        for idx in indices:
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            time.sleep(0.1)
            if cap.isOpened():
                self.capture = cap
                self.camera_index = idx
                print(f"Opened /dev/video{idx}")
                return
            cap.release()
            last_err = f"could not open /dev/video{idx}"
        raise IOError(last_err or "no usable V4L2 camera found")

    def start_camera(self, preview=True):
        """Open camera (if needed) and optionally start live preview."""
        if self.capture is None:
            self._find_and_open()

        if preview and not self.streaming:
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()

    def _stream_loop(self):
        """imshow loop; press 'q' in the window to stop preview."""
        while self.streaming:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.1)
                continue
            cv2.imshow("Camera Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_camera()
                break
        cv2.destroyWindow("Camera Feed")

    def start_record(self, filename=None, fps=20.0, frame_size=None, preview=False):
        """
        Begin recording:
          preview=False => no imshow window
          preview=True  => start live preview (q to quit that)
        """
        # ensure camera open; may or may not start preview
        self.start_camera(preview=preview)

        # prepare output file
        if filename is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            filename = f"/home/opencal/opencal/OpenCAL/utils/prints/{ts}.mp4"
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
        print(f"Recording to {filename}  (preview={'on' if preview else 'off'})")

    def _record_loop(self):
        """Background loop writing frames to disk."""
        while self.recording:
            ok, frame = self.capture.read()
            if not ok:
                break
            self.writer.write(frame)

    def stop_record(self):
        """Stop recording thread and close file."""
        self.recording = False
        if self.record_thread:
            self.record_thread.join(timeout=1.0)
            self.record_thread = None
        if self.writer:
            self.writer.release()
            self.writer = None
        if self.record_file:
            print(f"✔ Recording saved to {self.record_file}")
        self.record_file = None

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

    def stop_all(self):
        """Convenience: stop both record and preview."""
        self.stop_record()
        self.stop_camera()


if __name__ == "__main__":
    cam = CameraController()

    # Catch Ctrl+C so we still clean up properly
    def on_sigint(signal, frame):
        print("\nInterrupted! Stopping...")
        cam.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_sigint)

    # Example: record WITHOUT preview
    cam.start_record(preview=False)
    print("Recording... Press Ctrl+C to stop.")
    # just spin until user aborts
    while cam.recording:
        time.sleep(0.1)
