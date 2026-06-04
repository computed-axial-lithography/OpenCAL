"""
menus.py — Menu tree definition for OpenCAL.

Call build_menu_tree(pc, gui) to get the root NavigationMenu.
Add new menus here by composing NavigationMenu / ActionItem / VariableMenu /
MultiSelectMenu / PyGameMenu / DynamicNavigationMenu instances.
"""

import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from opencal.hardware import PrintController
from opencal.hardware.usb_manager import unique_path
from opencal.gui.lcd_gui import (
    MenuBase,
    NavigationMenu,
    DynamicNavigationMenu,
    ActionItem,
    VariableMenu,
    MultiSelectMenu,
    PyGameMenu,
    PrintStatusMenu,
)
from opencal.hardware.projector_controller import ProjectorOrientation

if TYPE_CHECKING:
    from opencal.gui.lcd_gui import LCDGui

_DARK_IMAGE = Path(__file__).parent.parent / "utils" / "calibration" / "dark.png"


# ---------------------------------------------------------------------------
# Custom item types
# ---------------------------------------------------------------------------


class PrintLaunchItem(MenuBase):
    """Represents a single .mp4 file in the 'Print from USB' menu."""

    def __init__(self, filename: str, pc: PrintController):
        self.title = filename
        self._filename = filename
        self._pc = pc
        self._gui_ref: Optional["LCDGui"] = None

    def on_activate(self, gui: "LCDGui") -> None:
        self._gui_ref = gui
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
        full_path = self._pc.hardware.usb_device.get_full_path(self._filename)
        self._pc.start_print_job(full_path)
        if self._gui_ref is not None:
            gui = self._gui_ref
            pc = self._pc
            def _stop() -> None:
                threading.Thread(target=pc.stop, daemon=True).start()
                if pc.ui_config.prompt_usb_video_save and pc.hardware.usb_device.is_mounted():
                    gui.push(VideoSaveMenu(pc))
                else:
                    gui.pop()
            gui.push(
                PrintStatusMenu(
                    pc=self._pc,
                    video_filename_short=self._filename,
                    on_stop=_stop,
                )
            )


class VideoSaveMenu(MenuBase):
    """Shown after stopping a print — lets the user save the video to USB."""

    title = "Save video to USB?"

    def __init__(self, pc: PrintController):
        self._pc = pc
        self._items = ["Yes", "No"]
        self._index = 0

    def on_enter(self, gui: "LCDGui") -> None:
        super().on_enter(gui)
        self._index = 0

    def on_rotate(self, delta: int) -> None:
        self._index = max(0, min(len(self._items) - 1, self._index + delta))

    def on_click(self) -> None:
        if self._gui is None:
            return
        save = self._items[self._index] == "Yes"
        self._gui.pop()  # pop VideoSaveMenu
        self._gui.pop()  # pop PrintStatusMenu
        if save:
            self._save_to_usb()

    def _save_to_usb(self) -> None:
        if self._gui is None:
            return
        if self._pc.recording_path is None:
            self._gui.splash("No recording found")
            return
        usb = self._pc.hardware.usb_device
        if not usb.is_mounted():
            self._gui.splash("No USB found")
            return
        try:
            dest = unique_path(usb.usb_save_path(self._pc.recording_path.name))
            shutil.copy2(self._pc.recording_path, dest)
            self._gui.splash("Video Saved!")
        except Exception as e:
            print(f"ERROR: Failed to save video to USB: {e}")
            self._gui.splash("Save Failed")

    def render(self) -> list[str]:
        return [
            "Save video to USB?".center(20),
            " " * 20,
            f"{'>' if self._index == 0 else ' '} Yes".ljust(20),
            f"{'>' if self._index == 1 else ' '} No".ljust(20),
        ]


# ---------------------------------------------------------------------------
# About menu
# ---------------------------------------------------------------------------


