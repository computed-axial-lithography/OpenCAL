import time
import threading
from typing import final
from gpiozero import OutputDevice


from opencal.utils.config import StepperConfig


@final
class StepperMotor:
    def __init__(self, config: StepperConfig):
        """Initialize GPIO communication with the stepper motor driver (Step/Dir mode)."""

        # Load configuration from the specified JSON file

        # Set up GPIO pins for step, direction, and enable
        self.step_pin = config.step_pin
        self.dir_pin = config.dir_pin
        self.enable_pin = config.enable_pin

        # Initialize GPIO output devices for step and direction
        self.step = OutputDevice(self.step_pin)
        self.direction = OutputDevice(self.dir_pin)

        # Enable the driver if an enable pin is specified
        if self.enable_pin:
            self.enable = OutputDevice(self.enable_pin, active_high=False)
            self.enable.off()  # Disable the driver by default

        # Load default parameters from the configuration
        self.default_speed = config.default_speed
        self.speed_rpm = self.default_speed  # Current speed in RPM
        self.default_direction = config.default_direction
        self.default_steps = config.default_steps

        # Calculate the delay between steps based on speed and steps per revolution
        self.step_delay = 60.00 / (self.default_speed * self.default_steps)
        self._rotation_thread = None  # Reference to the thread for continuous rotation
        self._running = False  # Flag to control whether the motor is currently running

    def set_speed(self, rpm: int | None = None):
        """Set the stepper motor speed in RPM (frequency of step pulses)."""
        rpm = rpm or self.default_speed  # Use default speed if no RPM is provided
        self.speed_rpm = rpm  # Update the current speed
        self.step_delay = 60.00 / (
            self.speed_rpm * self.default_steps
        )  # Recalculate step delay
        print(f"Speed set to {self.speed_rpm} RPM")  # Log the new speed

    def rotate_steps(self, steps: int | None = None, direction: str | None = None):
        """
        Rotate the stepper motor for a specified number of steps.
        - steps: Number of steps to move.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        steps = steps or self.default_steps  # Use default steps if not provided
        direction = (
            direction or self.default_direction
        )  # Use default direction if not provided
        print(f"Rotating {steps} steps {direction}")  # Log the rotation command

        # Set the direction of rotation
        if direction == "CW":
            self.direction.on()  # Set direction to clockwise
        else:
            self.direction.off()  # Set direction to counterclockwise

        # Generate step pulses for the specified number of steps
        start_time = time.perf_counter()  # Record the start time
        for _ in range(steps):
            self.step.on()  # Activate the step pin
            # Calculate the elapsed time and determine how long to sleep
            elapsed_time = time.perf_counter() - start_time
            time_to_sleep = self.step_delay - elapsed_time
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)  # Sleep for the remaining time
            self.step.off()  # Deactivate the step pin
            start_time = time.perf_counter()  # Reset the start time for the next pulse

    def start_rotation(self, direction: str | None = None):
        """
        Start rotating the stepper motor continuously at the set speed.

        :param direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = (
            direction or self.default_direction
        )  # Use default direction if not provided
        print(f"Starting continuous rotation {direction}")  # Log the start of rotation

        # Set the direction of rotation
        if direction == "CW":
            self.direction.on()  # Set direction to clockwise
        else:
            self.direction.off()  # Set direction to counterclockwise

        # Start a new thread for continuous rotation if not already running
        if not self._running:
            print("Starting a new thread for rotation")
            self._running = True

            if self.enable_pin:
                self.enable.on()

            self._rotation_thread = threading.Thread(
                target=self._rotate_motor, daemon=True
            )
            self._rotation_thread.start()  # Start the rotation thread

    def _rotate_motor(self):
        """Internal method to handle continuous rotation of the motor."""
        next_time = time.perf_counter()  # Initialize the next time for scheduling
        while self._running:  # Continue while the motor is running
            self.step.on()  # Activate the step pin
            self.step.off()  # Deactivate the step pin

            # Schedule the next step based on the step delay
            next_time += self.step_delay
            sleep_time = next_time - time.perf_counter()  # Calculate how long to sleep
            if sleep_time > 0:
                time.sleep(sleep_time)  # Sleep for the calculated time
            else:
                # If we're behind schedule, adjust the next_time
                next_time = time.perf_counter()  # Reset next_time to current time

    def stop(self):
        """Stop the rotation of the motor."""
        print("Stopping the motor.")  # Log the stop command
        self._running = False  # Set the flag to stop the rotation
        if self._rotation_thread is not None:
            self._rotation_thread.join()  # Wait for the thread to finish cleanly
        self.step.off()  # Deactivate the step pin
        if self.enable_pin:
            self.enable.off()  # Disable the motor if an enable pin is used

    def close(self):
        """Cleanup GPIO resources."""
        print("Closing motor connection.")  # Log the cleanup command
        # gpiozero handles cleanup automatically, no need to explicitly call GPIO.cleanup()


# Example usage (remove or modify during integration)
if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    motor = StepperMotor(cfg.stepper)  # Create an instance of the StepperMotor class
    motor.set_speed(20)  # Set the motor speed to the default (20 RPM)
    motor.start_rotation()  # Start continuous rotation
    time.sleep(30.0)  # Run for 60 seconds
    # motor.rotate_steps(15, "CCW")  # Example of rotating a specific number of steps
    # time.sleep(2)  # Wait 2 seconds
    motor.stop()  # Stop the motor
    motor.close()  # Cleanup GPIO resources
