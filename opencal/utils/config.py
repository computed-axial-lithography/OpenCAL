
from pathlib import Path
import json
from typing import Any, final


CFG_PATH = Path(__file__).with_suffix('.json')


@final
class Config:
    def __init__(self, path: Path = CFG_PATH):
        with open(path) as f:
            config: dict[str, dict[str, Any]] = json.load(f)
        self.stepper = StepperConfig(config['stepper_motor'])
        self.camera = CameraConfig(config['camera'])
        self.led_array = LedArrayConfig(config['led_array'])
        self.lcd_display = LcdDisplayConfig(config['lcd_display'])
        self.rotary_encoder = RotaryConfig(config['rotary_encoder'])
        self.projector = ProjectorConfig(config['projector'])

class StepperConfig:
    def __init__(self, config: dict[str, Any]):
        self.step_pin: int = config['step_pin']
        self.dir_pin: int= config['dir_pin']
        self.enable_pin: int = config['enable_pin']
        self.default_speed: int = config['default_speed']
        self.default_direction: str = config['default_direction']
        self.default_steps: int = config['default_steps']


class CameraConfig:
    def __init__(self, config: dict[str, Any]):
        self.type: str = config['type']
        self.index: int = config['index']
        self.save_path: str = config['save_path']


class LedArrayConfig:
    def __init__(self, config: dict[str, Any]):
        self.num_led: int = config['num_led']
        self.default_color: tuple[int, int, int] = tuple(config['default_color'])
        self.ring_indices: dict[str, list[int]] = config['ring_indices']

class LcdDisplayConfig:
    def __init__(self, config: dict[str, Any]):
        self.port: str = config['port']
        self.address: str = config['address']
        self.cols: int = config['cols']
        self.rows: int = config['rows']


class RotaryConfig:
    def __init__(self, config: dict[str, Any]):
        self.clk_pin: int = config['clk_pin']
        self.dt_pin: int = config['dt_pin']
        self.btn_pin: int = config['btn_pin']


class ProjectorConfig:
    def __init__(self, config: dict[str, Any]):
        self.default_print_size: int = config['default_print_size']
        self.calibration_img_path: str = config['calibration_img_path']

        


    
