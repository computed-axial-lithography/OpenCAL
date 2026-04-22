import numpy as np
from PIL import Image


def main():
    w, h = 1920, 1080
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    y = np.linspace(0, 255, h)
    x = np.linspace(0, 255, w)
    Y, X = np.meshgrid(x, y)
    print(Y.shape)
    arr[..., 0] = Y.astype(np.uint8)
    arr[..., 1] = X.astype(np.uint8)

    im = Image.fromarray(arr, "RGB")
    im.save("vial_width.png")
    pass


if __name__ == "__main__":
    main()
