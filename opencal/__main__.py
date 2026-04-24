import queue
import threading
import os

from opencal.hardware import PrintController
from opencal.gui.lcd_gui import LCDGui
from opencal.gui.menus import build_menu_tree
from opencal.gui.pygame_app import PygameApp


def main():
    os.environ["DISPLAY"] = ":0"

    encoder_q: queue.Queue = queue.Queue()
    pygame_q: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    pc = PrintController()
    gui = LCDGui(pc=pc, encoder_q=encoder_q, pygame_q=pygame_q, stop_event=stop_event)
    root = build_menu_tree(pc, gui)
    gui.set_root(root)

    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    pygame_app = PygameApp(encoder_q=encoder_q, pygame_q=pygame_q, stop_event=stop_event, fps=30)
    pygame_app.run()


if __name__ == "__main__":
    main()
