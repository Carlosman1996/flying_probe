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
        # If the device is in test mode, the session parameter will be None:
        session = None

        # If the device is set to active, initialize session:
        if self.device_active:
            # Create serial port connection (session).
            try:
                session = serial.Serial(port=self.serial_port, baudrate=self.baud_rate)
            except Exception as exception:
                self.exception_handler(exception)

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
            response = "OK\nOK\n\n"
        return response

    def close_connection(self):
        # If the device is set to active, close VISA interface:
        if self.device_active:
            self.session.close()

    @staticmethod
    def check_command_response(func):
        """ Decorator that controls the MARLIN responses. """
        def check_command_response_wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            if response != "OK\nOK\n\n":
                raise Exception("ENGINES CONTROLLER ERROR\n"
                                "Error information: Response must contain two 'OK' in different lines. The string read"
                                f"is: {response}")
        return check_command_response_wrapper


class XAxisEngine:
    def __init__(self, serial_port_ctrl):
        # General attributes:
        self.serial_port_ctrl = serial_port_ctrl

    @SerialPortController.check_command_response
    def move(self, probe, movement, speed):
        response = self.serial_port_ctrl.send_command(f"G{probe}91Y{movement}F{speed}")
        return response

    @SerialPortController.check_command_response
    def homing(self, probe):
        response = self.serial_port_ctrl.send_command(f"G{probe}28 X0 Y0 Z0")
        return response


class YAxisEngine:
    def __init__(self, serial_port_ctrl):
        # General attributes:
        self.serial_port_ctrl = serial_port_ctrl

    @SerialPortController.check_command_response
    def move(self, probe, movement, speed):
        response = self.serial_port_ctrl.send_command(f"{probe}")
        return response


class ZAxisEngine:
    def __init__(self, serial_port_ctrl):
        # General attributes:
        self.serial_port_ctrl = serial_port_ctrl

        # Define commands time constants:
        self.calibration_command_time = 0.25
        self.measurement_command_time = 0.75
        self.homing_command_time = 1.25

    @SerialPortController.check_command_response
    def low_level(self, probe):
        response = self.serial_port_ctrl.send_command(f"M{probe}4")
        return response

    @SerialPortController.check_command_response
    def high_level(self, probe):
        response = self.serial_port_ctrl.send_command(f"M{probe}5")
        return response

    def calibration(self, probe):
        self.low_level(probe)
        time.sleep(self.calibration_command_time)
        self.high_level(probe)

    def measure(self, probe):
        self.low_level(probe)
        time.sleep(self.measurement_command_time)
        self.high_level(probe)

    def homing(self, probe):
        self.low_level(probe)
        time.sleep(self.homing_command_time)
        self.high_level(probe)


class EnginesController:
    def __init__(self, engines_conf):
        # General attributes:
        self.serial_port = engines_conf["serial_port"]
        self.baud_rate = engines_conf["baud_rate"]
        self.devices_active = engines_conf["active"]
        self.x_axis_ctrl = None
        self.y_axis_ctrl = None
        self.z_axis_ctrl = None

        # Initialize serial port controller:
        self.serial_port_ctrl = SerialPortController(self.serial_port, self.baud_rate, engines_conf["active"])

    def initialize(self):
        # Initialize X axis engine controller:
        self.x_axis_ctrl = XAxisEngine(self.serial_port_ctrl)

        # Initialize Y axis engine controller:
        self.y_axis_ctrl = YAxisEngine(self.serial_port_ctrl)

        # Initialize Z axis engine controller:
        self.z_axis_ctrl = ZAxisEngine(self.serial_port_ctrl)

    def stop(self):
        # Close serial port controller:
        self.serial_port_ctrl.close_connection()


if __name__ == '__main__':
    conf = {
        "serial_port": "COM1",
        "baud_rate": 115200,
        "active": False
    }
    engines_ctrl = EnginesController(engines_conf=conf)
    engines_ctrl.initialize()

    engines_ctrl.y_axis_ctrl.move("", -50.0, 10000)
    engines_ctrl.y_axis_ctrl.move("", 50.0, 10000)
    engines_ctrl.y_axis_ctrl.move("", -100.0, 10000)
    engines_ctrl.y_axis_ctrl.move("", 200.0, 10000)
    engines_ctrl.y_axis_ctrl.move("", -100.0, 10000)

    engines_ctrl.stop()
