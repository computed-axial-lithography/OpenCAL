import queue
import signal
import threading
import os

from opencal.hardware import PrintController
from opencal.gui.lcd_gui import LCDGui
from opencal.gui.menus import build_menu_tree
from opencal.gui.pygame_app import PygameApp
from opencal.utils.config import load_config


def main():
    os.environ["DISPLAY"] = ":0"

    input_q: queue.Queue = queue.Queue()
    pygame_q: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    video_playing = threading.Event()

    conf = load_config()
    pc = PrintController(conf, video_playing=video_playing)
    gui = LCDGui(pc=pc, input_q=input_q, pygame_q=pygame_q, stop_event=stop_event)
    root = build_menu_tree(pc, gui)
    gui.set_root(root)

    def _shutdown(*_):
        gui.kill_gui()

    signal.signal(signal.SIGTERM, _shutdown)

    # Non-daemon so the goodbye sequence can complete before the process exits
    gui_thread = threading.Thread(target=gui.run, daemon=False)
    gui_thread.start()

    pygame_app = PygameApp(
        config=conf.pygame, input_q=input_q, pygame_q=pygame_q, stop_event=stop_event, fps=30,
        video_playing=video_playing,
    )
    try:
        pygame_app.run()
    except KeyboardInterrupt:
        pass
    finally:
        gui.kill_gui()

    # Wait for the goodbye sequence to finish (LCD clear + "Goodbye!" message)
    gui_thread.join(timeout=5)


if __name__ == "__main__":
    main()
