"""
menus.py — Menu tree definition for OpenCAL.

Call build_menu_tree(pc, gui) to get the root NavigationMenu.
Add new menus here by composing NavigationMenu / ActionItem / VariableMenu /
MultiSelectMenu / PyGameMenu / DynamicNavigationMenu instances.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from opencal.hardware import PrintController
from opencal.gui.lcd_gui import (
    MenuBase,
    NavigationMenu,
    DynamicNavigationMenu,
    ActionItem,
    VariableMenu,
    MultiSelectMenu,
    PyGameMenu,
    PrintStatusMenu,
    StaticMenu,
)

if TYPE_CHECKING:
    from opencal.gui.lcd_gui import LCDGui

_DARK_IMAGE = Path(__file__).parent.parent / "utils" / "calibration" / "dark.png"


# ---------------------------------------------------------------------------
# Custom item types
# ---------------------------------------------------------------------------


class PrintLaunchItem(MenuBase):
    """Represents a single .mp4 file in the 'Print from USB' menu.

    Selecting it:
      1. Blackens the projector screen.
      2. Pushes a VariableMenu to let the user set the print RPM.
      3. On RPM confirmation: sets RPM, starts the print job, and pushes
         a PrintStatusMenu so the user can monitor / stop the print.
    """

    def __init__(self, filename: str, pc: PrintController):
        self.title = filename
        self._filename = filename
        self._pc = pc
        self._gui_ref: "LCDGui | None" = None

    def on_activate(self, gui: "LCDGui") -> None:
        self._gui_ref = gui
        # Black out the projector while the user sets RPM.
        self._pc.hardware.projector.display_image(_DARK_IMAGE)
        gui.push(
            VariableMenu(
                title="RPM",
                get=lambda: self._pc.hardware.stepper.speed_rpm,
                set=lambda v: self._pc.hardware.stepper.set_rpm(v),
                min_val=1,
                max_val=60,
                step=1,
                hint=self._filename[:20],
                on_confirm=self._on_rpm_confirmed,
            )
        )

    def _on_rpm_confirmed(self, _rpm: float) -> None:
        # RPM was already applied by VariableMenu._set; just start the print.
        full_path = self._pc.hardware.usb_device.get_full_path(self._filename)
        self._pc.start_print_job(full_path)
        if self._gui_ref is not None:
            self._gui_ref.push(
                PrintStatusMenu(
                    pc=self._pc,
                    video_filename_short=self._filename,
                )
            )


class CalibActionItem(MenuBase):
    """Represents a calibration image file in the 'Calibration' menu.

    Selecting it displays the image on the projector and shows a static
    'Calibrating' screen. Clicking that screen returns to the Calibration menu.
    """

    def __init__(self, filename: str, pc: PrintController):
        self.title = filename
        self._filename = filename
        self._pc = pc

    def on_activate(self, gui: "LCDGui") -> None:
        projector = self._pc.hardware.projector
        path = projector.calibration_dir_path / self._filename
        projector.display_image(path)
        gui.push(
            StaticMenu(
                title="Calibrating",
                lines=[
                    "Calibrating".center(20),
                    self._filename[:20].ljust(20),
                    " " * 20,
                    "Click to go back".center(20),
                ],
            )
        )


# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------


def build_menu_tree(pc: PrintController, gui: "LCDGui") -> NavigationMenu:
    """Build and return the root NavigationMenu for the OpenCAL interface.

    Parameters
    ----------
    pc:  PrintController owning all hardware.
    gui: The LCDGui instance (used for utility callbacks like kill_gui,
         save_defaults, restart_pi, power_off_pi).
    """

    encoder_q = gui.encoder_q

    def _make_usb_items() -> list[MenuBase]:
        return [PrintLaunchItem(f, pc) for f in pc.hardware.usb_device.get_file_names()]

    def _make_calib_items() -> list[MenuBase]:
        return [CalibActionItem(f, pc) for f in pc.hardware.projector.get_calibration_file_names()]

    def _apply_vial_result(result: dict) -> None:
        width = result.get("vial_width")
        if width is not None:
            pc.hardware.projector.show_vial_width(int(width))

    settings_items: list[MenuBase] = [
        ActionItem(
            "save as default",
            lambda: gui.save_defaults(),
        ),
        VariableMenu(
            title="Resize Print",
            get=lambda: pc.hardware.projector.size,
            set=lambda v: pc.hardware.projector.resize(int(v)),
            min_val=1,
            max_val=100,
            step=1,
        ),
        VariableMenu(
            title="Set Stepper RPM",
            get=lambda: pc.hardware.stepper.speed_rpm,
            set=lambda v: pc.hardware.stepper.set_rpm(v, ramp_time=1),
            min_val=1,
            max_val=60,
            step=1,
        ),
        DynamicNavigationMenu("Calibration", refresh=_make_calib_items),
    ]

    # Only add Find Vial Width if the encoder queue is available.
    if encoder_q is not None:
        settings_items.append(
            PyGameMenu(
                title="Find Vial Width",
                encoder_q=encoder_q,
                on_exit_callback=_apply_vial_result,
            )
        )

    return NavigationMenu(
        "main",
        items=[
            DynamicNavigationMenu("Print from USB", refresh=_make_usb_items),
            NavigationMenu(
                "Manual Control",
                items=[
                    ActionItem(
                        "Turn on LEDs", lambda: pc.hardware.led_manager.set_led((255, 0, 0))
                    ),
                    ActionItem("Turn off LEDs", pc.hardware.led_manager.clear_leds),
                    ActionItem(
                        "Start stepper", lambda: pc.hardware.stepper.start_rotation(ramp_time=1)
                    ),
                    ActionItem("Stop stepper", pc.hardware.stepper.stop),
                    ActionItem(
                        "Capture image", lambda: pc.hardware.camera.capture_image("test.jpeg")
                    ),
                ],
            ),
            NavigationMenu("Settings", items=settings_items),
            NavigationMenu(
                "Power Options",
                items=[
                    ActionItem("Kill GUI", gui.kill_gui),
                    ActionItem("Restart", gui.restart_pi),
                    ActionItem("Power Off", gui.power_off_pi),
                ],
            ),
        ],
    )
