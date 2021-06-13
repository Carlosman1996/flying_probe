import pyvisa as visa


class VISAController:
    def __init__(self, visa_address):
        self.visa_address = visa_address
        self.resource_manager, self.session = self.create_connection()

    @staticmethod
    def exception_handler(exception):
        raise Exception("VISA ERROR - An error has occurred!\n"
                        "Error information:\n"
                        f"\tAbbreviation: {exception.abbreviation}\n"
                        f"\tError code: {exception.error_code}\n"
                        f"\tDescription: {exception.description}")

    def create_connection(self):
        # Create a connection (session) to the TCP/IP socket on the instrument.
        resource_manager = visa.ResourceManager()
        try:
            session = resource_manager.open_resource(self.visa_address)
        except visa.VisaIOError as exception:
            self.exception_handler(exception)

        # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
        if session.resource_name.startswith('ASRL') or session.resource_name.endswith('SOCKET'):
            session.read_termination = '\n'

        # Set huge timeout for ADC reading:
        session.timeout = 10000
        return resource_manager, session

    def send_command(self, scpi_command):
        try:
            self.session.write(scpi_command)
            response = self.session.read()
        except visa.VisaIOError as exception:
            self.exception_handler(exception)

        print(f"SCPI Command: {scpi_command} - Result: {response}\n")
        return response

    def close_connection(self):
        self.session.close()
        self.resource_manager.close()


class OwonVDS1022(VISAController):
    def __init__(self, port=5188):
        # Oscilloscope attributes:
        self.address = f"TCPIP0::127.0.0.1::{port}::SOCKET"
        self.pixels_per_div = 25

        # VISA controller:
        super().__init__(self.address)

    def convert_pixels_to_value(self, vertical_scale, offset_per_div, pixels):
        return vertical_scale * ((pixels - offset_per_div * self.pixels_per_div) / self.pixels_per_div)

    def convert_value_to_pixels(self, vertical_scale, offset_per_div, value):
        return self.pixels_per_div * (value / vertical_scale) + offset_per_div * self.pixels_per_div

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
        self.send_command(f":TIMEBASE:HOFFSET 0")

    def set_channel_state(self, channel, state):
        """
        Channel possible states:
            {ON | OFF}
        """
        self.send_command(f":CHANNEL{channel}:DISPLAY {state}")     # ON, OFF

    def set_channel_configuration(self, channel, scale, offset, coupling="DC", probe="X1"):
        """
        Channel possible couplings:
            {AC | DC | GND}
        Channel possible probe attenuation ratios:
            {X1 | X10 | X100 | X1000}
        Channel possible scales:
            {5mV | 10mV | 20mV | 50mV | 100mV | 200mV | 500mV | 1V | 2V | 5V}
        """
        self.send_command(f":CHANNEL{channel}:COUPING {coupling}")
        self.send_command(f":CHANNEL{channel}:PROBE {probe}")
        self.send_command(f":CHANNEL{channel}:SCALE {scale}")
        self.send_command(f":CHANNEL{channel}:OFFSET "
                          f"{self.convert_value_to_pixels(scale, 0, offset)}")

    def set_edge_trigger(self, channel, vertical_scale, offset_per_div, mode="NORMAL", slope="RISE", level=0.0):
        """
        Trigger possible modes:
            {AUTO | NORMAL}
        Trigger possible slopes:
            {RISE | FALL}
        """
        self.send_command(f":TRIGGER:MODE {mode}")
        self.send_command(f":TRIGGER:SINGLE EDGE")
        self.send_command(f":TRIGGER:SINGLE:EDGE:SOURCE CH{str(channel)}")
        self.send_command(f":TRIGGER:SINGLE:EDGE:SLOPE {slope}")  # RISE, FALL
        self.send_command(f":TRIGGER:SINGLE:EDGE:LEVEL "
                          f"{self.convert_value_to_pixels(vertical_scale, offset_per_div, level)}")

    def set_acquire(self, acq_type="SAMPLE", count=4, n_samples="1K"):
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
        self.send_command(f":TRIGGER:MDEPTH {n_samples}")

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
        self.send_command(f":MEASURE{channel}:{measurement}?")

    def get_waveform(self, channel):
        self.send_command(f"*ADC? CH{channel}")


if __name__ == '__main__':
    osc_obj = OwonVDS1022(port=5188)
    osc_obj.set_general_state("RUN")
    # osc_obj.set_edge_trigger(channel=1, vertical_scale=5, offset_per_div=1.64, level=2.5)
    osc_obj.get_waveform(1)
    osc_obj.close_connection()
