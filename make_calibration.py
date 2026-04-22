import numpy as np
from PIL import Image
from pathlib import Path


def main():
    w, h = 1920, 1080
    arr = np.zeros((h, w), dtype=np.uint8)

    # k = 0
    # for i in range(50, 950, 50):
    #     for j in range(50, 600, 50):
    #         arr[i-2:i+3, j-2:j+3, k] = 255
    #         k = (k + 1) % 3
    #
    # cy, cx = h // 2, w // 2
    # dy, dx = 2, 2
    #
    # arr[cy - dy : cy + dy, cx - dx : cx + dx] = 255

    im = Image.fromarray(arr, mode="L")
    im.save("opencal/utils/calibration/dark.png")


if __name__ == "__main__":
    main()
