import threading

from opencal.gui import LCDGui
from opencal.hardware.hardware_controller import HardwareController
from opencal.print_controller import PrintController


def main():
    print_controller = PrintController()

    # Pass print_controller to the GUI
    gui = LCDGui(pc=print_controller)
    if not print_controller.hardware.lcd or not print_controller.hardware.rotary:
        print("GUI peripherals missing, not starting GUI")
        return

    # Start GUI in separate thread
    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    gui_thread.join()


if __name__ == "__main__":
    main()
