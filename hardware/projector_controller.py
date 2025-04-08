import os
import subprocess
import threading

class Projector:
    def __init__(self):
        # Initialize the process attribute to keep track of the playback process.
        self.process = None
        self.thread = None  # We'll use this to keep track of the playback thread.

    def play_video_with_mplayer(self, video_path="/home/opencal/opencal/OpenCAL/tmp/preprocessed_output.mp4"):
        """
        Play the video using cvlc (VLC command-line interface) with the window positioned
        at x=1920 and y=0, and loop the video indefinitely.
        """
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        env["XAUTHORITY"] = "/home/opencal/.Xauthority"

        
        command = [
            "/usr/bin/cvlc", 
            "--video-x=1920",
            "--video-y=0",
            "--loop",
            "--fullscreen",
            video_path
        ]
        
        self.process = subprocess.Popen(command, env=env)
        print("Video playback started.")

    def stop_video(self):
        """
        Stop the video playback by terminating the cvlc process.
        """
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Video playback stopped.")

    def start_video_thread(self, video_path="/home/opencal/opencal/OpenCAL/tmp/preprocessed_output.mp4"):
        """
        Start the video playback in a new thread.
        """
        # Create a new thread for playing the video.
        self.thread = threading.Thread(target=self.play_video_with_mplayer, args=(video_path,))
        self.thread.start()

def main():
    # Create an instance of Projector.
    projector = Projector()
    
    # Start video playback in a new thread.
    projector.start_video_thread()
    
    # Wait for user input to stop the video.
    input("Press Enter to stop video playback...")
    projector.stop_video()
    
    # Optionally, wait for the video thread to finish.
    if projector.thread is not None:
        projector.thread.join()

if __name__ == "__main__":
    main()
