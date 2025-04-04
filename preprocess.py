import cv2
import numpy as np
import os

def preprocess_video(input_path, output_path, screen_width, screen_height):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Error opening video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    out = cv2.VideoWriter(output_path, fourcc, fps, (screen_width, screen_height))

    last_printed = -5  # Track last printed percentage to only print every 5%
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rotated = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        resized = resize_and_pad(rotated, screen_width, screen_height)
        out.write(resized)

        frame_idx += 1
        percent = int((frame_idx / total_frames) * 100)
        if percent >= last_printed + 5:
            print(f"{percent}% complete")
            last_printed = percent

    cap.release()
    out.release()
    print("✅ Preprocessing complete!")

def resize_and_pad(frame, target_width, target_height):
    h, w = frame.shape[:2]
    scale = min(target_width / w, target_height / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    background = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    x_offset = (target_width - new_w) // 2
    y_offset = (target_height - new_h) // 2
    background[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    return background

if __name__ == "__main__":
    preprocess_video(
        input_path=r"C:\Users\conno\Documents\1-Academic\School Documents\Berkeley\Capstone\OpenCAL\OpenCAL\development\simulations\PEGDA700_starship_rebinned_36degps_intensity11x.mp4",
        output_path="tmp/preprocessed_output.avi",
        screen_width=1920,
        screen_height=1080
    )
