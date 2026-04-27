import queue
import threading
import os

from opencal.hardware import PrintController
from opencal.gui.lcd_gui import LCDGui
from opencal.gui.menus import build_menu_tree
from opencal.gui.pygame_app import PygameApp
from opencal.utils.config import load_config


def main():
    os.environ["DISPLAY"] = ":0"

    encoder_q: queue.Queue = queue.Queue()
    pygame_q: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    video_playing = threading.Event()

    conf = load_config()
    pc = PrintController(conf, video_playing=video_playing)
    gui = LCDGui(pc=pc, encoder_q=encoder_q, pygame_q=pygame_q, stop_event=stop_event)
    root = build_menu_tree(pc, gui)
    gui.set_root(root)

    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    pygame_app = PygameApp(
        config=conf.pygame, encoder_q=encoder_q, pygame_q=pygame_q, stop_event=stop_event, fps=30,
        video_playing=video_playing,
    )
    pygame_app.run()
    # Join on GUI thread, so that if PyGame is disabled GUI continues to run
    gui_thread.join()


if __name__ == "__main__":
    main()
