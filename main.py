import threading
import cv2
import time
from hardware.hardware_controller import HardwareController
from gui.lcd_gui import LCDGui

class PrintController:
    def __init__(self, hardware=HardwareController()):
        self.hardware = hardware
        self.running = False

    def print(self, video_file):
        print("Starting print job...")
        self.running = True
        
        # Open video file
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            print(f"Failed to open video file: {video_file}")
            return

        # Start hardware
        # self.hardware.stepper.start_rotation() # Start stepper motor
        # self.hardware.led_array.set_led((255, 0, 0), set_all=True)  # Turn on LEDs

        # Get video FPS to sync frame timing
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30  # Default to 30 FPS if unknown

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    break  # End of video

                # Send frame to projector
                self.hardware.projector.display(frame)

                # Keep timing consistent
                time.sleep(frame_delay)

        except Exception as e:
            print(f"Error during print: {e}")

        finally:
            cap.release()
            # self.hardware.stepper.stop()
            # self.hardware.led_array.clear_leds()  # Turn off LEDs
            print("Print job complete.")

    def stop(self):
        print("Stopping print job...")
        self.running = False

def startup_sequence():
    """Run system checks before enabling the GUI."""
    print("System Starting Up...")
    hardware = HardwareController()

    # hardware.communication_check()  # Verify hardware comms
    return hardware

def main():
    hardware = startup_sequence()
    
    print_controller = PrintController(hardware)
    
    # Pass print_controller to the GUI
    gui = LCDGui(hardware, print_controller)

    # Start GUI in separate thread
    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    gui_thread.join()

if __name__ == "__main__":
    main()
