import time
import threading

from opencal.hardware.stepper.interface import StepperMotorInterface
from opencal.utils.config import UARTStepperConfig

_TMC_CLK_HZ = 12_000_000  # TMC2209 internal oscillator frequency


def _rpm_to_vactual(rpm: float, steps_per_rev: int) -> int:
    """Convert RPM to the VACTUAL register value for the TMC2209."""
    fstep = rpm * steps_per_rev / 60.0
    return round(fstep * (2**24) / _TMC_CLK_HZ)


class UARTStepperMotor(StepperMotorInterface):
    def __init__(self, config: UARTStepperConfig):
        self.default_rpm = config.default_rpm
        self.default_direction = config.default_direction
        self.steps_per_rev = config.steps_per_revolution
        self.encoder_cpr = config.encoder_cpr

        self._speed_rpm: float = config.default_rpm
        self._rotation_thread: threading.Thread | None = None
        self._finish_event = threading.Event()
        self._driver = None

        try:
            from pytrinamic.connections import UartIcInterface
            from pytrinamic.ic import TMC2209 as _TMC2209
            self._interface = UartIcInterface(config.uart_port, data_rate=config.baud_rate)
            self._ic = _TMC2209(self._interface, node_id=config.uart_address)
            self._TMC2209 = _TMC2209
            print("INFO: TMC2209 UART driver initialized.")
        except Exception as e:
            print(f"WARNING: UARTStepperMotor init failed: {e}")
            self._interface = None
            self._ic = None
            self._TMC2209 = None

    @property
    def speed_rpm(self) -> float:
        return self._speed_rpm

    def _write_vactual(self, vactual: int) -> None:
        if self._ic is None:
            return
        self._ic.write_register(self._TMC2209.REG.VACTUAL, vactual)

    def set_rpm(self, rpm: float | None = None, ramp_time: float = 0) -> None:
        print(f"INFO: Changing rpm from {self._speed_rpm} to {rpm} in {ramp_time} sec.")
        rpm = rpm or self.default_rpm
        if rpm <= 0:
            raise ValueError("RPM must be positive. Use stop() to halt the stepper.")

        if ramp_time == 0:
            self._speed_rpm = rpm
            self._write_vactual(self._signed_vactual(rpm))
        else:
            thread = threading.Thread(target=self._ramp_rpm, args=(rpm, ramp_time), daemon=True)
            thread.start()

    def _signed_vactual(self, rpm: float) -> int:
        """Return VACTUAL with sign encoding direction (positive=CW, negative=CCW)."""
        magnitude = _rpm_to_vactual(abs(rpm), self.steps_per_rev)
        return magnitude if self._current_direction == "CW" else -magnitude

    def _ramp_rpm(self, target: float, ramp_time: float) -> None:
        TIMESTEPS = 100
        dt = ramp_time / TIMESTEPS
        start_rpm = max(self._speed_rpm, 1)

        for i in range(TIMESTEPS):
            if self._finish_event.is_set():
                return
            self._speed_rpm = start_rpm + (target - start_rpm) * ((i + 1) / TIMESTEPS)
            self._write_vactual(self._signed_vactual(self._speed_rpm))
            time.sleep(dt)

        self._speed_rpm = target
        self._write_vactual(self._signed_vactual(self._speed_rpm))

    def start_rotation(self, direction: str | None = None, ramp_time: float = 0) -> None:
        direction = direction or self.default_direction
        self._current_direction = direction
        print(f"INFO: Starting UART rotation {direction}")

        if self.is_running():
            print("WARNING: Stepper already running")
            return

        self._finish_event.clear()

        if ramp_time > 0:
            target_rpm, self._speed_rpm = self._speed_rpm, 0
            self._write_vactual(0)
            self._rotation_thread = threading.Thread(target=self._run_until_stopped, daemon=True)
            self._rotation_thread.start()
            self.set_rpm(target_rpm, ramp_time)
        else:
            self._write_vactual(self._signed_vactual(self._speed_rpm))
            self._rotation_thread = threading.Thread(target=self._run_until_stopped, daemon=True)
            self._rotation_thread.start()

    def _run_until_stopped(self) -> None:
        self._finish_event.wait()

    def is_running(self) -> bool:
        return self._rotation_thread is not None and self._rotation_thread.is_alive()

    def stop(self) -> None:
        print("INFO: Stopping the motor.")
        self._write_vactual(0)
        self._finish_event.set()

        if self._rotation_thread is not None:
            self._rotation_thread.join()

    def rotate_steps(self, steps: int, direction: str | None = None) -> None:
        raise NotImplementedError("rotate_steps is not yet implemented for UART mode")

    def angle_in_steps(self) -> int:
        return 0

    def angle_in_degrees(self) -> float:
        return 0.0
