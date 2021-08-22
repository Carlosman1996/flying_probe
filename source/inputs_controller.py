from source.utils import ROOT_PATH
from source.utils import JSONFileOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class InputsController:
    def __init__(self):
        self.inputs_data_path = ROOT_PATH + "//inputs//inputs_data.json"
        self.conf_data_path = ROOT_PATH + "//inputs//configuration_data.json"
        self.pcb_path = ROOT_PATH + "//inputs//*.kicad_pcb"

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

        if JSONFileOperations.validate_data_schema_dict_of_dicts(data, data_schema):
            return data
        else:
            raise Exception("Inputs data structure is not correct.")

    def run(self):
        inputs_data = self.read_inputs_data()
        conf_data = self.read_conf_data()
        return inputs_data, conf_data


if __name__ == "__main__":
    inputs_ctrl_obj = InputsController()
    inputs_ctrl_obj.read_inputs_data()
