from gpiozero import OutputDevice
from time import sleep
import json

class StepperMotor:
    def __init__(self, config_file="utils/config.json"):
        """Initialize GPIO communication with the stepper motor driver (Step/Dir mode)."""
        # Load config from the JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.step_pin = config['stepper_motor'].get("step_pin", 18)  # Set default to GPIO18
        self.dir_pin = config['stepper_motor'].get("dir_pin", 23)   # Set default to GPIO23
        self.enable_pin = config['stepper_motor'].get("enable_pin", None)  # Optional

        # Setup GPIO with gpiozero OutputDevice (using default pin factory)
        self.step = OutputDevice(self.step_pin)
        self.direction = OutputDevice(self.dir_pin)

        if self.enable_pin:
            self.enable = OutputDevice(self.enable_pin)
            self.enable.on()  # Enable the driver by default

        # Default parameters
        self.default_speed = config['stepper_motor'].get("default_speed", 120)
        self.default_direction = config['stepper_motor'].get("default_direction", "CW")
        self.default_steps = config['stepper_motor'].get("default_steps", 200)

    def set_speed(self, rpm=None):
        """Set the stepper motor speed in RPM (frequency of step pulses)."""
        rpm = rpm or self.default_speed  # Use default if no rpm is provided
        self.speed_rpm = rpm
        self.step_delay = 60 / (self.speed_rpm * self.default_steps)
        print(f"Speed set to {self.speed_rpm} RPM")

    def rotate_steps(self, steps=None, direction=None):
        """
        Rotate the stepper motor for a specified number of steps.
        - steps: Number of steps to move.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        steps = steps or self.default_steps
        direction = direction or self.default_direction
        print(f"Rotating {steps} steps {direction}")

        # Set direction
        if direction == "CW":
            self.direction.on()  # Clockwise
        else:
            self.direction.off()  # Counterclockwise

        # Generate step pulses
        for _ in range(steps):
            self.step.on()
            sleep(self.step_delay / 2)  # Pulse duration
            self.step.off()
            sleep(self.step_delay / 2)

    def start_rotation(self, direction=None):
        """
        Start rotating the stepper motor continuously at the set speed.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = direction or self.default_direction
        print(f"Starting continuous rotation {direction}")

        # Set direction
        if direction == "CW":
            self.direction.on()  # Clockwise
        else:
            self.direction.off()  # Counterclockwise

        # Generate continuous step pulses
        try:
            while True:
                self.step.on()
                sleep(self.step_delay / 2)  # Pulse duration
                self.step.off()
                sleep(self.step_delay / 2)
        except KeyboardInterrupt:
            print("Continuous rotation stopped.")
            self.stop()

    def stop(self):
        """Stop the stepper motor."""
        print("Stopping motor.")
        # Optional: Disable the driver if an enable pin is connected
        if self.enable_pin:
            self.enable.off()  # Disable motor

    def close(self):
        """Cleanup GPIO."""
        print("Closing motor connection.")
        # gpiozero handles cleanup automatically, no need to explicitly call GPIO.cleanup()

# Example usage (remove or modify during integration)
if __name__ == "__main__":
    motor = StepperMotor()
    motor.set_speed(200)  # Default speed from config (120 RPM)
    motor.start_rotation()  # Default 200 steps, CW from config
    sleep(2)  # Wait 2 seconds
    motor.stop()
    motor.close()
