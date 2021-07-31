__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class ProbeController:
    def __init__(self, configuration, oscilloscope_ctrl, engines_ctrl):
        # General attributes:
        self.configuration = configuration  # General configuration of the probe: speed, acceleration, ...
        self.current_position = {'x': 0,
                                 'y': 0}

        # Probe controller must inherit the oscilloscope and engines controller:
        self.engines_ctrl = engines_ctrl
        self.oscilloscope_ctrl = oscilloscope_ctrl

    def measure_test_point(self, trajectory, measurement_inputs):
        """ measure_test_point(self, list, dict)

        The trajectory is a list of coordinates, so the software must calculate the incremental values to move the
        engines.
        """
        # Move probe to test point following the trajectory:
        for coordinates in trajectory:
            # Move X engine:
            self.engines_ctrl.x_axis_ctrl.move(probe=self.configuration["probe"],
                                               movement=coordinates['x'] - self.current_position['x'],
                                               speed=self.configuration["speed"])
            # Move Y engine:
            self.engines_ctrl.y_axis_ctrl.move(probe=self.configuration["probe"],
                                               movement=coordinates['y'] - self.current_position['y'],
                                               speed=self.configuration["speed"])

            # Update probe position:
            self.current_position = {'x': coordinates['x'],
                                     'y': coordinates['y']}

        # Measure test point:
        measurement_inputs["channel"] = self.configuration["probe"]
        result = self.oscilloscope_ctrl.measure(measurement_inputs)

        return result
