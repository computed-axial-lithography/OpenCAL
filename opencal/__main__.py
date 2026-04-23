import queue
import threading

from opencal.gui import LCDGui
from opencal.gui.pygame_app import PygameApp


def main():
    encoder_q: queue.Queue = queue.Queue()
    pygame_q: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    gui = LCDGui(encoder_q=encoder_q, pygame_q=pygame_q, stop_event=stop_event)
    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    pygame_app = PygameApp(encoder_q=encoder_q, pygame_q=pygame_q, stop_event=stop_event)
    pygame_app.run()


if __name__ == "__main__":
    main()
