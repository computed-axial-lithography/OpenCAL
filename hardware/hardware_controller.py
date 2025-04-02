from .camera_controller import CameraController
from .stepper_controller import StepperMotor
from .led_manager import LEDArray
from .lcd_display import LCDDisplay
from .rotary_controller import RotaryEncoderHandler
from .projector_controller import Projector
from .usb_manager import MP4Driver

import time
import cv2


class HardwareController:
    def __init__(self):
        self.camera = None
        self.stepper = None
        self.led_array = None
        self.lcd = None
        self.rotary = None
        self._projector = None
        self.usb_device = None

        self.errors = []
        self.healthy = True

        try:
            self.camera = CameraController()
        except Exception as e:
            self.errors.append(f"CameraController failed: {e}")
            self.healthy = False

        try:
            self.stepper = StepperMotor()
        except Exception as e:
            self.errors.append(f"StepperMotor failed: {e}")
            self.healthy = False

        try:
            self.led_array = LEDArray()
        except Exception as e:
            self.errors.append(f"LEDArray failed: {e}")
            self.healthy = False

        try:
            self.lcd = LCDDisplay()
        except Exception as e:
            self.errors.append(f"LCDDisplay failed: {e}")
            self.healthy = False

        try:
            self.rotary = RotaryEncoderHandler()   
        except Exception as e:
            self.errors.append(f"RotaryEncoder failed: {e}")
            self.healthy = False
        
        try:
            self.usb_device = MP4Driver()
        except Exception as e:
            self.errors.append(f"USB device failed: {e}")
            self.healthy = False
        
        # try:
        #     #self.projector = Projector(1920,1080) 
        # except Exception as e:
        #     self.errors.append(f"Projector failed: {e}")     

    @property
    def projector(self):
        if self._projector is None:
            # Create the projector on first access.
            self._projector = Projector(1920, 1080)
        return self._projector
    
    def communication_check(self):
        print("\nRunning hardware communication check...")

        if self.errors:
            print("Errors detected:")
            for error in self.errors:
                print(f"  - {error}")
            print("Hardware check failed. Fix issues before proceeding.")
            self.healthy = False
        else:
            print("All hardware components are detected and responsive.")
            self.healthy = True


    def actuation_test(self):
        print(f"Beginning hardware actuation test...")

        # Stepper Motor Test
        print("Testing stepper")
        try:
            self.stepper.rotate_steps()
            self.stepper.stop()
        except Exception as e:
            print(f"Stepper test failed: {e}")
        finally:
            self.stepper.close()  # Ensure stepper is closed

        # LED Test
        print("Testing LEDs")
        try:
            self.led_array.clear_leds()
            self.led_array.set_led()
            time.sleep(5)
        except Exception as e:
            print(f"LED test failed: {e}")
        finally:
            self.led_array.clear_leds()  # Ensure LEDs are off

        # Camera Test
        print("Testing camera")
        try:
            print("Testing camera...press 'q' to quit")
            self.camera.start_camera()

            while True:
                frame = self.camera.read_frame()
                cv2.imshow("Camera Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except Exception as e:
            print(f"Camera test failed: {e}")
        finally:
            self.camera.stop_camera()  # Ensure camera shuts down
            cv2.destroyAllWindows()    # Close OpenCV windows