class AboutMenu(MenuBase):
    """Animated credits. Shows 'MADE BY' intro then auto-scrolls names. Click to exit."""

    title = "About"

    _NAMES: list[str] = [
        "X Sun",
        "Alvin Li",
        "Connor Vidmar",
        "Scarlett Hao",
        "Erfan Kohyarnejadfard",
        "Evan Percival",
        "Tristan Bourgade",
        "Angel Arambula",
        "Daniel Oslund",
        "Maya Lund",
        "Paul Morenkov",
        "Wangari Mbuthia",
        "Zev Schuman",
        "Bryan Vu",
        "Erik Broude",
        "Rajdeep Summan",
        "Ty Snyder",
        "Tamira Shany",
        "Tavleen Kaur",
        "Natalia De La Torre",
        "Carl Kruse",
        "Huy Tran",
        "Ian Bos",
    ]

    def __init__(self) -> None:
        self._phase = "intro"
        self._offset = 0
        self._stop_event = threading.Event()
        self._anim_thread: threading.Thread | None = None

    def on_enter(self, gui: "LCDGui") -> None:
        super().on_enter(gui)
        self._phase = "intro"
        self._offset = 0
        self._stop_event.clear()
        self._anim_thread = threading.Thread(target=self._animate, daemon=True)
        self._anim_thread.start()

    def on_exit(self) -> None:
        self._stop_event.set()

    def on_rotate(self, delta: int) -> None:
        pass  # auto-scroll only

    def on_click(self) -> None:
        if self._gui:
            self._gui.pop()

    def _animate(self) -> None:
        # Hold intro screen for 2 seconds
        self._stop_event.wait(2.0)
        if self._stop_event.is_set():
            return

        self._phase = "scroll"

        # Auto-scroll one line at a time
        max_offset = max(0, len(self._NAMES) - 4)
        while not self._stop_event.is_set():
            if self._offset >= max_offset:
                # Pause at end, then loop back to start
                self._stop_event.wait(3.0)
                if not self._stop_event.is_set():
                    self._offset = 0
            else:
                self._stop_event.wait(1.2)
                if not self._stop_event.is_set():
                    self._offset += 1

    def render(self) -> list[str]:
        if self._phase == "intro":
            return [
                " " * 20,
                "-- MADE BY --".center(20),
                " " * 20,
                " " * 20,
            ]
        lines = []
        for i in range(4):
            idx = self._offset + i
            if idx < len(self._NAMES):
                lines.append(self._NAMES[idx][:20].ljust(20))
            else:
                lines.append(" " * 20)
        return lines


# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------


def build_menu_tree(pc: PrintController, gui: "LCDGui") -> NavigationMenu:
    input_q = gui.input_q

    def _make_usb_items() -> list[MenuBase]:
        return [PrintLaunchItem(f, pc) for f in pc.hardware.usb_device.get_file_names()]

    def _make_calib_items() -> list[MenuBase]:
        calib_dir = pc.hardware.projector.calibration_dir_path
        return [
            PyGameMenu(
                title=f,
                input_q=input_q,
                mode_name="calibration",
                mode_kwargs={"image_path": calib_dir / f},
            )
            for f in pc.hardware.projector.get_calibration_file_names()
        ]

    def _apply_vial_result(result: dict) -> None:
        width = result.get("vial_width")
        if width is not None:
            pc.hardware.projector.show_vial_width(int(width))

    def _capture_image() -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}.jpeg"
        usb = pc.hardware.usb_device
        if usb.is_mounted():
            save_path = unique_path(usb.usb_save_path(filename))
            success_msg = "Saved to USB"
        else:
            save_path = None
            success_msg = "Image Captured"
        success = pc.hardware.camera.capture_image(save_path)
        gui.splash(success_msg if success else "Image error")

    def _toggle_usb_video_prompt() -> None:
        pc.ui_config.prompt_usb_video_save = not pc.ui_config.prompt_usb_video_save
        state = "On" if pc.ui_config.prompt_usb_video_save else "Off"
        gui.splash(f"USB prompt: {state}")

    settings_items: list[MenuBase] = [
        ActionItem("save as default", lambda: gui.save_defaults()),
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
        MultiSelectMenu(
            title="Display Orient.",
            choices=[o.value for o in ProjectorOrientation],
            get=pc.hardware.projector.get_projector_orientation,
            set=lambda s: pc.hardware.projector.set_projector_orientation(ProjectorOrientation(s)),
        ),
        ActionItem("USB video prompt", _toggle_usb_video_prompt),
        PyGameMenu(
            title="Find Vial Width",
            input_q=input_q,
            mode_name="vial_width",
            on_exit_callback=_apply_vial_result,
        ),
    ]

    return NavigationMenu(
        "main",
        items=[
            DynamicNavigationMenu("Print from USB", refresh=_make_usb_items),
            NavigationMenu(
                "Manual Control",
                items=[
                    ActionItem(
                        "Turn on LEDs", lambda: pc.hardware.led_manager.set_led((0, 240, 0, 0))
                    ),
                    ActionItem("Turn off LEDs", pc.hardware.led_manager.clear_leds),
                    ActionItem(
                        "Start stepper", lambda: pc.hardware.stepper.start_rotation(ramp_time=1)
                    ),
                    ActionItem("Stop stepper", pc.hardware.stepper.stop),
                    ActionItem("Capture image", _capture_image),
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
            AboutMenu(),
        ],
    )
