from source import logger
from source.utils import FileOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class ProbeController:
    def __init__(self, oscilloscope_ctrl, engines_ctrl):
        # General attributes:
        self.probe_name = None
        self.configuration = {}
        self.current_position = {'x': 0,
                                 'y': 0}

        # Set logger:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level="DEBUG")

        # Probe controller must inherit the oscilloscope and engines controller:
        self.engines_ctrl = engines_ctrl
        self.oscilloscope_ctrl = oscilloscope_ctrl

    def initialize(self, probe_name, configuration):
        self.probe_name = int(probe_name)
        self.configuration = configuration  # General configuration of the probe: speed, acceleration, ...

    def measure_test_point(self, trajectory, measurement_inputs, test_point_name=""):
        """ measure_test_point(self, list, dict)

        The trajectory is a list of coordinates, so the software must calculate the incremental values to move the
        engines.
        """
        self.logger.set_message(level="CRITICAL", message_level="SUBSECTION", message=test_point_name)

        # Move probe to test point following the trajectory:
        for coordinates in trajectory:
            # Move XY engines:
            self.engines_ctrl.xy_axis_ctrl.move(probe=self.probe_name,
                                                x_move=coordinates['x'] - self.current_position['x'],
                                                y_move=coordinates['y'] - self.current_position['y'],
                                                speed=self.configuration["speed"])

            # Update probe position:
            self.current_position = {'x': coordinates['x'],
                                     'y': coordinates['y']}

        # Measure test point:
        measurement_inputs["channel"] = self.probe_name
        result = self.oscilloscope_ctrl.measure(measurement_inputs)
        return result
