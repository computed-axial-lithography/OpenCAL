import os
import subprocess
import threading
import json

class Projector:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        # Initialize the process attribute to keep track of the playback process.
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.size = config['projector'].get("default_print_size", 100)  # Default size is 100 if not specified
        self.calibration_img_path = config['projector'].get("calibration_img_path", "/home/opencal/OpenCAL/utils/calibration.png")
        
        self.process = None
        self.thread = None  # We'll use this to keep track of the playback thread.
        

    def get_video_dimensions(self,video_path):
        """
        Uses ffprobe to retrieve the video dimensions (width and height) dynamically.
        Expects ffprobe to output a single line like: widthxheight (e.g., 1920x1080).
        """
        cmd = [
            "/usr/bin/ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            video_path
        ]
        output = subprocess.check_output(cmd).decode().strip()
        try:
            width, height = map(int, output.split("x"))
        except Exception as e:
            raise ValueError(f"Unable to parse video dimensions from output: {output}") from e
        return width, height


    def play_video_with_mpv(self, video_path=None):
        """
        Play the video using cvlc (VLC command-line interface) with the window positioned
        at x=1920 and y=0, and loop the video indefinitely.
        """
        if not video_path:
                raise ValueError("play_video_with_mpv() requires a `video_path` argument")
        
        orig_width, orig_height = self.get_video_dimensions(video_path)
        scale_factor = self.size / 100
        new_width = int(orig_width / scale_factor)
        new_height = int(orig_height / scale_factor)

        # Calculate the cropping values to ensure the video remains centered
        crop_x = int((orig_width) / 2) - new_width / 2
        crop_y = int((orig_height) / 2) - new_height / 2

        # Construct the crop filter argument to center the zoomed video
        crop_filter = f"crop={new_width}:{new_height}:{crop_x}:{crop_y}"

        # Set up the environment for the video
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        #env["XAUTHORITY"] = "/home/opencal/.Xauthority"

        # Construct the mpv command to play the video
        command = [
            "/usr/bin/mpv", 
            "--fs",                # Fullscreen mode
            "--loop",              # Loop the video
            f"--vf=lavfi=[{crop_filter}]",  # Apply the crop filter for zoom
            video_path
        ]
      

        
        self.process = subprocess.Popen(command, env=env)
        print("Video playback started.")

    def resize(self, size_new):
        self.size = size_new


    def stop_video(self):
        """
        Stop the video playback by terminating the cvlc process.
        """
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Video playback stopped.")
    

    def start_video_thread(self, video_path=None):
        """
        Start the video playback in a new thread.
        """
        if not video_path:
            raise ValueError("start_video_thread() requires a `video_path` argument")

        # Create a new thread for playing the video.
        self.thread = threading.Thread(target=self.play_video_with_mpv, args=(video_path,))
        self.thread.start()

    def display_image(self, image_path = None):
        """
        Display a still image fullscreen until stop_video() is called.
        Uses mpv with infinite loop on the single frame.
        """
        if image_path is None:
            image_path = self.calibration_img_path
        # If something’s already playing, stop it.
        if self.process:
            self.stop_video()

        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        #env["XAUTHORITY"] = "/home/opencal/.Xauthority"

        # mpv will loop the single image forever (until we terminate it)
        command = [
            "/usr/bin/mpv",
            "--fs",                    # fullscreen
            "--loop-file=inf",         # loop indefinitely
            "--no-audio",              # no sound
            "--image-display-duration=inf",  # keep image up forever
            image_path
        ]

        self.process = subprocess.Popen(command, env=env)
        print(f"Image displayed: {image_path}")

    def start_image_thread_for_image(self, image_path):
        """
        Same as display_image(), but in a background thread.
        """
        self.thread = threading.Thread(
            target=self.display_image,
            args=(image_path,),
            daemon=True
        )
        self.thread.start()

def main():
    # Example test for playback on projector:
    projector = Projector()
    projector.resize(100)
    # Start video playback in a new thread.
    projector.play_video_with_mpv() #include video path here
    
    
    # Wait for user input to stop the video.
    input("Press Enter to stop video playback...")
    projector.stop_video()
    
    # Optionally, wait for the video thread to finish.
    if projector.thread is not None:
        projector.thread.join()

if __name__ == "__main__":
    main()
