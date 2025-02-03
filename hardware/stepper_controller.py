import RPi.GPIO as GPIO
import time
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
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)

        if self.enable_pin:
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.output(self.enable_pin, GPIO.HIGH)  # Enable the driver by default

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
            GPIO.output(self.dir_pin, GPIO.HIGH)  # Clockwise
        else:
            GPIO.output(self.dir_pin, GPIO.LOW)   # Counterclockwise

        # Generate step pulses
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(self.step_delay / 2)  # Pulse duration
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(self.step_delay / 2)

    def start_rotation(self, direction=None):
        """
        Start rotating the stepper motor continuously at the set speed.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = direction or self.default_direction
        print(f"Starting continuous rotation {direction}")

        # Set direction
        if direction == "CW":
            GPIO.output(self.dir_pin, GPIO.HIGH)  # Clockwise
        else:
            GPIO.output(self.dir_pin, GPIO.LOW)   # Counterclockwise

        # Generate continuous step pulses
        try:
            while True:
                GPIO.output(self.step_pin, GPIO.HIGH)
                time.sleep(self.step_delay / 2)  # Pulse duration
                GPIO.output(self.step_pin, GPIO.LOW)
                time.sleep(self.step_delay / 2)
        except KeyboardInterrupt:
            print("Continuous rotation stopped.")
            self.stop()

    def stop(self):
        """Stop the stepper motor."""
        print("Stopping motor.")
        # Optional: Disable the driver if an enable pin is connected
        if self.enable_pin:
            GPIO.output(self.enable_pin, GPIO.LOW)  # Disable motor

    def close(self):
        """Cleanup GPIO and close the communication."""
        GPIO.cleanup()
        print("GPIO cleanup done. Connection closed.")

# Example usage (remove or modify during integration)
if __name__ == "__main__":
    motor = StepperMotor()
    motor.set_speed()  # Default speed from config (120 RPM)
    motor.rotate_steps()  # Default 200 steps, CW from config
    time.sleep(2)  # Wait 2 seconds
    motor.stop()
    motor.close()
