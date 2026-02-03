import time
import threading
from typing import final
from gpiozero import OutputDevice, RotaryEncoder


from opencal.utils.config import StepperConfig


ENCODER_CPR = 1000


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
        self.encoder = RotaryEncoder(
            config.encoder_a_pin, config.encoder_b_pin, max_steps=0
        )

        # Enable the driver if an enable pin is specified
        if self.enable_pin:
            self.enable = OutputDevice(self.enable_pin, active_high=False)
            self.enable.off()  # Disable the driver by default

        # Load default parameters from the configuration
        self.default_rpm = config.default_rpm
        self.speed_rpm = self.default_rpm  # Current speed in RPM
        self.default_direction = config.default_direction
        self.default_steps = config.default_steps

        # Calculate the delay between steps based on speed and steps per revolution
        # FIXME: I think self.default_steps should be 1000, not 1600
        self.step_delay = 60.00 / (self.default_rpm * self.default_steps)
        self._rotation_thread = None  # Reference to the thread for continuous rotation
        self._finish_event = threading.Event()
        self._running = False  # Flag to control whether the motor is currently running

    def set_rpm(self, rpm: float | None = None, ramp_time: float = 0):
        """Set the stepper motor speed in RPM (frequency of step pulses)."""
        rpm = rpm or self.default_rpm  # Use default speed if no RPM is provided
        if ramp_time == 0:
            self.speed_rpm = rpm
            # Recalculate step delay
            self.step_delay = 60.0 / (self.speed_rpm * self.default_steps)
            print(f"Speed set to {self.speed_rpm} RPM")  # Log the new speed
        else:
            thread = threading.Thread(target=self._ramp_rpm, args=(rpm, ramp_time))
            thread.start()

    def _ramp_rpm(self, target: float, ramp_time: float):
        if ramp_time <= 0:
            raise ValueError("ramp time must be positive")

        # Discretize into approximately sized intervals and increment RPM
        TIMESTEPS = 100
        dt = ramp_time / TIMESTEPS
        start_rpm = self.speed_rpm

        for i in range(TIMESTEPS):
            self.speed_rpm = start_rpm + (target - start_rpm) * ((i + 1) / TIMESTEPS)
            self.step_delay = 60.0 / (self.speed_rpm * self.default_steps)
            time.sleep(dt)
        # Set finally to ensure exact value achieved
        self.speed_rpm = target
        self.step_delay = 60.0 / (self.speed_rpm * self.default_steps)

    def rotate_steps(self, steps: int, direction: str | None = None):
        """
        Rotate the stepper motor for a specified number of steps.
        - steps: Number of steps to move.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = direction or self.default_direction
        print(f"Rotating {steps} steps {direction}")

        # Set the direction of rotation
        if direction == "CW":
            self.direction.on()
        else:
            self.direction.off()

        # Generate step pulses for the specified number of steps
        prev_time = time.perf_counter()  # Record the start time
        for _ in range(steps):
            self.step.on()  # Activate the step pin
            # Calculate the elapsed time and determine how long to sleep
            elapsed_time = time.perf_counter() - prev_time
            time_to_sleep = self.step_delay - elapsed_time
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)  # Sleep for the remaining time
            # FIXME: Should this be immediately after setting to high?
            self.step.off()  # Deactivate the step pin
            prev_time = time.perf_counter()  # Reset the start time for the next pulse

    def angle_in_steps(self) -> int:
        return self.encoder.steps % ENCODER_CPR

    def angle_in_degrees(self) -> float:
        """Returns the motor angle in degrees from it's angle at startup."""
        return self.angle_in_steps() / ENCODER_CPR * 360

    def start_rotation(self, direction: str | None = None):
        """
        Start rotating the stepper motor continuously at the set speed.

        :param direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = direction or self.default_direction
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
        while not self._finish_event.is_set():  # Continue while the motor is running
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
        self._finish_event.set()

        if self._rotation_thread is not None:
            self._rotation_thread.join()  # Wait for the thread to finish cleanly

        self.step.off()  # Deactivate the step pin
        if self.enable_pin:
            self.enable.off()  # Disable the motor if an enable pin is used


# Example usage (remove or modify during integration)
if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    motor = StepperMotor(cfg.stepper)  # Create an instance of the StepperMotor class
    motor.set_rpm(20)  # Set the motor speed to the default (20 RPM)
    motor.start_rotation()  # Start continuous rotation
    time.sleep(30.0)  # Run for 60 seconds
    # motor.rotate_steps(15, "CCW")  # Example of rotating a specific number of steps
    # time.sleep(2)  # Wait 2 seconds
    motor.stop()  # Stop the motor
