import time
import threading
from gpiozero import OutputDevice

import json

class StepperMotor:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        """Initialize GPIO communication with the stepper motor driver (Step/Dir mode)."""
        
        # Load configuration from the specified JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Set up GPIO pins for step, direction, and enable
        self.step_pin = config['stepper_motor'].get("step_pin", 18)  # Default to GPIO18
        self.dir_pin = config['stepper_motor'].get("dir_pin", 23)   # Default to GPIO23
        self.enable_pin = config['stepper_motor'].get("enable_pin", 27)  # Optional enable pin

        # Initialize GPIO output devices for step and direction
        self.step = OutputDevice(self.step_pin)
        self.direction = OutputDevice(self.dir_pin)

        # Enable the driver if an enable pin is specified
        if self.enable_pin:
            self.enable = OutputDevice(self.enable_pin)
            self.enable.on()  # Enable the driver by default

        # Load default parameters from the configuration
        self.default_speed = config['stepper_motor'].get("default_speed", 20)  # Default speed in RPM
        self.speed_rpm = self.default_speed  # Current speed in RPM
        self.default_direction = config['stepper_motor'].get("default_direction", "CW")  # Default direction
        self.default_steps = config['stepper_motor'].get("default_steps", 1600)  # Default number of steps

        # Calculate the delay between steps based on speed and steps per revolution
        self.step_delay = 60.00 / (self.default_speed * self.default_steps)
        self._rotation_thread = None  # Reference to the thread for continuous rotation
        self._running = False  # Flag to control whether the motor is currently running

    def enable(self, enable_on=True):
        """Enable or disable the stepper motor driver."""
        if enable_on:
            self.enable.on()  # Turn on the enable pin
        else:
            self.enable.off()  # Turn off the enable pin

    def set_speed(self, rpm=None):
        """Set the stepper motor speed in RPM (frequency of step pulses)."""
        rpm = rpm or self.default_speed  # Use default speed if no RPM is provided
        self.speed_rpm = rpm  # Update the current speed
        self.step_delay = 60.00 / (self.speed_rpm * self.default_steps)  # Recalculate step delay
        print(f"Speed set to {self.speed_rpm} RPM")  # Log the new speed

    def rotate_steps(self, steps=None, direction=None):
        """
        Rotate the stepper motor for a specified number of steps.
        - steps: Number of steps to move.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        steps = steps or self.default_steps  # Use default steps if not provided
        direction = direction or self.default_direction  # Use default direction if not provided
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

    def start_rotation(self, direction=None):
        """
        Start rotating the stepper motor continuously at the set speed.
        - direction: "CW" for clockwise, "CCW" for counterclockwise.
        """
        direction = direction or self.default_direction  # Use default direction if not provided
        print(f"Starting continuous rotation {direction}")  # Log the start of rotation

        # Set the direction of rotation
        if direction == "CW":
            self.direction.on()  # Set direction to clockwise
        else:
            self.direction.off()  # Set direction to counterclockwise

        # Start a new thread for continuous rotation if not already running
        if not self._running:
            self._running = True
            self._rotation_thread = threading.Thread(target=self._rotate_motor)
            self._rotation_thread.daemon = True  # Ensure the thread terminates with the program
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
    motor = StepperMotor()  # Create an instance of the StepperMotor class
    motor.set_speed(20)  # Set the motor speed to the default (20 RPM)
    motor.start_rotation()  # Start continuous rotation
    time.sleep(60.00)  # Run for 60 seconds
    #motor.rotate_steps(15, "CCW")  # Example of rotating a specific number of steps
    # time.sleep(2)  # Wait 2 seconds
    motor.stop()  # Stop the motor
    motor.close()  # Cleanup GPIO resources
