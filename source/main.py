import os
import sys
import pandas as pd

import logger
import files_controller
import pcb_mapping
import checkpoints_selector
import flying_maps
import engines_controller
import oscilloscope_controller
import probe_controller
from utils import ROOT_PATH
from utils import FileOperations
from utils import DataframeOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class FlyingProbe:
    def __init__(self, inputs_path=None, outputs_path=None, logger_level="INFO"):
        # Main attributes:
        self.inputs_path = inputs_path
        self.outputs_path = outputs_path
        self.logger_level = logger_level

        # Initialize modules:
        # TODO: add property() method to initialize parameters and perform inputs validation.
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level=self.logger_level)
        self.inputs_controller = files_controller.InputsController(inputs_path=self.inputs_path)
        self.pretest_controller = files_controller.PreTestController(pretest_path=self.inputs_path)
        self.outputs_controller = files_controller.OutputsController(outputs_path=self.outputs_path)
        self.pcb_mapping = pcb_mapping.PCBMappingKiCAD(pcb_path=self.inputs_controller.pcb_path)
        self.checkpoints_selector = checkpoints_selector.TestPointsSelector()
        self.calibration_points_selector = checkpoints_selector.CalibrationPointsSelector()
        self.flying_maps = flying_maps.FlyingMaps()
        self.engines_controller = engines_controller.EnginesController(logger_level=self.logger_level)
        self.oscilloscope_controller = oscilloscope_controller.OscilloscopeController()

        self.probes_controller = {}

    @staticmethod
    def request_input(question=""):
        valid = {"yes": True, "y": True, "no": False, "n": False}
        prompt = " [y/N] "

        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()

            # Enter as input:
            if choice == "":
                return False
            # Valid input:
            elif choice in valid:
                if choice == "y" or choice == "yes":
                    return True
                else:
                    return False
            # Not valid input:
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

    def pre_test_operations(self):
        # Execute inputs controller module:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Inputs Controller module")
        inputs_data, conf_data = self.inputs_controller.run()

        # Read PCB:
        # TODO: remove lines commented used for testing
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute PCB Mapping module")
        # pcb_info_df = self.pcb_mapping.run()
        pcb_info_df = DataframeOperations.read_csv(file_path=os.path.join(self.inputs_path, "pcb_data.csv"))
        pcb_info_df.loc[:, ["position", "shape_lines", "shape_circles", "shape_arcs"]] = \
            pd.DataFrame({"position": DataframeOperations.convert_str_to_list(pcb_info_df["position"]),
                          "shape_lines": DataframeOperations.convert_str_to_list(pcb_info_df["shape_lines"]),
                          "shape_circles": DataframeOperations.convert_str_to_list(pcb_info_df["shape_circles"]),
                          "shape_arcs": DataframeOperations.convert_str_to_list(pcb_info_df["shape_arcs"])})

        # Run test points selector:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Calibration Points Selector"
                                                                               "module")
        calibration_points_data = \
            self.calibration_points_selector.run(test_points_df=pcb_info_df,
                                                 calibration_conf=conf_data["engines"]["calibration"])

        # Run test points selector:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Test Points Selector module")
        user_nets = list(inputs_data.keys())
        test_points_data = self.checkpoints_selector.run(probes_conf=conf_data["probes"],
                                                         user_nets=user_nets,
                                                         pcb_info_df=pcb_info_df)

        # Run flying maps for test points data:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Flying Maps module for "
                                                                               "calibrations data")
        calibration_points_data = self.flying_maps.run(calibration_points_data)

        # Run flying maps for test points data:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Flying Maps module for test "
                                                                               "points data")
        test_points_data = self.flying_maps.run(test_points_data)

        # Save configuration and test planning:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Save Pre-Test results")
        self.pretest_controller.save_data(inputs_data=inputs_data,
                                          configuration_data=conf_data,
                                          test_points_data=test_points_data)
        return inputs_data, conf_data, test_points_data, calibration_points_data

    def execute_test(self, inputs_data, conf_data, test_points_data, calibration_points_data):
        # Check calibration points data:
        if len(calibration_points_data) == 0:
            self.logger.set_message(level="INFO", message_level="SECTION", message="No calibration points available")
            test_points_data.loc[:, "measurements"] = None
            return test_points_data

        # Initialize engines:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Initialize engines")
        self.engines_controller.initialize(configuration=conf_data["engines"])

        # Initialize oscilloscope:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Initialize oscilloscope")
        self.oscilloscope_controller.initialize(configuration=conf_data["oscilloscope"])

        # Initialize probes:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Initialize probes")
        for probe, probe_conf in conf_data["probes"].items():
            self.probes_controller[probe] = \
                probe_controller.ProbeController(oscilloscope_ctrl=self.oscilloscope_controller,
                                                 engines_ctrl=self.engines_controller,
                                                 logger_level=self.logger_level)

            # Initialize each probe: do homing
            self.probes_controller[probe].initialize(probe_name=probe,
                                                     configuration=probe_conf,
                                                     calibration_points_df=calibration_points_data)

        # Iterate over each test point: move probes and measure:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Measure test points")
        test_points_data["measurements"] = \
            test_points_data.apply(lambda test_point:
                                   self.probes_controller[test_point["probe"]].
                                   measure_test_point(trajectory=test_point["trajectories"],
                                                      measurement_inputs=inputs_data[test_point["net_name"]],
                                                      test_point_name=test_point["net_name"]),
                                   axis=1)

        # Close probes:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Stop probes")
        for probe, probe_conf in conf_data["probes"].items():
            self.probes_controller[probe].stop()

        return test_points_data

    def run(self):
        # Initialize main variables:
        inputs_data = {}
        conf_data = {}
        test_points_data = pd.DataFrame()
        calibration_points_data = pd.DataFrame()

        # Load previous test
        self.logger.set_message(level="INFO", message_level="SECTION", message="Load previous test")
        load_previous_test = self.request_input(question="Do you want to load previous pre-test results?")

        if not load_previous_test:
            self.logger.set_message(level="INFO", message_level="MESSAGE", message="Result: NO")
            # Run all pretest operations:
            inputs_data, conf_data, test_points_data, calibration_points_data = self.pre_test_operations()
        else:
            self.logger.set_message(level="INFO", message_level="MESSAGE", message="Result: YES")
            # Load previous pre-test results:
            try:
                inputs_data, test_points_data, calibration_points_data = self.pretest_controller.read_data()
            except Exception as exception:
                self.logger.set_message(level="CRITICAL", message_level="MESSAGE", message="Unable to read files: "
                                                                                           f"{str(exception)}")

        # Run test:
        test_points_data = self.execute_test(inputs_data, conf_data, test_points_data, calibration_points_data)

        # Save results:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Save results")
        self.outputs_controller.save_data(test_points_data)


if __name__ == "__main__":
    flying_probe_obj = FlyingProbe(inputs_path=ROOT_PATH + "//inputs//",
                                   outputs_path=ROOT_PATH + "//inputs//",
                                   logger_level="INFO")

    flying_probe_obj.run()
