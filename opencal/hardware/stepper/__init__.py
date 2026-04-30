from .interface import StepperMotorInterface
from opencal.utils.config import StepperConfigBase


def create_stepper(config: StepperConfigBase) -> StepperMotorInterface:
    mode = config.driver_mode
    if mode == "step_dir":
        from .step_dir import StepDirStepperMotor

        return StepDirStepperMotor(config)  # pyright: ignore[reportArgumentType]
    elif mode == "uart":
        from .uart import UARTStepperMotor

        return UARTStepperMotor(config)  # pyright: ignore[reportArgumentType]
    elif mode == "mock":
        from .mock import MockStepperMotor

        return MockStepperMotor(config)

    raise ValueError(f"Unknown stepper driver_mode: {mode!r}")
