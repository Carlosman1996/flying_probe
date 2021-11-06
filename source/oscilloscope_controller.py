import time
import random
from datetime import datetime
import pyvisa as visa
from source import logger
from source.utils import FileOperations


random.seed(str(datetime.now()))


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class VISAController:
    RESPONSE_DELAY_TIME = 0.25

    def __init__(self, logger_level="INFO"):
        self.device_active = False
        self.resource_manager = None
        self.session = None

        # Set logger:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level=logger_level)

    def exception_handler(self, exception):
        message = "VISA ERROR - An error has occurred!\nError information:\n"\
                  f"\tAbbreviation: {exception.abbreviation}\n"\
                  f"\tError code: {exception.error_code}\n"\
                  f"\tDescription: {exception.description}"
        self.logger.set_message(level="CRITICAL", message_level="MESSAGE", message=message)
        raise Exception(message)

    def create_connection(self, address, device_active=False):
        # Set devices state:
        self.device_active = device_active

        # If the device is set to active, initialize VISA interface:
        if self.device_active:
            # Create a connection (session) to the TCP/IP socket on the instrument.
            self.resource_manager = visa.ResourceManager()
            try:
                self.session = self.resource_manager.open_resource(address)
            except visa.VisaIOError as exception:
                self.exception_handler(exception)

            # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
            if self.session.resource_name.startswith('ASRL') or self.session.resource_name.endswith('SOCKET'):
                self.session.read_termination = '\n'

            # Set response timeout:
            self.session.timeout = 10

        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message="Connection established")

    def send_command(self, scpi_command):
        response = None
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message=f"Send command: {scpi_command}")

        # If the device is set to active, write and read command:
        if self.device_active:
            try:
                self.session.write(scpi_command)
                response = self.session.read()
            except visa.VisaIOError as exception:
                self.exception_handler(exception)

            # Set response delay time:
            time.sleep(self.RESPONSE_DELAY_TIME)
        # If the device is in test mode, generate a float random number:
        else:
            response = random.uniform(0, 1000000)

        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message=f"Response: {response}")
        return response

    def close_connection(self):
        # If the device is set to active, close VISA interface:
        if self.device_active:
            self.session.close()
            self.resource_manager.close()
        self.logger.set_message(level="DEBUG", message_level="MESSAGE", message="Connection closed")


