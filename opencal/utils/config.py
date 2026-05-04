from pathlib import Path
import json
from typing import Any, final


CFG_PATH = Path(__file__).with_suffix(".json")


def load_config() -> "Config":
    return Config()


@final
class Config:
    def __init__(self, path: Path = CFG_PATH):
        with open(path) as f:
            config: dict[str, dict[str, Any]] = json.load(f)
        self.pygame = PygameConfig(config["pygame"])
        self.stepper = _make_stepper_config(config["stepper_motor"])
        self.camera = CameraConfig(config["camera"])
        self.led_array = LedArrayConfig(config["led_array"])
        self.lcd_display = LcdDisplayConfig(config["lcd_display"])
        self.rotary_encoder = RotaryConfig(config["rotary_encoder"])
        self.projector = ProjectorConfig(config["projector"])


class PygameConfig:
    def __init__(self, config: dict[str, Any]):
        self.active: bool = config["active"]

class StepperConfigBase:
    def __init__(self, config: dict[str, Any]):
        self.driver_mode: str = config.get("driver_mode", "step_dir")
        self.enable_pin: int | None = config.get("enable_pin")
        self.default_rpm: float = config["default_rpm"]
        self.default_direction: str = config["default_direction"]
        self.steps_per_revolution: int = config["steps_per_revolution"]
        self.encoder_cpr: int = config["encoder_cpr"]


class StepDirStepperConfig(StepperConfigBase):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.step_pin: int = config["step_pin"]
        self.dir_pin: int = config["dir_pin"]
        self.encoder_a_pin: int = config["A_pin"]
        self.encoder_b_pin: int = config["B_pin"]


class UARTStepperConfig(StepperConfigBase):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.uart_port: str = config["uart_port"]
        self.baud_rate: int = config["baud_rate"]
        self.uart_address: int = config["uart_address"]
        self.microsteps: int = config["microsteps"]


def _make_stepper_config(raw: dict[str, Any]) -> StepperConfigBase:
    mode: str = raw.get("driver_mode", "step_dir")
    if mode == "step_dir":
        return StepDirStepperConfig(raw)
    elif mode == "uart":
        return UARTStepperConfig(raw)
    elif mode == "mock":
        return StepperConfigBase(raw)
    raise ValueError(f"Unknown stepper driver_mode: {mode!r}")


class CameraConfig:
    def __init__(self, config: dict[str, Any]):
        self.type: str = config["type"]
        self.index: int = config["index"]
        self.save_path: str = config["save_path"]


class LedArrayConfig:
    def __init__(self, config: dict[str, Any]):
        self.num_led: int = config["num_led"]
        self.default_color: tuple[int, int, int] = tuple(config["default_color"])
        self.ring_indices: dict[str, list[int]] = config["ring_indices"]


class LcdDisplayConfig:
    def __init__(self, config: dict[str, Any]):
        self.port: str = config["port"]
        self.address: str = config["address"]
        self.cols: int = config["cols"]
        self.rows: int = config["rows"]


class RotaryConfig:
    def __init__(self, config: dict[str, Any]):
        self.clk_pin: int = config["clk_pin"]
        self.dt_pin: int = config["dt_pin"]
        self.btn_pin: int = config["btn_pin"]


class ProjectorConfig:
    def __init__(self, config: dict[str, Any]):
        self.default_print_size: int = config["default_print_size"]
        self.calibration_img_path: str = config["calibration_img_path"]
        self.calibration_dir_path: str = config["calibration_dir_path"]
