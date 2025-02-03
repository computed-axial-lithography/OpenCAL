import serial
import time
import json

class StepperMotor:
    def __init__(self, config_file="utils/config.json"):
        """Initialize UART communication with the stepper motor driver."""
        # Load config from the JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.port = config['stepper_motor'].get("serial_port", "/dev/serial0")
        self.baudrate = config['stepper_motor'].get("baudrate", 9600)
        
        # Initialize the serial connection
        self.serial = serial.Serial(self.port, self.baudrate)
        
        if self.serial.is_open:
            print(f"Connected to {self.port} at {self.baudrate} baud.")
        else:
            raise Exception("Failed to open UART connection.")
        
        # Default parameters
        self.default_speed = config['stepper_motor'].get("default_speed", 120)
        self.default_direction = config['stepper_motor'].get("default_direction", "CW")
        self.default_steps = config['stepper_motor'].get("default_steps", 200)

    def set_speed(self, rpm=None):
        """Set the stepper motor speed in RPM."""
        rpm = rpm or self.default_speed  # Use default if no rpm is provided
        command = f"SPEED:{rpm}\n"
        self.serial.write(command.encode())
        print(f"Sent: {command.strip()}")

    def rotate_steps(self, steps=None, direction=None):
        """
        Rotate the stepper motor.
        - steps: Number of steps to move.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        steps = steps or self.default_steps
        direction = direction or self.default_direction
        command = f"MOVE:{steps},{direction}\n"
        self.serial.write(command.encode())
        print(f"Sent: {command.strip()}")

    def start_rotation(self, direction=None):
        """
        Start rotating the stepper motor continuously at the set speed.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = direction or self.default_direction
        command = f"START:{direction}\n"
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
    motor.set_speed()  # Default speed from config (120 RPM)
    motor.rotate_steps()  # Default 200 steps, CW from config
    time.sleep(2)  # Wait 2 seconds
    motor.stop()
    motor.close()