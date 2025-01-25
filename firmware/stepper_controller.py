import serial
import time

class StepperMotor:
    def __init__(self, port="/dev/serial0", baudrate=9600):
        """Initialize UART communication with the stepper motor driver."""
        self.serial = serial.Serial(port, baudrate)
        if self.serial.is_open:
            print(f"Connected to {port} at {baudrate} baud.")
        else:
            raise Exception("Failed to open UART connection.")

    def set_speed(self, rpm):
        """Set the stepper motor speed in RPM."""
        command = f"SPEED:{rpm}\n"
        self.serial.write(command.encode())
        print(f"Sent: {command.strip()}")

    def rotate(self, steps, direction="CW"):
        """
        Rotate the stepper motor.
        - steps: Number of steps to move.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        command = f"MOVE:{steps},{direction}\n"
        self.serial.write(command.encode())
        print(f"Sent: {command.strip()}")

    def stop(self):
        """Stop the stepper motor."""
        command = "STOP\n"
        self.serial.write(command.encode())
        print("Sent: STOP")

    def close(self):
        """Close the UART connection."""
        self.serial.close()
        print("Connection closed.")

# Example usage (remove or modify during integration)
if __name__ == "__main__":
    motor = StepperMotor()
    motor.set_speed(120)  # 120 RPM
    motor.rotate(200, "CW")  # Rotate 200 steps clockwise
    time.sleep(2)  # Wait 2 seconds
    motor.stop()
    motor.close()
