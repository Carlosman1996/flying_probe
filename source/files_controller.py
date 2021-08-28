from source.utils import ROOT_PATH
from source.utils import JSONFileOperations
from source.utils import DataframeOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class InputsController:
    def __init__(self, inputs_path=None):
        if inputs_path is None:
            inputs_path = ROOT_PATH + "//inputs//"

        # Set files paths:
        self.inputs_data_path = inputs_path + "inputs_data.json"
        self.conf_data_path = inputs_path + "configuration_data.json"
        self.pcb_path = inputs_path + "API_info_pcb.csv"   # Hardcoded
        # self.pcb_path = ROOT_PATH + "//inputs//*.kicad_pcb"

    def read_inputs_data(self, data=None):
        if data is None:
            data = JSONFileOperations.read_file(self.inputs_data_path)

        # Check data types structure:
        data_schema = {
            "type": "object",
            "properties": {
                "signal_max_value": {"type": "number"},
                "signal_min_value": {"type": "number"},
                "frequency": {"type": "number"},
                "measurements": {
                    "type": "array"
                    # "enum": [
                    #     "PERIOD", "FREQUENCY", "AVERAGE", "MAX", "MIN", "VTOP", "VBASE",
                    #     "VAMP", "PKPK", "CYCRMS", "RTIME", "FTIME", "PDUTY", "NDUTY",
                    #     "PWIDTH", "NWIDTH", "OVERSHOOT", "PRESHOOT", "RDELAY", "FDELAY"]
                }
            },
            "required": ["signal_max_value", "signal_min_value", "frequency", "measurements", "probe_attenuation"],
            "additionalProperties": {"type": "string"}
        }

        if JSONFileOperations.validate_data_schema_dict_of_dicts(data, data_schema):
            # Complete the inputs dictionary if any key is missing and return the data
            for sub_data in data.values():
                parameters = sub_data.keys()
                if "trigger_edge_slope" not in parameters:
                    sub_data["trigger_edge_slope"] = "RISE"
                if "coupling" not in parameters:
                    sub_data["coupling"] = "DC"
            return data
        else:
            raise Exception("Inputs data structure is not correct.")

    def read_conf_data(self, data=None):
        if data is None:
            data = JSONFileOperations.read_file(self.conf_data_path)

        # Check data types structure:
        data_schema = {
            "type": "object",
            "additionalProperties": {"type": "number"}
        }

        if JSONFileOperations.validate_data_schema_dict_of_dicts(data["probes"], data_schema):
            return data
        else:
            raise Exception("Inputs data structure is not correct.")

    def run(self):
        inputs_data = self.read_inputs_data()
        conf_data = self.read_conf_data()
        return inputs_data, conf_data


class PreTestController:
    def __init__(self, pretest_path=None):
        self.pretest_path = pretest_path
        self.inputs_data_file_name = "inputs_data.json"
        self.conf_data_file_name = "configuration_data.json"
        self.test_points_data_file_name = "test_points_processed.csv"   # Hardcoded

    def save_data(self, inputs_data, configuration_data, test_points_data):
        # Write inputs data file:
        JSONFileOperations.write_file(self.pretest_path + self.inputs_data_file_name, inputs_data)

        # Write configuration data file:
        JSONFileOperations.write_file(self.pretest_path + self.conf_data_file_name, configuration_data)

        # Write test points data file:
        DataframeOperations.save_csv(self.pretest_path + self.test_points_data_file_name, test_points_data)

    def read_data(self):
        # Read inputs data file:
        inputs_data = JSONFileOperations.read_file(self.pretest_path + self.inputs_data_file_name)

        # Read configuration data file:
        conf_data = JSONFileOperations.read_file(self.pretest_path + self.conf_data_file_name)

        # Read test points data file:
        test_points_data = DataframeOperations.read_csv(self.pretest_path + self.test_points_data_file_name)
        return inputs_data, conf_data, test_points_data


class OutputsController:
    def __init__(self, outputs_path=None):
        self.outputs_path = outputs_path
        self.test_points_data_file_name = "test_points_measurements.csv"   # Hardcoded

    def save_data(self, test_points_data):
        # Write test points data file:
        DataframeOperations.save_csv(self.outputs_path + self.test_points_data_file_name, test_points_data)


if __name__ == "__main__":
    inputs_ctrl_obj = InputsController()
    inputs_ctrl_obj.read_inputs_data()
