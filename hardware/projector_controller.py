import os
import subprocess

class Projector:
    def __init__(self):
        # Initialize the process attribute to keep track of mplayer.
        self.process = None

    def play_video_with_mplayer(self, video_path="/home/opencal/opencal/OpenCAL/tmp/preprocessed_output.mp4"):
        """
        Play the video using cvlc (VLC command-line interface) with the window positioned
        at x=1920 and y=0, and loop the video indefinitely.
        """
        command = [
            "cvlc",
            "--video-x=1920",
            "--video-y=0",
            "--loop",
            "--fullscreen",
            video_path
        ]
        
        self.process = subprocess.Popen(command)
        print("Video playback started.")

    def stop_video(self):
        """
        Stop the video playback by terminating the mplayer process.
        """
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Video playback stopped.")

def main():
    # Create an instance of Projector
    projector = Projector()
    
    # Play video using mplayer.
    projector.play_video_with_mplayer()
    
    # Wait for user input to stop the video.
    input("Press Enter to stop video playback...")
    projector.stop_video()

if __name__ == "__main__":
    main()