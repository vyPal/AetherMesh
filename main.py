import time
import machine

def main():
    pin = machine.Pin(8, machine.Pin.OUT)

    while True:
        pin.on()
        time.sleep(1)
        pin.off()
        time.sleep(1)

if __name__ == '__main__':
    main()