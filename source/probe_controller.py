__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class ProbeController:
    def __init__(self, port=5188, device_active=True):
        # Oscilloscope attributes:
        self.address = f"TCPIP0::127.0.0.1::{port}::SOCKET"