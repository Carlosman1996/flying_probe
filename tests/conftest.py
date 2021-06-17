import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../source')))
import visa_devices


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


@pytest.fixture
def vds1022_inactive():
    osc_obj = visa_devices.OwonVDS1022(port=5188, device_active=False)
    return osc_obj
