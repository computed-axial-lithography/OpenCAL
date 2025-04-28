import cv2
import time
import json
import threading
import glob
import subprocess
import os

class CameraController:
    def __init__(self, config_file="/home/opencal/opencal/OpenCAL/utils/config.json"):
        with open(config_file) as f:
            cfg = json.load(f)["camera"]
        self.cam_type     = cfg.get("type", "usb")
        self.camera_index = cfg.get("index", 0)
        self.save_path    = cfg.get("save_path")

        self.capture       = None
        self.stream_thread = None
        self.streaming     = False
        self.record_thread = None
        self.recording     = False
        self.writer        = None
        self.record_file   = None
        self._proc         = None
        self._raw_file     = None
    def set_type(self, type):
        self.cam_type = type
    def _open_usb_camera(self):
        devices = glob.glob("/dev/video*")
        indices = sorted({int(d.replace("/dev/video", "")) for d in devices if d.replace("/dev/video", "").isdigit()})
        for idx in indices:
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            time.sleep(0.1)
            if cap.isOpened():
                self.capture = cap
                self.camera_index = idx
                print(f"Opened /dev/video{idx}")
                return
            cap.release()
        raise IOError("no usable V4L2 camera found")

    def start_camera(self, preview=True):
        if self.cam_type == "usb" and self.capture is None:
            self._open_usb_camera()
        elif self.cam_type == "rpi":
            print("⚠️ Preview not available when using libcamera-vid")

        if preview and self.capture and not self.streaming:
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()

    def _stream_loop(self):
        while self.streaming:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.1)
                continue
            cv2.imshow("Camera Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_all()
                break
        cv2.destroyAllWindows()

    def start_record(self, filename=None, fps=20.0, frame_size=(640,480), preview=False):
        if self.cam_type == "rpi":
            # prepare raw .h264 file
            if filename is None:
                ts = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{self.save_path}/{ts}.h264"
            self._raw_file = filename
            self.record_file = os.path.splitext(filename)[0] + ".mp4"
            cmd = [
                "libcamera-vid",
                "--timeout", "0",
                "--inline",
                "--width", str(frame_size[0]),
                "--height", str(frame_size[1]),
                "--framerate", str(fps),
                "-o", filename
            ]
            self._proc = subprocess.Popen(cmd)
            print(f"🔴 RPi recording (raw H264) → {filename}")
            return

        # USB path
        if not self.capture:
            self._open_usb_camera()
        if filename is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{self.save_path}/{ts}.mp4"
        self.record_file = filename
        w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filename, fourcc, fps, (w, h))
        self.recording = True
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        print(f"🔴 Recording to {filename}…")

    def _record_loop(self):
        while self.recording:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.1)
                continue
            self.writer.write(frame)

    def stop_record(self):
        if self._proc:
            # stop libcamera-vid
            self._proc.send_signal(subprocess.signal.SIGINT)
            self._proc.wait()
            # wrap raw h264 into mp4 container
            raw = self._raw_file
            mp4 = self.record_file
            # requires MP4Box (GPAC)
            subprocess.run(["MP4Box", "-quiet", "-add", raw, mp4], check=True)
            os.remove(raw)
            print(f"💾 Saved RPi recording to {mp4}")
            self._proc = None
            self._raw_file = None
            return

        # USB stop
        self.recording = False
        if self.record_thread:
            self.record_thread.join(1.0)
        if self.writer:
            self.writer.release()
        print(f"💾 Saved recording to {self.record_file}")
        self.record_file, self.writer = None, None

    def stop_camera(self):
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join(1.0)
        if self.capture:
            self.capture.release()
            self.capture = None
        cv2.destroyAllWindows()

    def stop_all(self):
        self.stop_record()
        self.stop_camera()

if __name__ == "__main__":
    cam = CameraController()
    cam.cam_type = "usb"  # or "usb"
    cam.start_record(preview=False)
    print("Recording... Press Ctrl+C to stop.")

    time.sleep(5)

    cam.stop_all()
