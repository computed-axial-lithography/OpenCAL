import time
import threading

from gpiozero import OutputDevice, RotaryEncoder

from opencal.hardware.stepper.interface import StepperMotorInterface
from opencal.utils.config import StepDirStepperConfig


class StepDirStepperMotor(StepperMotorInterface):
    def __init__(self, config: StepDirStepperConfig):
        self.step = OutputDevice(config.step_pin)
        self.direction = OutputDevice(config.dir_pin)
        self.encoder = RotaryEncoder(config.encoder_a_pin, config.encoder_b_pin, max_steps=0)
        self.enable = OutputDevice(config.enable_pin, active_high=False)
        self.enable.off()

        self.default_rpm = config.default_rpm
        self.default_direction = config.default_direction
        self.steps_per_rev = config.steps_per_revolution
        self.encoder_cpr = config.encoder_cpr

        self._speed_rpm: float = self.default_rpm
        self.step_delay = 60.0 / (self._speed_rpm * self.steps_per_rev)
        self._rotation_thread: threading.Thread | None = None
        self._finish_event = threading.Event()

    @property
    def speed_rpm(self) -> float:
        return self._speed_rpm

    def set_rpm(self, rpm: float | None = None, ramp_time: float = 0) -> None:
        print(f"INFO: Changing rpm from {self._speed_rpm} to {rpm} in {ramp_time} sec.")
        rpm = rpm or self.default_rpm
        if rpm <= 0:
            raise ValueError("RPM must be positive. Use stop() to halt the stepper.")

        if ramp_time == 0:
            self._speed_rpm = rpm
            self.step_delay = 60.0 / (self._speed_rpm * self.steps_per_rev)
        else:
            thread = threading.Thread(target=self._ramp_rpm, args=(rpm, ramp_time), daemon=True)
            thread.start()

    def _ramp_rpm(self, target: float, ramp_time: float) -> None:
        if ramp_time <= 0:
            raise ValueError("ramp_time must be positive")

        TIMESTEPS = 100
        dt = ramp_time / TIMESTEPS
        start_rpm = max(self._speed_rpm, 1)

        for i in range(TIMESTEPS):
            if self._finish_event.is_set():
                return
            self._speed_rpm = start_rpm + (target - start_rpm) * ((i + 1) / TIMESTEPS)
            self.step_delay = 60.0 / (self._speed_rpm * self.steps_per_rev)
            time.sleep(dt)

        self._speed_rpm = target
        self.step_delay = 60.0 / (self._speed_rpm * self.steps_per_rev)

    def rotate_steps(self, steps: int, direction: str | None = None) -> None:
        direction = direction or self.default_direction
        print(f"INFO: Rotating {steps} steps {direction}")

        if direction == "CW":
            self.direction.on()
        else:
            self.direction.off()

        prev_time = time.perf_counter()
        for _ in range(steps):
            self.step.on()
            elapsed_time = time.perf_counter() - prev_time
            time_to_sleep = self.step_delay - elapsed_time
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
            self.step.off()
            prev_time = time.perf_counter()

    def angle_in_steps(self) -> int:
        return self.encoder.steps % self.encoder_cpr

    def angle_in_degrees(self) -> float:
        return self.angle_in_steps() / self.encoder_cpr * 360

    def start_rotation(self, direction: str | None = None, ramp_time: float = 0) -> None:
        direction = direction or self.default_direction
        print(f"INFO: Starting continuous rotation {direction}")

        if direction == "CW":
            self.direction.on()
        else:
            self.direction.off()

        if self.is_running():
            print("WARNING: Stepper already running")
            return

        self.enable.on()

        if ramp_time > 0:
            target_rpm, self._speed_rpm = self._speed_rpm, 0
            self.set_rpm(target_rpm, ramp_time)

        self._finish_event.clear()
        self._rotation_thread = threading.Thread(target=self._rotate_motor, daemon=True)
        self._rotation_thread.start()

    def _rotate_motor(self) -> None:
        next_time = time.perf_counter()
        while not self._finish_event.is_set():
            self.step.on()
            self.step.off()

            next_time += self.step_delay
            sleep_time = next_time - time.perf_counter()

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_time = time.perf_counter()

    def is_running(self) -> bool:
        return self._rotation_thread is not None and self._rotation_thread.is_alive()

    def stop(self) -> None:
        print("INFO: Stopping the motor.")
        self._finish_event.set()

        if self._rotation_thread is not None:
            self._rotation_thread.join()

        self.step.off()
        self.enable.off()
