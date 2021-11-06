from source import logger
from source.utils import FileOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class ProbeController:
    def __init__(self, oscilloscope_ctrl, engines_ctrl, logger_level="INFO"):
        # General attributes:
        self.probe_name = None
        self.configuration = {}

        # Set logger:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level=logger_level)

        # Probe controller must inherit the oscilloscope and engines controller:
        self.engines_ctrl = engines_ctrl
        self.oscilloscope_ctrl = oscilloscope_ctrl

    def move_xy_probe(self, coordinates):
        # Move XY engines:
        self.engines_ctrl.xy_axis_ctrl.move(probe=self.probe_name,
                                            # TODO: PCB mapping must rotate PCB, not this module (x -> y, y -> x)
                                            y_position=coordinates['x'],
                                            x_position=coordinates['y'],
                                            speed=self.configuration["speed"])

    def initialize(self, probe_name, configuration, calibration_points_df):
        self.probe_name = int(probe_name)
        self.configuration = configuration  # General configuration of the probe: speed, acceleration, ...

        # Calibrate XY engines:
        # TODO: add probe XY position offset - PCB is placed at FP center
        self.engines_ctrl.xy_axis_ctrl.homing(probe=self.probe_name)

        # Calibrate Z engine:
        for point_index, point_data in calibration_points_df.iterrows():
            for coordinates in point_data["trajectories"]:
                # Move probe to Z homing point:
                self.move_xy_probe(coordinates)

                # Z axis homing:
                self.engines_ctrl.z_axis_ctrl.homing(probe=self.probe_name)

        # Move XY engines to initial position = [0, 0]:
        self.move_xy_probe({'x': 0, 'y': 0})

        # TODO: add flag to check if homing has been done or not
        # return True or False

    def measure_test_point(self, trajectory, measurement_inputs, test_point_name=""):
        """ measure_test_point(self, list, dict)

        The trajectory is a list of coordinates, so the software must calculate the incremental values to move the
        engines.
        """
        self.logger.set_message(level="INFO", message_level="SUBSECTION", message=test_point_name)

        # Move probe to test point following the trajectory:
        for coordinates in trajectory:
            self.move_xy_probe(coordinates)

        # Measure test point:
        measurement_inputs["channel"] = self.probe_name
        result = self.oscilloscope_ctrl.measure(measurement_inputs)
        return result
