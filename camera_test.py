from picamera2 import Picamera2, Preview
import time

def main():
    cam = Picamera2()
    camera_config = cam.create_preview_configuration()
    cam.configure(camera_config)
    cam.start_preview(Preview.QTGL)
    cam.start()
    time.sleep(2)
    cam.capture_file('test.jpg')


if __name__ == '__main__':
    main()