class OscilloscopeController(VISAController):
    """Methods implemented for the oscilloscope OWON VDS1022"""

    def __init__(self):
        # Oscilloscope attributes:
        self.address = None
        self.pixels_per_div = 25
        self.vertical_divisions = 5
        self.horizontal_divisions = 20
        self.channels = [1, 2]
        self.timebase_values = {0.000000005: "5ns", 0.00000001: "10ns", 0.00000002: "20ns", 0.00000005: "50ns",
                                0.0000001: "100ns", 0.0000002: "200ns", 0.0000005: "500ns", 0.000001: "1us",
                                0.000002: "2us", 0.000005: "5us", 0.00001: "10us", 0.00002: "20us", 0.00005: "50us",
                                0.0001: "100us", 0.0002: "200us", 0.0005: "500us", 0.001: "1ms", 0.002: "2ms",
                                0.005: "5ms", 0.01: "10ms", 0.02: "20ms", 0.05: "50ms", 0.1: "100ms", 0.2: "200ms",
                                0.5: "500ms", 1: "1s", 2: "2s", 5: "5s", 10: "10s", 20: "20s", 50: "50s", 100: "100s"}
        self.channel_values = {0.005: "5mv", 0.01: "10mv", 0.02: "20mv", 0.05: "50mv", 0.1: "100mv", 0.2: "200mv",
                               0.5: "500mv", 1: "1v", 2: "2v", 5: "5v"}

        # Run method configuration parameters:
        self.relation_horizontal_signal = 5
        self.relation_signal_vertical = 2
        self.relation_acq_time_horizontal = 5

        # VISA controller:
        super().__init__()

    def convert_pixels_to_value(self, vertical_scale, offset_per_div, pixels):
        try:
            return vertical_scale * ((pixels - offset_per_div * self.pixels_per_div) / self.pixels_per_div)
        except ZeroDivisionError:
            return 0

    def convert_value_to_pixels(self, vertical_scale, offset_per_div, value):
        try:
            return int(self.pixels_per_div * (value / vertical_scale) + offset_per_div * self.pixels_per_div)
        except ZeroDivisionError:
            return 0

    @staticmethod
    def get_closest_value_with_key_dictionary(dictionary, search_key):
        return dictionary.get(search_key) or dictionary[min(dictionary.keys(), key=lambda key: abs(key - search_key))]

    @staticmethod
    def get_closest_key_dictionary(dictionary, search_key):
        return min(dictionary.keys(), key=lambda key: abs(key - search_key))

    @staticmethod
    def get_key_from_value_dictionary(dictionary, search_value):
        for key, value in dictionary.items():
            if value == search_value:
                return key
        return None

    def get_id(self):
        self.send_command("*IDN?")

    def set_restore(self):
        self.send_command("*RST")

    def set_general_state(self, state):
        """
        Possible general states:
            {RUN | STOP}
        """
        current_state = self.send_command("*RUNSTOP?")
        if (current_state == "RUN" and state == "STOP") or (current_state == "STOP" and state == "RUN"):
            self.send_command("*RUNSTOP")

    def set_timebase(self, scale):
        """
        Scale possible values:
            {5ns | 10ns | 20ns | 50ns | 100ns | 200ns | 500ns | 1us | 2us | 5us | 10us | 20us | 50us |
             100us | 200us | 500us | 1ms | 2ms | 5ms | 10ms | 20ms | 50ms | 100ms | 200ms | 500ms |
             1s | 2s | 5s | 10s | 20s | 50s | 100s}
        """
        self.send_command(f":TIMEBASE:SCALE {scale}")
        self.send_command(":TIMEBASE:HOFFSET 0")

    def set_channel_state(self, channel, state):
        """
        Channel possible states:
            {ON | OFF}
        """
        self.send_command(f":CHANNEL{channel}:DISPLAY {state}")  # ON, OFF

    def set_probe_configuration(self, channel, coupling="DC", probe="X1"):
        """
        Channel possible couplings:
            {AC | DC | GND}
        Channel possible probe attenuation ratios:
            {X1 | X10 | X100 | X1000}
        """
        self.send_command(f":CHANNEL{channel}:COUPLING {coupling}")
        self.send_command(f":CHANNEL{channel}:PROBE {probe}")

    def set_channel_configuration(self, channel, scale, offset):
        """
        Channel possible scales (float values, not string type: eg: 0.005 instead of 5mV):
            {5mV | 10mV | 20mV | 50mV | 100mV | 200mV | 500mV | 1V | 2V | 5V}
        """
        self.send_command(f":CHANNEL{channel}:SCALE {scale}")
        self.send_command(f":CHANNEL{channel}:OFFSET {self.convert_value_to_pixels(scale, 0, offset)}")

    def set_configure_edge_trigger(self, channel, mode="AUTO", slope="RISE"):
        """
        Trigger possible modes:
            {AUTO | NORMAL}
        Trigger possible slopes:
            {RISE | FALL}
        """
        self.send_command(f":TRIGGER:MODE {mode}")
        self.send_command(":TRIGGER:SINGLE EDGE")
        self.send_command(f":TRIGGER:SINGLE:EDGE:SOURCE CH{str(channel)}")
        self.send_command(f":TRIGGER:SINGLE:EDGE:SLOPE {slope}")

    def set_trigger_level(self, channel, level=0.0):
        vertical_scale = float(self.send_command(f":CHANNEL{channel}:SCALE?"))
        self.send_command(f":TRIGGER:SINGLE:EDGE:LEVEL {self.convert_value_to_pixels(vertical_scale, 0, level)}")

    def set_acquire(self, acq_type="AVERAGE", count=4):
        """
        Acquire possible modes:
            {SAMPLE | AVERAGE | PEAK}
        Acquire average values range:
            {1 ~ 128}
        Acquire possible values memory depth:
            {1K | 10K | 100K | 1M | 5M or 10M}
        """
        self.send_command(f":ACQUIRE:TYPE {acq_type}")
        if type == "AVERAGE":
            self.send_command(f":ACQUIRE:AVERAGE {count}")

    def set_measurement(self, channel, measurement):
        """
        Measurement possible modes:
            {PERiod | FREQuency | AVERage | MAX | MIN | VTOP | VBASe | VAMP | PKPK | CYCRms | RTime |
             FTime | PDUTy | NDUTy | PWIDth | NWIDth | OVERshoot | PREShoot | RDELay | FDELay}
        """
        self.send_command(f":MEASURE:SOURCE CH{channel}")
        self.send_command(f":MEASURE:ADD {measurement}")

    def remove_measurement(self, channel, measurement="ALL"):
        """
        Measurement possible modes:
            {PERiod | FREQuency | AVERage | MAX | MIN | VTOP | VBASe | VAMP | PKPK | CYCRms | RTime |
             FTime | PDUTy | NDUTy | PWIDth | NWIDth | OVERshoot | PREShoot | RDELay | FDELay | ALL}
        """
        self.send_command(f":MEASURE:SOURCE CH{channel}")
        self.send_command(f":MEASURE:DELETE {measurement}")

    def get_measurement(self, channel, measurement):
        """
        Measurement possible modes:
            {PERiod | FREQuency | AVERage | MAX | MIN | VTOP | VBASe | VAMP | PKPK | CYCRms | RTime |
             FTime | PDUTy | NDUTy | PWIDth | NWIDth | OVERshoot | PREShoot | RDELay | FDELay}
        """
        string_value = self.send_command(f":MEASURE{channel}:{measurement}?")
        if string_value == '?':
            return None
        else:
            return float(string_value)

    def get_waveform(self, channel):
        return self.send_command(f"*ADC? CH{channel}")  # TODO: This method does not work: list of values is not read.

    def initialize(self, configuration):
        """ initialize(self) """
        # Create connection:
        address = f"TCPIP0::127.0.0.1::{configuration['port']}::SOCKET"
        self.create_connection(address=address,
                               device_active=configuration["active"])

        # Disable all channels:
        for channel in self.channels:
            self.set_channel_state(channel, "OFF")

        # Run device:
        self.set_general_state("RUN")

        # Configure acquire:
        self.set_acquire()

    def measure(self, inputs_dict):
        """ measure(self, dict) """
        # Check if channel is available:
        if inputs_dict["channel"] not in self.channels:
            raise Exception("Channel is not valid. Available channels are 1 and 2.")

        # Configure probe:
        self.set_probe_configuration(inputs_dict["channel"], inputs_dict["coupling"], inputs_dict["probe_attenuation"])

        # Set timebase:
        if inputs_dict["frequency"] == 0:
            timebase = 0.1  # Hardcoded
        else:
            timebase = self.relation_horizontal_signal * (1 / inputs_dict["frequency"]) / self.horizontal_divisions
        horizontal_scale = self.get_closest_value_with_key_dictionary(self.timebase_values, timebase)
        self.set_timebase(horizontal_scale)

        # Configure channel:
        vertical_amplitude = self.relation_signal_vertical * inputs_dict["signal_max_value"] / self.vertical_divisions
        vertical_scale = self.get_closest_key_dictionary(self.channel_values, vertical_amplitude)
        self.set_channel_configuration(inputs_dict["channel"], vertical_scale, 0)

        # Enable channel:
        self.set_channel_state(inputs_dict["channel"], "ON")

        # Configure trigger:
        self.set_configure_edge_trigger(inputs_dict["channel"], "AUTO", inputs_dict["trigger_edge_slope"])
        trigger_level = (inputs_dict["signal_max_value"] - inputs_dict["signal_min_value"]) / 2
        self.set_trigger_level(inputs_dict["channel"], trigger_level)

        # Minimum time to acquire the desired signal:
        time.sleep(timebase * self.relation_acq_time_horizontal)

        # Get measurements:
        measurements = {"channel": inputs_dict["channel"],
                        "measurements": {}}
        for measurement in inputs_dict["measurements"]:
            measurements["measurements"][measurement] = self.get_measurement(inputs_dict["channel"],
                                                                             measurement)

        # Disable channel:
        self.set_channel_state(inputs_dict["channel"], "OFF")
        return measurements

    def stop(self):
        """ stop(self) """
        # Stop device:
        self.set_general_state("STOP")


if __name__ == '__main__':
    conf = {
        "port": 5188,
        "active": False
    }
    osc_obj = OscilloscopeController()

    # Initialize oscilloscope:
    osc_obj.initialize(configuration=conf)

    # Perform measurement:
    measurement_inputs = {"channel": 1,
                          "trigger_edge_slope": "FALL",
                          "coupling": "DC",
                          "probe_attenuation": "X10",
                          "signal_max_value": 5,
                          "signal_min_value": 0,
                          "frequency": 10000000,
                          "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]}
    result = osc_obj.measure(measurement_inputs)
    print(result)

    # Stop oscilloscope:
    osc_obj.stop()

    osc_obj.close_connection()
