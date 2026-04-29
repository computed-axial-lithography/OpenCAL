from opencal.hardware.stepper.interface import StepperMotorInterface
from opencal.utils.config import StepperConfigBase


class MockStepperMotor(StepperMotorInterface):
    def __init__(self, config: StepperConfigBase):
        self.default_rpm = config.default_rpm
        self.default_direction = config.default_direction
        self.encoder_cpr = config.encoder_cpr
        self._speed_rpm: float = config.default_rpm
        self._running = False
        self._steps = 0

    @property
    def speed_rpm(self) -> float:
        return self._speed_rpm

    def set_rpm(self, rpm: float | None = None, ramp_time: float = 0) -> None:
        self._speed_rpm = rpm or self.default_rpm
        print(f"[MockStepper] set_rpm {self._speed_rpm} (ramp_time={ramp_time} ignored)")

    def start_rotation(self, direction: str | None = None, ramp_time: float = 0) -> None:
        direction = direction or self.default_direction
        print(f"[MockStepper] start_rotation direction={direction}")
        self._running = True

    def stop(self) -> None:
        print("[MockStepper] stop")
        self._running = False

    def rotate_steps(self, steps: int, direction: str | None = None) -> None:
        direction = direction or self.default_direction
        delta = steps if direction == "CW" else -steps
        self._steps += delta
        print(f"[MockStepper] rotate_steps {steps} {direction} (total={self._steps})")

    def is_running(self) -> bool:
        return self._running

    def angle_in_steps(self) -> int:
        return self._steps % self.encoder_cpr

    def angle_in_degrees(self) -> float:
        return self.angle_in_steps() / self.encoder_cpr * 360
