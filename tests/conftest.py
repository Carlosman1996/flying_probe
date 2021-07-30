import pytest

from source import engines_controller
from source import oscilloscope_controller


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


@pytest.fixture
def vds1022_inactive():
    osc_obj = oscilloscope_controller.OwonVDS1022(port=5188, device_active=False)
    return osc_obj


@pytest.fixture
def engine_inactive():
    engine_obj = engines_controller.YAxisEngine(serial_port="COM1", device_active=False)
    return engine_obj
