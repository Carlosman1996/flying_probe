import time
import random
from datetime import datetime
import serial


random.seed(str(datetime.now()))


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class SerialPortController:
    RESPONSE_TIMEOUT = 20
    INITIALIZATION_DELAY_TIME = 2
    RESPONSE_DELAY_TIME = 0

    def __init__(self, serial_port, baud_rate, device_active):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.device_active = device_active
        self.session = self.create_connection()

    @staticmethod
    def exception_handler(exception):
        raise Exception("SERIAL ERROR - An error has occurred!\n"
                        f"Error information: {str(exception)}")

    def create_connection(self):
        # If the device is set to active, initialize session:
        if self.device_active:
            # Create serial port connection (session).
            try:
                session = serial.Serial(port="COM6", baudrate=115200)
            except Exception as exception:
                self.exception_handler(exception)

        # If the device is in test mode, set the return parameters to None:
        else:
            session = None

        time.sleep(self.INITIALIZATION_DELAY_TIME)
        return session

    def read_response(self):
        response = ""
        elapsed_time = 0
        while self.session.inWaiting() > 0 and elapsed_time < self.RESPONSE_TIMEOUT:
            response += self.session.readline().decode("Ascii")
            elapsed_time += 1
        return response

    def send_command(self, command):
        response = None

        # If the device is set to active, write and read command:
        if self.device_active:
            try:
                # Write command and wait:
                self.session.write(str.encode(command + "\r\n"))
                time.sleep(self.RESPONSE_DELAY_TIME)
                # Read microcontroller response:
                response = self.read_response()
            except Exception as exception:
                self.exception_handler(exception)
        # If the device is in test mode, generate a float random number:
        else:
            response = command
        return response

    def close_connection(self):
        # If the device is set to active, close VISA interface:
        if self.device_active:
            self.session.close()


class Engine(SerialPortController):
    def __init__(self, serial_port, baud_rate, device_active=True):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.device_active = device_active

        # Serial port controller:
        super().__init__(self.serial_port, self.baud_rate, device_active)

    def move(self, movement, speed):
        # Send GCODE commands:
        print(f"G91Y{movement}F{speed}")
        response = self.send_command(f"G91Y{movement}F{speed}")
        print(response + "\n")

    def homing(self):
        # Send GCODE commands:
        print(f"G28")
        response = self.send_command(f"G28 X0 Y0 Z0")
        print(response + "\n")


if __name__ == '__main__':
    engine_obj = Engine(serial_port="COM6", baud_rate=115200, device_active=True)

    engine_obj.move(-50.0, 10000)
    engine_obj.move(50.0, 10000)
    engine_obj.move(-100.0, 10000)
    engine_obj.move(200.0, 10000)
    engine_obj.move(-100.0, 10000)

    engine_obj.close_connection()
