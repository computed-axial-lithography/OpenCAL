from hardware import HardwareController
import cv2

def main():
    hardware = HardwareController()

    try:
        # Start hardware
        hardware.start_all()
        print("Press 'q' to quit.")

        # Stream video
        while True:
            frame = hardware.capture_frame()
            cv2.imshow("Camera Feed", frame)

            # Break the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Stop hardware
        hardware.stop_all()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()