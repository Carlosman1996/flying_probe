import sys
import copy
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


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class FlyingProbe:
    def __init__(self, inputs_path=None, outputs_path=None):
        # Main attributes:
        self.inputs_path = inputs_path
        self.outputs_path = outputs_path

        # Initialize calculations modules:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level="DEBUG")
        self.inputs_controller = files_controller.InputsController(inputs_path=self.inputs_path)
        self.pcb_mapping = pcb_mapping.PCBMapping(pcb_path=self.inputs_controller.pcb_path)
        self.checkpoints_selector = checkpoints_selector.TestPointsSelector()
        self.flying_maps = flying_maps.FlyingMaps()
        self.pretest_files_controller = files_controller.PreTestController(pretest_path=self.outputs_path)

        # Read configuration data:
        self.conf_data = self.inputs_controller.read_conf_data()

        # Initialize devices modules:
        self.engines_controller = engines_controller.EnginesController(engines_conf=self.conf_data["engines"])
        self.oscilloscope_controller = \
            oscilloscope_controller.OscilloscopeController(oscilloscope_conf=self.conf_data["oscilloscope"])

        self.probes_controller = {}
        self.probe_controller = probe_controller.ProbeController(oscilloscope_ctrl=self.oscilloscope_controller,
                                                                 engines_ctrl=self.engines_controller)

    @staticmethod
    def request_input_load_test():
        question = "Do you want to load previous pre-test results?"
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
        inputs_data = self.inputs_controller.read_inputs_data()

        # Read PCB:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute PCB Mapping module")
        pcb_info_df = self.pcb_mapping.run()

        # Run test points selector:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Test Points Selector module")
        user_nets = list(inputs_data.keys())
        test_points_data = self.checkpoints_selector.run(probes_conf=self.conf_data["probes"],
                                                         user_nets=user_nets,
                                                         pcb_info_df=pcb_info_df)

        # Run flying maps:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Flying Maps module")
        test_points_data = self.flying_maps.run(test_points_data)
        # TODO: implement flying maps module methods

        # Save configuration and test planning:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Save Pre-Test results")
        self.pretest_files_controller.save_data(inputs_data=inputs_data,
                                                configuration_data=self.conf_data,
                                                test_points_data=test_points_data)
        return inputs_data, test_points_data

    def execute_test(self, inputs_data, test_points_data):
        # Initialize engines:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Initialize engines")
        self.engines_controller.initialize()

        # Initialize oscilloscope:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Initialize oscilloscope")
        self.oscilloscope_controller.initialize()

        # Initialize probes:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Initialize probes")
        for probe, probe_conf in self.conf_data["probes"].items():
            self.probes_controller[probe] = copy.deepcopy(self.probe_controller)
            self.probes_controller[probe].initialize(probe_name=probe, configuration=probe_conf)

        # Iterate over each test point: move probes and measure:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Measure test points")
        test_points_data["measurements"] = \
            test_points_data.apply(lambda test_point:
                                   self.probes_controller[test_point["probe"]].
                                   measure_test_point(trajectory=test_point["trajectories"],
                                                      measurement_inputs=inputs_data[test_point["net_name"]]),
                                   axis=1)

        # Stop oscilloscope:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Stop oscilloscope")
        self.oscilloscope_controller.stop()

        # Stop engines:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Stop engines")
        self.engines_controller.stop()
        return test_points_data

    def run(self):
        inputs_data = {}
        conf_data = {}
        test_points_data = pd.DataFrame()

        # Load previous test
        self.logger.set_message(level="INFO", message_level="SECTION", message="Load previous test")
        load_previous_test = self.request_input_load_test()

        if not load_previous_test:
            self.logger.set_message(level="INFO", message_level="MESSAGE", message="Result: NO")
            # Run all pretest operations:
            inputs_data, test_points_data = self.pre_test_operations()
        else:
            self.logger.set_message(level="INFO", message_level="MESSAGE", message="Result: YES")
            # Load previous pre-test results:
            try:
                inputs_data, test_points_data = self.pretest_files_controller.read_data()
            except Exception as exception:
                self.logger.set_message(level="CRITICAL", message_level="MESSAGE", message="Unable to read files: "
                                                                                           f"{str(exception)}")

        # Run test:
        test_points_data = self.execute_test(inputs_data, test_points_data)
        print(test_points_data)
        print(test_points_data["measurements"].values[0])

        # Save results:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Save results")
        # TODO: implement save results methods in files_controller module


if __name__ == "__main__":
    flying_probe_obj = FlyingProbe(inputs_path=ROOT_PATH + "//inputs//",
                                   outputs_path=ROOT_PATH + "//docs//software//outputs//")
    flying_probe_obj.run()