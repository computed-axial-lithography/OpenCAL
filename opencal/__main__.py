import threading

from opencal.gui import LCDGui


def main():

    # Pass print_controller to the GUI
    gui = LCDGui()

    # Start GUI in separate thread
    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()
    gui_thread.join()


if __name__ == "__main__":
    main()
