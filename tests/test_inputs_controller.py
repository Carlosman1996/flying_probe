__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


def test_inputs_data_empty(inputs_controller_object):
    data = {}
    try:
        inputs_controller_object.read_inputs_data(data)
        assert 0, "Data structure is not correct."
    except Exception as exception:
        assert str(exception) == "Inputs data structure is not correct.", f"Not correct exception: {str(exception)}"


def test_inputs_data_missing_data(inputs_controller_object):
    data = {
        "DATA-RB6":
        {
            "trigger_edge_slope": "RISE",
            "coupling": "DC",
            "probe_attenuation": "X10",
            "signal_max_value": 5,
            "signal_min_value": 0,
            "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]
        },
        "DATA-RB7":
        {
            "coupling": "AC",
            "probe_attenuation": "X10",
            "signal_max_value": 5,
            "frequency": 1000,
            "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]
        }
    }
    try:
        inputs_controller_object.read_inputs_data(data)
        assert 0, "Data structure is not correct: missing data"
    except Exception as exception:
        assert str(exception) == "Inputs data structure is not correct.", f"Not correct exception: {str(exception)}"


def test_inputs_data_types_incorrect(inputs_controller_object):
    data = {
        "DATA-RB6":
        {
            "trigger_edge_slope": "RISE",
            "coupling": "DC",
            "probe_attenuation": 10,
            "signal_max_value": 5,
            "signal_min_value": 0,
            "frequency": "YES",
            "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]
        },
        "DATA-RB7":
        {
            "coupling": "AC",
            "probe_attenuation": "X10",
            "signal_max_value": "5",
            "signal_min_value": 0,
            "frequency": 1000,
            "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]
        }
    }
    try:
        inputs_controller_object.read_inputs_data(data)
        assert 0, "Data structure is not correct: data types incorrect"
    except Exception as exception:
        assert str(exception) == "Inputs data structure is not correct.", f"Not correct exception: {str(exception)}"


def test_inputs_data_correct(inputs_controller_object):
    data = {
        "DATA-RB6":
        {
            "trigger_edge_slope": "RISE",
            "coupling": "DC",
            "probe_attenuation": "X10",
            "signal_max_value": 5,
            "signal_min_value": 0,
            "frequency": 1000,
            "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]
        },
        "DATA-RB7":
        {
            "coupling": "AC",
            "probe_attenuation": "X10",
            "signal_max_value": 5,
            "signal_min_value": 0,
            "frequency": 1000,
            "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]
        }
    }
    try:
        inputs_controller_object.read_inputs_data(data)
    except Exception as exception:
        assert 0, f"Data structure is not correct: data structure is correct. Exception raised: {str(exception)}"


def test_configuration_data_types_incorrect(inputs_controller_object):
    data = {
        "probes":
        {
            "1":
            {
                "inclination": 0,
                "speed": "10000",
                "diameter": 0.001
            },
            "2":
            {
                "inclination": 12,
                "speed": "No speed",
                "diameter": 0.001
            }
        }
    }
    try:
        inputs_controller_object.read_conf_data(data)
        assert 0, "Data structure is not correct: data types incorrect"
    except Exception as exception:
        assert str(exception) == "Inputs data structure is not correct.", f"Not correct exception: {str(exception)}"


def test_configuration_data_correct(inputs_controller_object):
    data = {
        "probes":
        {
            "1":
            {
                "inclination": 0,
                "speed": 10000,
                "diameter": 0.001
            },
            "2":
            {
                "inclination": 12,
                "speed": 10000,
                "diameter": 0.001
            }
        }
    }
    try:
        inputs_controller_object.read_conf_data(data)
    except Exception as exception:
        assert 0, f"Data structure is not correct: data structure is correct. Exception raised: {str(exception)}"
