import time
from typing import final
from pathlib import Path
from picamera2 import Picamera2
from libcamera import controls  # pyright: ignore

from opencal.utils.config import CameraConfig


@final
class CameraController:
    def __init__(self, config: CameraConfig):
        """Initialize the CameraController with configuration from a JSON file."""

        # TODO: remove unneccessary config
        self.cam_type = config.type
        self.camera_index = config.index
        self.save_path = Path(config.save_path)

        self.capture = None
        self._stream_thread = None
        self.streaming = False
        self._record_thread = None
        self.recording = False
        self.writer = None
        self.record_file = None
        self._proc = None
        self._raw_file = None
        self.fps = 20

        self.picam = Picamera2()
        print(self.picam)
        self.still_config = self.picam.create_still_configuration(buffer_count=2)
        self.video_config = self.picam.create_still_configuration({})
        self.picam.configure(self.still_config)

    def start_camera(self, preview: bool = True):
        """Start the camera and begin streaming if requested.

        Args:
            preview (bool): Whether to show a preview of the camera feed.
        """
        self.picam.start()

        # TODO: remove if necessary

        # if preview and self.capture and not self.streaming:
        #     self.streaming = True
        #     self._stream_thread = threading.Thread(
        #         target=self._stream_loop, daemon=True
        #     )
        #     self._stream_thread.start()

    def capture_image(self, filename: str):
        if not self.picam.started:
            self.start_camera()

        save_path = Path.cwd() / "output/images" / filename
        self.picam.capture_file(save_path)

    def set_focus(self, diopters: float):
        """Turns off autofocus and sets a manual focal distance in diopters (m^-1)"""
        self.picam.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": diopters})

    def activate_autofocus(self):
        self.picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    def _stream_loop(self):
        """Continuously read frames from the camera and display them."""
        pass
        # while self.streaming:
        #     ok, frame = self.capture.read()  # Read a frame from the camera
        #     if not ok:
        #         time.sleep(0.1)  # Wait if frame reading fails
        #         continue
        #     cv2.imshow("Camera Feed", frame)  # Display the camera feed
        #     if cv2.waitKey(1) & 0xFF == ord("q"):
        #         self.stop_all()  # Stop all operations if 'q' is pressed
        #         break
        # cv2.destroyAllWindows()  # Close all OpenCV windows

    # def start_record(
    #     self,
    #     filename: Path | None = None,
    #     frame_size: tuple[int, int] = (640, 480),
    #     preview: bool = False,
    # ):
    #     """Start recording video from the camera.
    #
    #     Args:
    #         filename (str): Name of the file to save the recording.
    #         fps (float): Frames per second for the recording.
    #         frame_size (tuple): Size of the video frames.
    #         preview (bool): Whether to show a preview while recording.
    #     """
    #     if self.cam_type == "rpi":
    #         # Prepare raw .h264 file for Raspberry Pi
    #         if filename is None:
    #             ts = time.strftime("%Y%m%d-%H%M%S")  # Timestamp for filename
    #             filename = f"{self.save_path}/{ts}.h264"
    #         self._raw_file = filename
    #         self.record_file = (
    #             os.path.splitext(filename)[0] + ".mp4"
    #         )  # Output MP4 filename
    #         cmd = [
    #             "/usr/bin/libcamera-vid",
    #             "--timeout",
    #             "0",
    #             "--inline",
    #             "--width",
    #             str(frame_size[0]),
    #             "--height",
    #             str(frame_size[1]),
    #             "--framerate",
    #             str(self.fps),
    #         ]
    #         if not preview:
    #             cmd += ["--nopreview"]  # or ["--preview", "none"]
    #         cmd += ["-o", filename]
    #         self._proc = subprocess.Popen(cmd)  # Start the recording process
    #         print(f"🔴 RPi recording (raw H264) → {filename}")
    #         return
    #
    #     # USB path
    #     if not self.capture:
    #         self._open_usb_camera()  # Open USB camera if not already opened
    #     if filename is None:
    #         ts = time.strftime("%Y%m%d-%H%M%S")  # Timestamp for filename
    #         filename = f"{self.save_path}/{ts}.mp4"
    #     self.record_file = filename
    #     w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))  # Get frame width
    #     h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Get frame height
    #     fourcc = cv2.VideoWriter.fourcc(*"mp4v")  # Codec for MP4
    #     self.writer = cv2.VideoWriter(
    #         filename, fourcc, self.fps, (w, h)
    #     )  # Initialize video writer
    #     self.recording = True
    #     self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
    #     self._record_thread.start()  # Start the recording thread
    #     print(f"🔴 Recording to {filename}…")
    #
    # def _record_loop(self):
    #     """Continuously read frames from the camera and write them to the video file."""
    #     while self.recording:
    #         ok, frame = self.capture.read()  # Read a frame from the camera
    #         if not ok:
    #             time.sleep(0.1)  # Wait if frame reading fails
    #             continue
    #         self.writer.write(frame)  # Write the frame to the video file
    #
    # def stop_record(self):
    #     if self._proc:
    #         # stop libcamera-vid
    #         self._proc.send_signal(subprocess.signal.SIGINT)
    #         self._proc.wait()
    #         # wrap raw h264 into mp4 container
    #         raw = self._raw_file
    #         mp4 = self.record_file
    #         # requires MP4Box (GPAC)\
    #         cmd = [
    #             "/usr/bin/ffmpeg",
    #             "-fflags",
    #             "+genpts",
    #             "-f",
    #             "h264",
    #             "-r",
    #             "20",
    #             "-i",
    #             raw,
    #             "-r",
    #             "20",
    #             "-c:v",
    #             "libx264",
    #             "-preset",
    #             "veryfast",
    #             "-crf",
    #             "23",
    #             "-movflags",
    #             "+faststart",
    #             mp4,
    #         ]
    #         try:
    #             subprocess.run(cmd, check=True)
    #             os.remove(raw)
    #         except subprocess.CalledProcessError as e:
    #             print("FFmpeg failed with exit code:", e.returncode)
    #             print("Command:", e.cmd)
    #             print("Output:", e.output)
    #
    #         print(f"💾 Saved RPi recording to {mp4}")
    #         self._proc = None
    #         self._raw_file = None
    #         return
    #
    #     # USB stop
    #     self.recording = False
    #     if self._record_thread:
    #         self._record_thread.join(1.0)
    #     if self.writer:
    #         self.writer.release()
    #     print(f"💾 Saved recording to {self.record_file}")
    #     self.record_file, self.writer = None, None

    def stop_camera(self):
        """Stop the camera and release resources."""
        self.picam.stop()

        # TODO: remove when done

        # self.streaming = False
        # if self._stream_thread:
        #     self._stream_thread.join(1.0)  # Wait for the streaming thread to finish
        # if self.capture:
        #     self.capture.release()  # Release the camera
        #     self.capture = None
        # cv2.destroyAllWindows()  # Close all OpenCV windows

    def stop_all(self):
        """Stop both recording and camera streaming."""
        # self.stop_record()  # Stop recording
        self.stop_camera()  # Stop camera streaming


if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    cam = CameraController(cfg.camera)  # Create an instance of the CameraController
    cam.cam_type = "rpi"  # Set camera type to Raspberry Pi (or "usb")
    print("Recording... Press Ctrl+C to stop.")

    time.sleep(10)  # Record for 5 seconds

    cam.stop_all()  # Stop all operations
