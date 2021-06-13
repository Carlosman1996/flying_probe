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


class OwonVDS1022:
    def __init__(self, port=5188):
        self.address = f"TCPIP0::127.0.0.1::{port}::SOCKET"
        self.pixels_per_div = 25
        self.configuration = {"CH1": {"vertical_scale": 5,
                                      "vertical_offset": 1.64}}

        self.visa_ctrl = VISAController(self.address)

    def convert_pixels_to_value(self, vertical_scale, vertical_offset, pixels):
        return vertical_scale * ((pixels - vertical_offset * self.pixels_per_div) / self.pixels_per_div)

    def convert_value_to_pixels(self, vertical_scale, vertical_offset, value):
        return self.pixels_per_div * (value / vertical_scale) + vertical_offset * self.pixels_per_div

    def set_edge_trigger(self, mode="NORMAL", channel=1, slope="RISE", level=0.0):
        vertical_scale = self.configuration[f"CH{str(channel)}"]["vertical_scale"]
        vertical_offset = self.configuration[f"CH{str(channel)}"]["vertical_offset"]

        self.visa_ctrl.send_command(f":TRIGGER:MODE {mode}")
        self.visa_ctrl.send_command(f":TRIGGER:SINGLE EDGE")
        self.visa_ctrl.send_command(f":TRIGGER:SINGLE:EDGE:SOURCE CH{str(channel)}")
        self.visa_ctrl.send_command(f":TRIGGER:SINGLE:EDGE:SLOPE {slope}")
        self.visa_ctrl.send_command(f":TRIGGER:SINGLE:EDGE:LEVEL "
                                    f"{self.convert_value_to_pixels(vertical_scale, vertical_offset, level)}")


if __name__ == '__main__':
    osc_obj = OwonVDS1022(port=5188)
    osc_obj.set_edge_trigger(level=2.5)
    osc_obj.visa_ctrl.close_connection()
