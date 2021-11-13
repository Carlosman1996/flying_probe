import time
import random
import math
from datetime import datetime
import serial
import re
from source import logger
from source.utils import FileOperations


random.seed(str(datetime.now()))


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class SerialPortController:
    LOOP_ITERATIONS = 50
    INITIALIZATION_DELAY_TIME = 2
    RESPONSE_DELAY_TIME = 0.5
    MOVEMENT_CHECK_ITERATION_TIME = 0.5

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
        iteration_index = 0
        while self.session.inWaiting() > 0 and iteration_index < self.LOOP_ITERATIONS:
            response += self.session.readline().decode("Ascii")

            time.sleep(self.RESPONSE_DELAY_TIME)
            iteration_index += 1

        # Raise exception if probe is not in expected position:
        if iteration_index == self.LOOP_ITERATIONS:
            raise Exception(f"Response could not be read.")
        return response

    def wait_movement(self, position):
        def position_reached(current_position, expected_position):
            differences = [abs(current_point - expected_point)
                           for current_point, expected_point in zip(current_position, expected_position)]

            # Check all errors:
            for difference in differences:
                if difference > 0.1:
                    return False
            return True

        # TODO: M114 is not working, it is received before finishing the movement
        position_command = "M114"
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message=f"Wait until position {position} has "
                                                                                f"been reached")

        iteration_index = 0
        while iteration_index < self.LOOP_ITERATIONS:
            if self.device_active:
                response = self.send_command(position_command)
            else:
                response = str(position)

            response_filtered = re.findall(r"[-+]?\d*\.\d+|\d+", response)
            if response_filtered:
                response_coordinates = [float(number) for number in response_filtered][0:3]
                if position_reached(current_position=response_coordinates, expected_position=position):
                    break

            time.sleep(self.MOVEMENT_CHECK_ITERATION_TIME)
            iteration_index += 1

        # Raise exception if probe is not in expected position:
        if iteration_index == self.LOOP_ITERATIONS:
            raise Exception(f"Position {position} has not been reached.")

    def send_command(self, command):
        response = None
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message=f"Send command: {command}")

        # If the device is set to active, write and read command:
        if self.device_active:
            try:
                # Write command and wait:
                self.session.write(str.encode(command + "\r\n"))

                # Wait until read response:
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
            if "ERROR" in response:
                raise Exception("ENGINES CONTROLLER ERROR\n"
                                "Error information: Response must contain two 'OK' in different lines. The string read"
                                f"is: {response}")
        return check_command_response_wrapper


class XYAxisEngines:
    def __init__(self, serial_port_ctrl):
        # General attributes:
        self.serial_port_ctrl = serial_port_ctrl

        # Current position
        self.current_position = {
            'x': 0,
            'y': 0
        }

    @SerialPortController.check_command_response
    def move(self, probe, x_position=0, y_position=0, speed=0):
        response = self.serial_port_ctrl.send_command(f"G0 X{x_position} Y{y_position} F{speed}")

        # TODO: study GCODES and MARLIN configuration to set a response after move engines
        self.serial_port_ctrl.wait_movement(position=[x_position, y_position, 0])

        # Update probe position:
        self.current_position = {
            'x': x_position,
            'y': y_position
        }
        return response

    @SerialPortController.check_command_response
    def homing(self, probe):
        response = self.serial_port_ctrl.send_command(f"G28")
        # TODO: study GCODES and MARLIN configuration to set a response after move engines
        self.serial_port_ctrl.wait_movement(position=[0, 0, 0])
        return response


class ZAxisEngine:
    ACTION_HARDCODED_TIME = 5

    def __init__(self, serial_port_ctrl, logger_level="INFO"):
        # General attributes:
        self.serial_port_ctrl = serial_port_ctrl

        # Define commands time constants:
        self.measurement_command_time = 0.6
        self.calibration_command_time = 1
        self.homing_command_time = 1.5

        # Set logger:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level=logger_level)

    @SerialPortController.check_command_response
    def low_level(self, probe):
        # response = self.serial_port_ctrl.send_command(f"M{probe}4")
        response = self.serial_port_ctrl.send_command("M4")
        # TODO: study GCODES and MARLIN configuration to set a response after move engines
        # TODO: UNKNOWN STATE - PENDING STUDY
        # TODO: add wait movement
        # self.serial_port_ctrl.wait_movement(position=[0, 0, 0])
        return response

    @SerialPortController.check_command_response
    def high_level(self, probe):
        # response = self.serial_port_ctrl.send_command(f"M{probe}5")
        response = self.serial_port_ctrl.send_command("M5")
        # TODO: study GCODES and MARLIN configuration to set a response after move engines
        # TODO: UNKNOWN STATE - PENDING STUDY
        # TODO: add wait movement
        # self.serial_port_ctrl.wait_movement(position=[0, 0, 0])
        return response

    def calibration(self, probe):
        self.logger.set_message(level="INFO", message_level="MESSAGE", message=f"Z axis calibration")

        self.low_level(probe)
        time.sleep(self.calibration_command_time)
        self.high_level(probe)
        # TODO: read times correctly - avoid software continue while engine is moving
        time.sleep(self.ACTION_HARDCODED_TIME)

    def measure(self, probe):
        self.logger.set_message(level="INFO", message_level="MESSAGE", message=f"Z axis measure")

        self.low_level(probe)
        time.sleep(self.measurement_command_time)
        self.high_level(probe)
        # TODO: read times correctly - avoid software continue while engine is moving
        time.sleep(self.ACTION_HARDCODED_TIME)

    def homing(self, probe):
        self.logger.set_message(level="INFO", message_level="MESSAGE", message=f"Z axis homing")

        self.low_level(probe)
        time.sleep(self.homing_command_time)
        self.high_level(probe)
        # TODO: read times correctly - avoid software continue while engine is moving
        time.sleep(self.ACTION_HARDCODED_TIME)


class EnginesController:
    def __init__(self, logger_level="INFO"):
        # General attributes:
        self.xy_axis_ctrl = None
        self.z_axis_ctrl = None

        # Initialize serial port controller:
        self.serial_port_ctrl = SerialPortController(logger_level=logger_level)

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
        "serial_port": "COM7",
        "baud_rate": 250000,
        "active": True
    }
    engines_ctrl = EnginesController(logger_level="INFO")
    engines_ctrl.initialize(configuration=conf)

    # engines_ctrl.xy_axis_ctrl.homing("")
    # engines_ctrl.xy_axis_ctrl.move("", 10, 100, 10000)
    # engines_ctrl.z_axis_ctrl.homing("")
    # engines_ctrl.z_axis_ctrl.low_level("")

    # Start calibration
    time.sleep(2)
    engines_ctrl.z_axis_ctrl.homing("")
    time.sleep(2)
    engines_ctrl.z_axis_ctrl.calibration("")
    # Move probe to init
    engines_ctrl.z_axis_ctrl.homing("")
    time.sleep(2)

    # Measure:
    time.sleep(3)
    time.sleep(1)
    engines_ctrl.z_axis_ctrl.measure("")    # Down
    time.sleep(2)
    engines_ctrl.z_axis_ctrl.measure("")    # Up

    # Measure:
    time.sleep(3)
    time.sleep(2)
    engines_ctrl.z_axis_ctrl.measure("")    # Down
    time.sleep(1)
    engines_ctrl.z_axis_ctrl.measure("")    # Up

    engines_ctrl.stop()
