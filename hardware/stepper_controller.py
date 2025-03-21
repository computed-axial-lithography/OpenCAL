from gpiozero import OutputDevice
from time import sleep
import json
import threading

class StepperMotor:
    def __init__(self, config_file="/home/opencal/opencal/OpenCAL/utils/config.json"):
        """Initialize GPIO communication with the stepper motor driver (Step/Dir mode)."""
        # Load config from the JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.step_pin = config['stepper_motor'].get("step_pin", 18)  # Set default to GPIO18
        self.dir_pin = config['stepper_motor'].get("dir_pin", 23)   # Set default to GPIO23
        self.enable_pin = config['stepper_motor'].get("enable_pin", 27)  # Optional

        # Setup GPIO with gpiozero OutputDevice (using default pin factory)
        self.step = OutputDevice(self.step_pin)
        self.direction = OutputDevice(self.dir_pin)

        if self.enable_pin:
            self.enable = OutputDevice(self.enable_pin)
            self.enable.on()  # Enable the driver by default

        # Default parameters
        self.default_speed = config['stepper_motor'].get("default_speed", 20)
        self.speed_rpm = self.default_speed
        self.default_direction = config['stepper_motor'].get("default_direction", "CW")
        self.default_steps = config['stepper_motor'].get("default_steps", 1600)

        self.step_delay = 60 / (self.default_speed * self.default_steps)
        self._rotation_thread = None  # Reference to the rotation thread
        self._running = False  # Flag to control whether the motor is running

    def enable(self, enable_on=True):
        if enable_on:
            self.enable.on()
        else:
            self.enable.off()

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
        if not self._running:
            self._running = True
            self._rotation_thread = threading.Thread(target=self._rotate_motor)
            self._rotation_thread.daemon = True  # Ensure the thread terminates with the program
            self._rotation_thread.start()

    def _rotate_motor(self):
        """Rotate the motor continuously in a separate thread."""
        try:
            while self._running:
                self.step.on()
                sleep(self.step_delay / 2)  # Pulse duration
                self.step.off()
                sleep(self.step_delay / 2)
        except KeyboardInterrupt:
            print("Continuous rotation interrupted.")
            self.stop()

    def stop(self):
        """Stop the rotation."""
        print("Stopping the motor.")
        self._running = False  # Set the flag to stop the rotation
        if self._rotation_thread is not None:
            self._rotation_thread.join()  # Wait for the thread to finish cleanly
        self.step.off()
        #self.direction.off()
        if self.enable_pin:
            self.enable.off()  # Disable motor

    def close(self):
        """Cleanup GPIO."""
        print("Closing motor connection.")
        # gpiozero handles cleanup automatically, no need to explicitly call GPIO.cleanup()

# Example usage (remove or modify during integration)
if __name__ == "__main__":
    motor = StepperMotor()
    motor.set_speed(20) # Default speed from config (120 RPM)
    motor.start_rotation()  # Default 200 steps, CW from config
    sleep(2)  # Wait 2 seconds
    motor.stop()
    motor.close()
