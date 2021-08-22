import os
from pathlib import Path
import pytest

from source import engines_controller
from source import oscilloscope_controller
from source import probe_controller
from source import pcb_mapping
from source import checkpoints_selector
from source import inputs_controller


FILE_DIRECTORY = Path(os.path.dirname(os.path.abspath(__file__)))


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


@pytest.fixture
def pcb_pic_programmer_example_info():
    file_path = str(FILE_DIRECTORY.parent) + "//assets//PCB//pic_programmer//API_info//API_info_pcb.csv"

    pcb_obj = pcb_mapping.PCBMapping(file_path)
    info_df = pcb_obj.run()
    return info_df


@pytest.fixture
def test_points_selector_one_probe():
    probes_configuration = {"1": {"inclination": 0,  # degrees
                                  "diameter": 0.001}}
    test_points_selector_obj = checkpoints_selector.TestPointsSelector(probes_configuration=probes_configuration)
    return test_points_selector_obj


@pytest.fixture
def test_points_selector_two_probes():
    probes_configuration = {"1": {"inclination": 0,  # degrees
                                  "diameter": 0.001},
                            "2": {"inclination": 12,  # degrees
                                  "diameter": 0.001}}
    test_points_selector_obj = checkpoints_selector.TestPointsSelector(probes_configuration=probes_configuration)
    return test_points_selector_obj


@pytest.fixture
def inputs_controller_object():
    inputs_ctrl_obj = inputs_controller.InputsController()
    return inputs_ctrl_obj
