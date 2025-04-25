# camera_controller.py

import cv2
import time
import json
import threading
import glob
import signal
import sys

try:
    from picamera2 import Picamera2
except:
    Picamera2 = None



class CameraController:
    def __init__(self, config_file="/home/opencal/opencal/OpenCAL/utils/config.json"):
        # load preferred camera index (fallback to 0)
        with open(config_file) as f:
            cfg = json.load(f)["camera"]
        self.cam_type    = cfg.get("type", "usb")
        self.camera_index= cfg.get("index", 0)

        self.capture     = None
        self.picam2      = None
        self.streaming   = False
        self.stream_thread = None
        self.recording   = False
        self.record_thread = None
        self.writer      = None
        self.record_file = None

    def _open_usb_camera(self):
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
    
    def _open_rpi_camera(self, width=640, height=480, fps=30):
        # OPTION A: Picamera2 (preferred)
        if Picamera2:
            self.picam2 = Picamera2()
            preview_config = self.picam2.create_preview_configuration(
                main={"size": (width, height), "format": "RGB888"},
                lores={"size": (width//2, height//2)}
            )
            self.picam2.configure(preview_config)
            self.picam2.start()
            print("🟢 Pi CSI camera started via Picamera2")
            return

    def start_camera(self, preview=True):
        """Open camera (if needed) and optionally start live preview."""

        if self.cam_type == "usb" and self.capture is None:
            self._open_usb_camera()
        elif self.cam_type == "rpi" and self.capture is None and self.picam2 is None:
            self._open_rpi_camera()

        # now kick off your existing preview thread logic,
        # but branch read calls if using picam2:
        if preview and not self.streaming:
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()

    def _stream_loop(self):
        """imshow loop; press 'q' in the window to stop preview."""
        while self.streaming:
            if self.picam2:
                frame = self.picam2.capture_array()
                ok = frame is not None
            else:
                ok, frame = self.capture.read()

            if not ok:
                time.sleep(0.1)
                continue

            cv2.imshow("Camera Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_all()
                break

        cv2.destroyAllWindows()

    def start_record(self, filename=None, fps=20.0, frame_size=None, preview=False):
        # unchanged until you get frame_size…
        if filename is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            filename = f"/path/to/output/{ts}.mp4"
        self.record_file = filename

        if frame_size is None:
            if self.picam2:
                # Picamera2: ask its config
                cfg = self.picam2.camera_configuration["main"]
                frame_size = tuple(cfg["size"])
            else:
                w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frame_size = (w, h)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filename, fourcc, fps, frame_size)

        self.recording = True
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        print(f"🔴 Recording to {filename}…")

    def _record_loop(self):
        """Background loop writing frames to disk."""
        while self.recording:
            if self.picam2:
                frame = self.picam2.capture_array()
                ok = frame is not None
            else:
                ok, frame = self.capture.read()
            if not ok:
                break
            self.writer.write(frame)

    def stop_record(self):
        self.recording = False
        if self.record_thread: self.record_thread.join(1.0)
        if self.writer:     self.writer.release()
        print(f"💾 Saved recording to {self.record_file}")
        self.record_file, self.writer = None, None

    def stop_camera(self):
        self.streaming = False
        if self.stream_thread: self.stream_thread.join(1.0)
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None
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
