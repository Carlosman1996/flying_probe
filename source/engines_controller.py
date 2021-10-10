import time
import random
from datetime import datetime
import serial
from source import logger
from source.utils import FileOperations


random.seed(str(datetime.now()))


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class SerialPortController:
    RESPONSE_TIMEOUT = 20
    INITIALIZATION_DELAY_TIME = 2
    RESPONSE_DELAY_TIME = 0

    def __init__(self, logger_level="INFO"):
        self.device_active = False
        self.session = None

        # Set logger:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level=logger_level)

    def exception_handler(self, exception):
        message = f"SERIAL ERROR - An error has occurred!\nError information: {str(exception)}"
        self.logger.set_message(level="CRITICAL", message_level="MESSAGE", message=message)
        raise Exception(message)

    def create_connection(self, serial_port, baud_rate, devices_active=False):
        # Set devices state parameter:
        self.device_active = devices_active

        # If the device is set to active, initialize session:
        if self.device_active:
            # Create serial port connection (session).
            try:
                self.session = serial.Serial(port=serial_port, baudrate=baud_rate)
            except Exception as exception:
                self.exception_handler(exception)

        time.sleep(self.INITIALIZATION_DELAY_TIME)
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message="Connection established")

    def read_response(self):
        response = ""
        elapsed_time = 0
        while self.session.inWaiting() > 0 and elapsed_time < self.RESPONSE_TIMEOUT:
            response += self.session.readline().decode("Ascii")
            elapsed_time += 1
        return response

    def send_command(self, command):
        response = None
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message=f"Send command: {command}")

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
            response = "ok"

        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message=f"Response: {response}")
        return response

    def close_connection(self):
        # If the device is set to active, close VISA interface:
        if self.device_active:
            self.session.close()
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message="Connection closed")

    @staticmethod
    def check_command_response(func):
        """ Decorator that controls the MARLIN responses. """
        def check_command_response_wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            # TODO: review response
            if "ok" not in response:
                raise Exception("ENGINES CONTROLLER ERROR\n"
                                "Error information: Response must contain two 'OK' in different lines. The string read"
                                f"is: {response}")
        return check_command_response_wrapper


class XYAxisEngines:
    def __init__(self, serial_port_ctrl):
        # General attributes:
        self.serial_port_ctrl = serial_port_ctrl

    @SerialPortController.check_command_response
    def move(self, probe, x_move=0, y_move=0, speed=0):
        # response = self.serial_port_ctrl.send_command(f"G{probe}0 Y{movement} F{speed}")
        self.serial_port_ctrl.send_command(f"G91")
        if x_move == 0:
            response = self.serial_port_ctrl.send_command(f"G0 Y{y_move} F{speed}")
        elif y_move == 0:
            response = self.serial_port_ctrl.send_command(f"G0 X{x_move} F{speed}")
        else:
            response = self.serial_port_ctrl.send_command(f"G0 X{x_move} Y{y_move} F{speed}")
        self.serial_port_ctrl.send_command(f"G90")
        return response

    @SerialPortController.check_command_response
    def homing(self, probe):
        response = self.serial_port_ctrl.send_command(f"G28")
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
        # response = self.serial_port_ctrl.send_command(f"M{probe}4")
        response = self.serial_port_ctrl.send_command("M4")
        return response

    @SerialPortController.check_command_response
    def high_level(self, probe):
        # response = self.serial_port_ctrl.send_command(f"M{probe}5")
        response = self.serial_port_ctrl.send_command("M5")
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
    def __init__(self):
        # General attributes:
        self.xy_axis_ctrl = None
        self.z_axis_ctrl = None

        # Initialize serial port controller:
        self.serial_port_ctrl = SerialPortController()

    def initialize(self, configuration):
        # Create connection:
        self.serial_port_ctrl.create_connection(serial_port=configuration["serial_port"],
                                                baud_rate=configuration["baud_rate"],
                                                devices_active=configuration["active"])

        # Initialize X axis engine controller:
        self.xy_axis_ctrl = XYAxisEngines(self.serial_port_ctrl)

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
    engines_ctrl = EnginesController()
    engines_ctrl.initialize(configuration=conf)

    engines_ctrl.xy_axis_ctrl.move("", 0, 0, 1)

    engines_ctrl.stop()
