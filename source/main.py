import sys
# import pandas as pd
import pandas as pd

import logger
import files_controller
import pcb_mapping
import checkpoints_selector
import flying_maps
# import engines_controller
# import oscilloscope_controller
# import probe_controller
from utils import ROOT_PATH
from utils import FileOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class FlyingProbe:
    def __init__(self, inputs_path=None, pretest_path=None, outputs_path=None):
        # Main attributes:
        self.inputs_path = inputs_path
        self.pretest_path = pretest_path
        self.outputs_path = outputs_path

        # Initialize modules:
        self.logger = logger.Logger(module=FileOperations.get_file_name(__file__), level="DEBUG")
        self.inputs_controller = files_controller.InputsController(inputs_path=self.inputs_path)
        self.pcb_mapping = pcb_mapping.PCBMapping(pcb_path=self.inputs_controller.pcb_path)
        self.checkpoints_selector = checkpoints_selector.TestPointsSelector()
        self.flying_maps = flying_maps.FlyingMaps()
        self.pretest_files_controller = files_controller.PreTestController(pretest_path=self.pretest_path)

    def request_input_load_test(self):
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
        inputs_data, conf_data = self.inputs_controller.run()

        # Read PCB:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute PCB Mapping module")
        pcb_info_df = self.pcb_mapping.run()

        # Run test points selector:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Test Points Selector module")
        user_nets = list(inputs_data.keys())
        test_points_data = self.checkpoints_selector.run(probes_conf=conf_data,
                                                         user_nets=user_nets,
                                                         pcb_info_df=pcb_info_df)

        # Run flying maps:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Execute Flying Maps module")
        test_points_data = self.flying_maps.run(test_points_data)
        # TODO: implement flying maps module methods

        # Save configuration and test planning:
        self.logger.set_message(level="INFO", message_level="SECTION", message="Save Pre-Test results")
        self.pretest_files_controller.save_data(inputs_data=inputs_data,
                                                configuration_data=conf_data,
                                                test_points_data=test_points_data)
        return inputs_data, conf_data, test_points_data

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
            inputs_data, conf_data, test_points_data = self.pre_test_operations()
        else:
            self.logger.set_message(level="INFO", message_level="MESSAGE", message="Result: YES")
            # Load previous pre-test results:
            try:
                inputs_data, conf_data, test_points_data = self.pretest_files_controller.read_data()
            except Exception as exception:
                self.logger.set_message(level="CRITICAL", message_level="MESSAGE", message="Unable to read files: "
                                                                                           f"{str(exception)}")

        # Run test:
        print(inputs_data, conf_data, test_points_data)


if __name__ == "__main__":
    flying_probe_obj = FlyingProbe(inputs_path=ROOT_PATH + "//docs//software//inputs//",
                                   pretest_path=ROOT_PATH + "//docs//software//outputs//",
                                   outputs_path=ROOT_PATH + "//docs//software//outputs//")
    flying_probe_obj.run()
