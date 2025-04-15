import subprocess

def preprocess_video_ffmpeg(input_path, output_path, screen_width=1920, screen_height=1080):
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"transpose=2,scale={screen_width}:{screen_height}:force_original_aspect_ratio=decrease,pad={screen_width}:{screen_height}:(ow-iw)/2:(oh-ih)/2",
        output_path
    ]
    subprocess.run(command, check=True)

if __name__ == "__main__":
    preprocess_video_ffmpeg(
        input_path="/media/opencal/UBOOKSTORE/Screw OpenCal Video 4_3_25.mp4",
        output_path="tmp/preprocessed_output.mp4"
    )
