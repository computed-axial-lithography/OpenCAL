"""
lcd_gui.py — LCDGui state machine + menu base classes.

Menu types
----------
MenuBase              Abstract base for all menu/item types.
NavigationMenu        Scrollable list of child items; "back" auto-added.
DynamicNavigationMenu Like NavigationMenu but refreshes its item list on entry.
ActionItem            Leaf: label + callback, no stack change.
VariableMenu          Rotate to adjust a float value; click to confirm.
MultiSelectMenu       Pick one of N string choices from a submenu-style list.
PyGameMenu            Routes encoder to pygame; waits for ("done", result) signal.
PrintStatusMenu       Shows print progress; click stops the job.
StaticMenu            Read-only display; click pops to parent.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable
from enum import Enum

from opencal.hardware import PrintController

CONFIG_PATH = Path(__file__).parent.parent / "utils" / "config.json"

# Legacy sys.path hack kept for compatibility with any direct-run scripts.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class Mode(Enum):
    MENU = "menu"
    PYGAME = "pygame"
    PRINTING = "printing"


# ---------------------------------------------------------------------------
# Menu base
# ---------------------------------------------------------------------------


class MenuBase:
    """Abstract base class for all menu items."""

    title: str = ""
    _gui: "LCDGui" | None = None

    def on_enter(self, gui: "LCDGui") -> None:
        """Called when this menu is pushed onto the stack."""
        self._gui = gui

    def on_exit(self) -> None:
        """Called when this menu is popped off the stack."""
        pass

    def on_rotate(self, delta: int) -> None:
        """Called on rotary encoder turn. delta is +1 (CW) or -1 (CCW)."""
        pass

    def on_click(self) -> None:
        """Called on rotary encoder button press."""
        pass

    def on_activate(self, gui: "LCDGui") -> None:
        """Called by a parent NavigationMenu when this item is selected.
        Default: push self onto the stack."""
        gui.push(self)

    def render(self) -> list[str]:
        """Return exactly 4 strings of up to 20 characters each for the LCD."""
        return [" " * 20] * 4


# ---------------------------------------------------------------------------
# Internal back-button item
# ---------------------------------------------------------------------------


class _BackItem(MenuBase):
    title = "back"

    def on_activate(self, gui: "LCDGui") -> None:
        gui.pop()


# ---------------------------------------------------------------------------
# NavigationMenu
# ---------------------------------------------------------------------------


class NavigationMenu(MenuBase):
    """Scrollable list of child items. A 'back' entry is prepended automatically
    unless this is the root menu (nothing else on the stack)."""

    VIEW_SIZE = 4

    def __init__(self, title: str, items: list[MenuBase]):
        self.title = title
        self._items = list(items)
        self._all_items: list[MenuBase] = []
        self._current_index = 0
        self._view_start = 0

    def on_enter(self, gui: "LCDGui") -> None:
        super().on_enter(gui)
        # Prepend back unless this is the root (stack is empty at push time).
        if len(gui.stack) > 0:
            back = _BackItem()
            back._gui = gui
            self._all_items = [back] + self._items
        else:
            self._all_items = list(self._items)
        # Pre-populate _gui on children so callbacks work before they're pushed.
        for item in self._all_items:
            item._gui = gui
        self._current_index = 0
        self._view_start = 0

    def on_rotate(self, delta: int) -> None:
        new_idx = self._current_index + delta
        self._current_index = max(0, min(len(self._all_items) - 1, new_idx))
        # Slide the 4-line viewport to keep selection visible.
        if self._current_index < self._view_start:
            self._view_start = self._current_index
        elif self._current_index >= self._view_start + self.VIEW_SIZE:
            self._view_start = self._current_index - self.VIEW_SIZE + 1

    def on_click(self) -> None:
        if not self._all_items or self._gui is None:
            return
        item = self._all_items[self._current_index]
        item.on_activate(self._gui)

    def render(self) -> list[str]:
        lines: list[str] = []
        for i in range(self.VIEW_SIZE):
            idx = i + self._view_start
            if idx < len(self._all_items):
                prefix = ">" if idx == self._current_index else " "
                label = self._all_items[idx].title
                lines.append(f"{prefix}{label}".ljust(20))
            else:
                lines.append(" " * 20)
        return lines


# ---------------------------------------------------------------------------
# DynamicNavigationMenu
# ---------------------------------------------------------------------------


class DynamicNavigationMenu(NavigationMenu):
    """Like NavigationMenu but calls refresh() each time the menu is entered
    to rebuild the item list (e.g. USB file list, calibration files)."""

    def __init__(self, title: str, refresh: Callable[[], list[MenuBase]]):
        super().__init__(title, [])
        self._refresh = refresh

    def on_enter(self, gui: "LCDGui") -> None:
        self._items = self._refresh()
        super().on_enter(gui)


# ---------------------------------------------------------------------------
# ActionItem
# ---------------------------------------------------------------------------


class ActionItem(MenuBase):
    """Leaf item: shows a label; executing it calls a callback.
    Does not push anything onto the stack."""

    def __init__(self, title: str, callback: Callable[[], None]):
        self.title = title
        self._callback = callback

    def on_activate(self, gui: "LCDGui") -> None:
        self._callback()

    def render(self) -> list[str]:
        return [self.title.ljust(20)] + [" " * 20] * 3


# ---------------------------------------------------------------------------
# VariableMenu
# ---------------------------------------------------------------------------


class VariableMenu(MenuBase):
    """Rotate to adjust a numeric value within [min_val, max_val].
    Click to confirm: calls set(value), pops the menu, then fires on_confirm."""

    def __init__(
        self,
        title: str,
        get: Callable[[], float],
        set: Callable[[float], None],
        min_val: float,
        max_val: float,
        step: float = 1.0,
        hint: str = "",
        on_confirm: Callable[[float], None] | None = None,
    ):
        self.title = title
        self._get = get
        self._set = set
        self._min = min_val
        self._max = max_val
        self._step = step
        self._hint = hint
        self.on_confirm = on_confirm
        self._value: float = 0.0

    def on_enter(self, gui: "LCDGui") -> None:
        super().on_enter(gui)
        self._value = self._get()

    def on_rotate(self, delta: int) -> None:
        self._value = max(self._min, min(self._max, self._value + delta * self._step))

    def on_click(self) -> None:
        self._set(self._value)
        if self._gui:
            self._gui.pop()
        # Fire on_confirm after pop so it can safely push new menus.
        if self.on_confirm:
            self.on_confirm(self._value)

    def render(self) -> list[str]:
        return [
            f"{self.title}: {int(self._value)}".ljust(20),
            "Use rotary to adjust",
            "Click to set".ljust(20),
            self._hint[:20].ljust(20),
        ]


# ---------------------------------------------------------------------------
# MultiSelectMenu
# ---------------------------------------------------------------------------


class MultiSelectMenu(MenuBase):
    """Pick one string from a list. Renders like a NavigationMenu with (*) on
    the current selection. Includes a 'back' entry to cancel without changing
    the value."""

    VIEW_SIZE = 4

    def __init__(
        self,
        title: str,
        choices: list[str],
        get: Callable[[], str],
        set: Callable[[str], None],
    ):
        self.title = title
        self._choices = list(choices)
        self._get = get
        self._set = set
        self._items = ["back"] + self._choices
        self._current_index = 0
        self._view_start = 0

    def on_enter(self, gui: "LCDGui") -> None:
        super().on_enter(gui)
        self._current_index = 0
        self._view_start = 0

    def on_rotate(self, delta: int) -> None:
        new_idx = self._current_index + delta
        self._current_index = max(0, min(len(self._items) - 1, new_idx))
        if self._current_index < self._view_start:
            self._view_start = self._current_index
        elif self._current_index >= self._view_start + self.VIEW_SIZE:
            self._view_start = self._current_index - self.VIEW_SIZE + 1

    def on_click(self) -> None:
        if self._gui is None:
            return
        label = self._items[self._current_index]
        if label == "back":
            self._gui.pop()
        else:
            self._set(label)
            self._gui.pop()

    def render(self) -> list[str]:
        current_val = self._get()
        lines: list[str] = []
        for i in range(self.VIEW_SIZE):
            idx = i + self._view_start
            if idx < len(self._items):
                item = self._items[idx]
                marker = "   " if item == "back" else ("(*)" if item == current_val else "   ")
                prefix = ">" if idx == self._current_index else " "
                line = f"{prefix}{item} {marker}"
                lines.append(line[:20].ljust(20))
            else:
                lines.append(" " * 20)
        return lines


# ---------------------------------------------------------------------------
# PyGameMenu
# ---------------------------------------------------------------------------


class PyGameMenu(MenuBase):
    """Hands control of the rotary encoder to PygameApp.

    Queue ownership:
      encoder_q — LCDGui writes rotary deltas; PygameApp reads.  (unchanged)
      pygame_q  — PygameApp writes results; LCDGui reads.        (unchanged)

    On rotate: forwards delta to encoder_q so PygameApp receives it.
    On click:  emergency exit — pops this menu (PygameApp keeps running).
    Graceful exit: PygameApp calls signal_done(result), which puts
      ("done", result) on pygame_q; LCDGui calls on_exit_callback then pops.
    """

    def __init__(
        self,
        title: str,
        encoder_q: queue.Queue,
        on_exit_callback: Callable[[dict], None] | None = None,
    ):
        self.title = title
        self._encoder_q = encoder_q
        self.on_exit_callback = on_exit_callback

    def on_rotate(self, delta: int) -> None:
        self._encoder_q.put(delta)

    def on_click(self) -> None:
        # Emergency exit: pop without stopping PygameApp.
        if self._gui:
            self._gui.pop()

    def render(self) -> list[str]:
        header = f"-- {self.title} --"[:20].center(20)
        return [
            header,
            "Pygame active".center(20),
            " " * 20,
            "Click to exit".center(20),
        ]


# ---------------------------------------------------------------------------
# PrintStatusMenu
# ---------------------------------------------------------------------------


class PrintStatusMenu(MenuBase):
    """Displayed while a print job is running. Click stops the job."""

    title = "Printing..."

    def __init__(self, pc: PrintController, video_filename_short: str):
        self._pc = pc
        self._filename = video_filename_short[:20]
        self._start_time: float = 0.0

    def on_enter(self, gui: "LCDGui") -> None:
        super().on_enter(gui)
        self._start_time = time.time()

    def on_rotate(self, delta: int) -> None:
        pass  # no-op while printing

    def on_click(self) -> None:
        self._pc.stop()
        if self._gui:
            self._gui.pop()

    def render(self) -> list[str]:
        elapsed = time.time() - self._start_time
        mins, secs = divmod(int(elapsed), 60)
        return [
            "-- Printing --".center(20),
            self._filename.ljust(20),
            f"Elapsed: {mins:02d}:{secs:02d}".ljust(20),
            "Click to stop".center(20),
        ]


# ---------------------------------------------------------------------------
# StaticMenu
# ---------------------------------------------------------------------------


class StaticMenu(MenuBase):
    """Read-only display of fixed lines. Rotate does nothing; click pops."""

    def __init__(self, title: str, lines: list[str]):
        self.title = title
        self._lines = lines

    def on_rotate(self, delta: int) -> None:
        pass

    def on_click(self) -> None:
        if self._gui:
            self._gui.pop()

    def render(self) -> list[str]:
        result = list(self._lines[:4])
        while len(result) < 4:
            result.append("")
        return [ln[:20].ljust(20) for ln in result]


# ---------------------------------------------------------------------------
# LCDGui
# ---------------------------------------------------------------------------


class LCDGui:
    """Thin dispatcher: owns the menu stack and wires hardware inputs to menus.

    Construct with a PrintController and optional queues/event, then call
    set_root(menu) before run().
    """

    def __init__(
        self,
        pc: PrintController,
        encoder_q: queue.Queue | None = None,
        pygame_q: queue.Queue | None = None,
        stop_event: threading.Event | None = None,
        fps: int = 20,
    ):
        self.pc = pc
        self.encoder_q = encoder_q
        self.pygame_q = pygame_q
        self.stop_event = stop_event
        self.running = True
        self.mode = Mode.MENU
        self.stack: list[MenuBase] = []
        self._last_rendered: list[str] = []
        self.fps = fps

    # ── Stack management ──────────────────────────────────────────────────────

    def push(self, menu: MenuBase) -> None:
        """Enter and push a menu onto the stack."""
        menu.on_enter(self)
        self.stack.append(menu)
        self._sync_mode()

    def pop(self) -> None:
        """Exit and remove the top menu; never empties the stack entirely."""
        if len(self.stack) > 1:
            self.stack[-1].on_exit()
            self.stack.pop()
        self._sync_mode()

    def _sync_mode(self) -> None:
        top = self.stack[-1] if self.stack else None
        if isinstance(top, PyGameMenu):
            self.mode = Mode.PYGAME
        elif isinstance(top, PrintStatusMenu):
            self.mode = Mode.PRINTING
        else:
            self.mode = Mode.MENU

    def set_root(self, root: MenuBase) -> None:
        """Push the root menu, initializing the stack."""
        self.push(root)

    # ── Hardware input handlers ───────────────────────────────────────────────

    def handle_rotary_rotation(self, delta: int) -> None:
        if self.stack:
            self.stack[-1].on_rotate(delta)

    def handle_button_press(self) -> None:
        if self.stack:
            self.stack[-1].on_click()

    # ── Utility methods (called from menu callbacks) ──────────────────────────

    def save_defaults(self) -> None:
        """Persist current RPM, print size, and camera type to config.json."""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
        else:
            cfg = {}

        cfg["stepper_motor"]["default_speed"] = self.pc.hardware.stepper.speed_rpm
        cfg["projector"]["default_print_size"] = self.pc.hardware.projector.size
        cfg["camera"]["type"] = self.pc.hardware.camera.cam_type

        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            print(f"Error saving defaults: {e}")
            return

        self.splash("Defaults saved!", 1.2)

    def splash(self, message: str, duration: float = 1.0) -> None:
        """Briefly show a centered message on the LCD, then force a redraw."""
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message(message.center(20), 1, 0)
        time.sleep(duration)
        self._last_rendered = []  # force full redraw on next loop tick

    def restart_pi(self) -> None:
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message("Restarting...", 1, 0)
        time.sleep(2)
        subprocess.run(["sudo", "reboot"])

    def power_off_pi(self) -> None:
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message("Powering Off...", 1, 0)
        time.sleep(2)
        self.kill_gui()
        subprocess.call(["sudo", "shutdown", "-h", "now"])

    def kill_gui(self) -> None:
        self.running = False
        if self.stop_event is not None:
            self.stop_event.set()

    # ── Startup display ───────────────────────────────────────────────────────

    def show_startup_screen(self) -> None:
        from threading import Thread

        Thread(target=self.pc.hardware.led_manager.run_start_animation).start()
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message("Open   ".center(20), 1, 0)
        time.sleep(1)
        self.pc.hardware.lcd.write_message("OpenCAL".center(20), 1, 0)
        time.sleep(2)
        self.pc.hardware.lcd.write_message("FOR THE COMMUNITY".center(20), 2, 0)
        time.sleep(1)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the GUI loop. Must call set_root() before run()."""
        self.show_startup_screen()

        encoder = self.pc.hardware.rotary.encoder
        encoder.when_rotated_clockwise = lambda: self.handle_rotary_rotation(1)
        encoder.when_rotated_counter_clockwise = lambda: self.handle_rotary_rotation(-1)
        self.pc.hardware.rotary.button.when_pressed = self.handle_button_press

        while self.running:
            # Check for signals from pygame (only meaningful in PYGAME mode).
            if self.pygame_q is not None and self.mode == Mode.PYGAME:
                while not self.pygame_q.empty():
                    try:
                        key, value = self.pygame_q.get_nowait()
                        if key == "done" and self.stack:
                            top = self.stack[-1]
                            if isinstance(top, PyGameMenu) and top.on_exit_callback:
                                result = value if isinstance(value, dict) else {}
                                top.on_exit_callback(result)
                            self.pop()
                    except queue.Empty:
                        break

            # Re-render only when the display content changes.
            if self.stack:
                lines = self.stack[-1].render()
                if lines != self._last_rendered:
                    for i, line in enumerate(lines[:4]):
                        self.pc.hardware.lcd.write_message(line, i, 0)
                    self._last_rendered = list(lines)

            time.sleep(1 / self.fps)

        # Goodbye sequence
        time.sleep(0.5)
        self.pc.hardware.lcd.clear()
        time.sleep(0.5)
        self.pc.hardware.lcd.write_message("Goodbye!".center(20), 1, 0)
        time.sleep(2)
        self.pc.hardware.lcd.clear()


if __name__ == "__main__":
    # Standalone test entry point (no queues).
    _pc = PrintController()
    _gui = LCDGui(pc=_pc)
    _gui.run()
