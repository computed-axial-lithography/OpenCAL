import threading

from opencal.hardware import PrintController
from opencal.gui import LCDGui


def main():
    print_controller = PrintController()

    # Pass print_controller to the GUI
    gui = LCDGui(pc=print_controller)
    if (
        print_controller.hardware.lcd is None
        or print_controller.hardware.rotary is None
    ):
        print("GUI peripherals missing, not starting GUI")
        return

    # Start GUI in separate thread
    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    gui_thread.join()


if __name__ == "__main__":
    main()
