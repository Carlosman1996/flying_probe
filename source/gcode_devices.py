import serial
import time


TIMEOUT = 200


def wait(serial_port):
    elapsed_time = 0
    time.sleep(2)
    print(serial_port.inWaiting())
    while serial_port.inWaiting() > 0 and elapsed_time < TIMEOUT:
        print(serial_port.read())
        elapsed_time += 1


if __name__ == '__main__':
    serial_port = serial.Serial(port="COM5", baudrate=115200)

    print(serial_port)

    print("Code G91Y-5.0F10000")
    wait(serial_port)
    serial_port.write(str.encode("G91Y-10.0F10000\r\n"))

    print("Code G91Y5.0F10000")
    wait(serial_port)
    serial_port.write(str.encode("G91Y10.0F10000\r\n"))

    print("Code G91Y-5.0F10000")
    wait(serial_port)
    serial_port.write(str.encode("G91Y20.0F10000\r\n"))

    print("Code G91Y5.0F10000")
    wait(serial_port)
    serial_port.write(str.encode("G91Y-20.0F10000\r\n"))

    time.sleep(1)
    serial_port.close()