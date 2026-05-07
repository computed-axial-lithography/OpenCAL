from abc import ABC, abstractmethod


class StepperMotorInterface(ABC):
    default_rpm: float
    default_direction: str

    @property
    @abstractmethod
    def speed_rpm(self) -> float: ...

    @abstractmethod
    def set_rpm(self, rpm: float | None = None, ramp_time: float = 0) -> None: ...

    @abstractmethod
    def start_rotation(self, direction: str | None = None, ramp_time: float = 0) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def rotate_steps(self, steps: int, direction: str | None = None) -> None: ...

    @abstractmethod
    def is_running(self) -> bool: ...

    @abstractmethod
    def angle_in_steps(self) -> int: ...

    @abstractmethod
    def angle_in_degrees(self) -> float: ...
