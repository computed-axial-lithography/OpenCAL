from serial import Serial
from opencal.hardware.stepper import create_stepper
from opencal.utils.config import load_config
import time


def crc8(data):

    crc = 0

    for byte in data:
        for _ in range(8):
            if (crc >> 7) ^ (byte & 1):
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
            byte >>= 1

    return crc


def send_and_recv(s, label, data: list[int]):
    frame = bytes(data)
    frame += bytes([crc8(frame)])
    s.write(frame)
    resp = s.read(12)
    print(f'{label}: {resp.hex()}')

def write_vactual(velocity):
    # Handle negative values (24-bit two's complement, sent in 32-bit field)
    if velocity < 0:
        velocity = (1 << 32) + velocity  # extend to 32-bit two's complement
    
    sync = 0x05
    slave_addr = 0x00
    reg = 0x22 | 0x80  # 0xA2 (write flag set)
    
    data_bytes = [
        (velocity >> 24) & 0xFF,
        (velocity >> 16) & 0xFF,
        (velocity >> 8)  & 0xFF,
        velocity & 0xFF
    ]
    
    frame = bytes([sync, slave_addr, reg] + data_bytes)
    frame += bytes([crc8(frame)])
    return frame



def main():

    conf = load_config()
    stepper = create_stepper(conf.stepper)
    stepper.enable.on()

    s = Serial("/dev/ttyAMA0", 115200, timeout=1)



    while True:
        velocity = input("Velocity: ")
        if velocity == 'debug':
            send_and_recv(s, "GCONF", [0x05, 0x00, 0x00])
            send_and_recv(s, "CHOPCONF", [0x05, 0x00, 0x6C])
            send_and_recv(s, "DRV_STATUS", [0x05, 0x00, 0x6F])
        else:
            frame = write_vactual(int(velocity))
            print(frame.hex())

            s.write(frame)
            s.read(8)

if __name__ == "__main__": main()


