import numpy as np
import cv2
import sys

def preprocess_video(input_path, output_path, screen_width, screen_height, rotation_angle=-90):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Failed to open video: {input_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames to process: {total_frames}")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calculate output size if rotated
    if rotation_angle in [-90, 90, 270]:
        out_w, out_h = height, width
    else:
        out_w, out_h = width, height

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (screen_width, screen_height))

    frame_counter = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_counter += 1

            # Print progress update
            progress = frame_counter / total_frames * 100 if total_frames > 0 else 0
            print(f"Processing frame {frame_counter}/{total_frames} ({progress:.2f}%)", end='\r')
            sys.stdout.flush()

            # Rotate frame
            frame = rotate_frame(frame, rotation_angle)

            # Resize if needed
            frame_h, frame_w = frame.shape[:2]
            scale = min(screen_width / frame_w, screen_height / frame_h, 1.0)
            frame = cv2.resize(frame, (int(frame_w * scale), int(frame_h * scale)), interpolation=cv2.INTER_AREA)

            # Center the frame on a black background
            background = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
            fh, fw = frame.shape[:2]
            x_offset = (screen_width - fw) // 2
            y_offset = (screen_height - fh) // 2
            background[y_offset:y_offset+fh, x_offset:x_offset+fw] = frame

            out.write(background)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    finally:
        cap.release()
        out.release()
        print(f"\nSaved preprocessed video to: {output_path}")

def rotate_frame(frame, angle):
    (h, w) = frame.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(frame, M, (w, h))
    return rotated

def main():
    input_path = "/home/opencal/opencal/OpenCAL/development/simulations/LVUDMA_benchy_rebinned_36degps_intensity10x.mp4"      # Replace with your input video file path
    output_path = "processed_video.mp4"   # Replace with your desired output file path
    screen_width = 1920
    screen_height = 1080
    rotation_angle = -90

    preprocess_video(input_path, output_path, screen_width, screen_height, rotation_angle)

if __name__ == "__main__":
    main()
