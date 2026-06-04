import time
import threading
from gpiozero import RotaryEncoder
from ticlib import TicUSB

from opencal.utils.config import StepperConfig

_HEARTBEAT_INTERVAL = 0.2  # seconds — Tic default command timeout is 1000ms


class StepperMotor:
    def __init__(self, config: StepperConfig):
        """Initialize USB communication with the Tic 259 stepper motor controller."""
        self.tic = TicUSB()
        self.encoder = RotaryEncoder(config.encoder_a_pin, config.encoder_b_pin, max_steps=0)

        self.default_rpm = config.default_rpm
        self.speed_rpm = self.default_rpm
        self.default_direction = config.default_direction
        self._current_direction = self.default_direction
        self.steps_per_rev = config.steps_per_revolution
        self.encoder_cpr = config.encoder_cpr

        self._heartbeat_thread: threading.Thread | None = None
        self._finish_event = threading.Event()

        self.tic.deenergize()

    def _rpm_to_tic_velocity(self, rpm: float, direction: str) -> int:
        """Convert RPM and direction to Tic velocity units (microsteps per 10,000 seconds)."""
        steps_per_sec = rpm * self.steps_per_rev / 60
        velocity = int(steps_per_sec * 10000)
        return -velocity if direction == "CCW" else velocity

    def is_running(self) -> bool:
        return self._heartbeat_thread is not None and self._heartbeat_thread.is_alive()

    def set_rpm(self, rpm: float | None = None, ramp_time: float = 0):
        """Set the stepper motor speed in RPM. The Tic handles acceleration internally."""
        rpm = rpm or self.default_rpm
        if rpm <= 0:
            raise ValueError("RPM must be positive. Use stop() to halt the stepper.")
        print(f"INFO: Changing rpm from {self.speed_rpm} to {rpm}")
        self.speed_rpm = rpm
        if self.is_running():
            velocity = self._rpm_to_tic_velocity(rpm, self._current_direction)
            self.tic.set_target_velocity(velocity)
            self.tic.reset_command_timeout()

    def rotate_steps(self, steps: int, direction: str | None = None):
        """Rotate the stepper motor a specific number of steps."""
        direction = direction or self.default_direction
        print(f"INFO: Rotating {steps} steps {direction}")

        signed_steps = -steps if direction == "CCW" else steps
        target = self.tic.get_current_position() + signed_steps
        self.tic.set_target_position(target)

        while self.tic.get_current_position() != target:
            self.tic.reset_command_timeout()
            time.sleep(0.05)

    def angle_in_steps(self) -> int:
        return self.encoder.steps % self.encoder_cpr

    def angle_in_degrees(self) -> float:
        """Returns the motor angle in degrees from its angle at startup."""
        return self.angle_in_steps() / self.encoder_cpr * 360

    def start_rotation(self, direction: str | None = None, ramp_time: float = 0):
        """Start rotating the stepper motor continuously at the set speed."""
        direction = direction or self.default_direction
        self._current_direction = direction
        print(f"INFO: Starting continuous rotation {direction}")

        if self.is_running():
            print("WARNING: Stepper already running")
            return

        self.tic.energize()
        self.tic.exit_safe_start()

        velocity = self._rpm_to_tic_velocity(self.speed_rpm, direction)
        self.tic.set_target_velocity(velocity)
        self.tic.reset_command_timeout()

        self._finish_event.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        """Periodically reset the Tic command timeout to keep the motor running."""
        while not self._finish_event.is_set():
            self.tic.reset_command_timeout()
            self._finish_event.wait(timeout=_HEARTBEAT_INTERVAL)

    def stop(self):
        """Stop the motor."""
        print("INFO: Stopping the motor.")
        self._finish_event.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join()
        self.tic.deenergize()


if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    motor = StepperMotor(cfg.stepper)
    motor.set_rpm(20)
    motor.start_rotation()
    time.sleep(30.0)
    motor.stop()
