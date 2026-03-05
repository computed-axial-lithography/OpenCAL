import numpy as np
from PIL import Image
from pathlib import Path

def main():
    arr = np.zeros((960, 600, 3), dtype=np.uint8)

    k = 0
    for i in range(50, 950, 50):
        for j in range(50, 600, 50):
            arr[i-2:i+3, j-2:j+3, k] = 255
            k = (k + 1) % 3
    
    im = Image.fromarray(arr, mode='RGB')
    im.save("opencal/utils/calibration/rgb_cycle_grid.png")


if __name__ == "__main__":
    main()
