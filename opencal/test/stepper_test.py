import time
from ticlib import TicUSB


def main():
    tic = TicUSB()

    tic.energize()
    tic.exit_safe_start()
    tic.reset_command_timeout()

    print("Starting test - rotating 200 steps CW")
    target = tic.get_current_position() + 200
    tic.set_target_position(target)

    while tic.get_current_position() != target:
        tic.reset_command_timeout()
        time.sleep(0.05)

    tic.deenergize()
    print("Test complete")


if __name__ == "__main__":
    main()
