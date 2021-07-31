import pytest

from source import engines_controller
from source import oscilloscope_controller
from source import probe_controller


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


@pytest.fixture
def oscilloscope_inactive():
    osc_obj = oscilloscope_controller.OscilloscopeController(port=5188, device_active=False)
    return osc_obj


@pytest.fixture
def engines_inactive():
    engines_ctrl = engines_controller.EnginesController(serial_port="COM6", baud_rate=115200, devices_active=False)
    engines_ctrl.initialize()
    return engines_ctrl


@pytest.fixture
def probe_inactive(oscilloscope_inactive, engines_inactive):
    configuration = {"probe": 1,
                     "speed": 10000}
    probe_obj = probe_controller.ProbeController(configuration=configuration,
                                                 oscilloscope_ctrl=oscilloscope_inactive,
                                                 engines_ctrl=engines_inactive)
    return probe_obj
