__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


def test_vds1022_inactive(vds1022_inactive):
    inputs = [{"channel": 1,
               "signal_max_value": 5,
               "signal_min_value": 0,
               "frequency": 1000,
               "trigger_edge_slope": "RISE",
               "coupling": "DC",
               "probe_attenuation": "X10",
               "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]}]

    result = vds1022_inactive.run(inputs)

    assert len(result) == 1, "Only one channel was specified."
    assert len(result[0]["measurements"].keys()) == 4, "The method must return 4 measurements."
    for measurement in result[0]["measurements"].values():
        assert type(measurement) == float, "The measurements must return float values."

    vds1022_inactive.close_connection()


def test_vds1022_inactive_multiple_channels(vds1022_inactive):
    inputs = [{"channel": 2,
               "signal_max_value": 5,
               "signal_min_value": 0,
               "frequency": 1000,
               "trigger_edge_slope": "RISE",
               "coupling": "DC",
               "probe_attenuation": "X10",
               "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]},
              {"channel": 1,
               "signal_max_value": 5,
               "signal_min_value": 0,
               "frequency": 0,
               "trigger_edge_slope": "FALL",
               "coupling": "AC",
               "probe_attenuation": "X1",
               "measurements": []}]

    result = vds1022_inactive.run(inputs)

    assert len(result) == 2, "Only one channel was specified."
    assert len(result[0]["measurements"].keys()) == 4, "The method must return 4 measurements."
    assert len(result[1]["measurements"].keys()) == 0, "The method must return 4 measurements."
    for measurement in result[0]["measurements"].values():
        assert type(measurement) == float, "The measurements must return float values."

    vds1022_inactive.close_connection()


def test_vds1022_inactive_channel_not_valid(vds1022_inactive):
    inputs = [{"channel": 3,
               "signal_max_value": 5,
               "signal_min_value": 0,
               "frequency": 1000,
               "trigger_edge_slope": "RISE",
               "coupling": "DC",
               "probe_attenuation": "X10",
               "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]}]

    try:
        vds1022_inactive.run(inputs)
        assert 0, "Channel not valid."
    except Exception as exception:
        assert str(exception) == "Channel is not valid. Available channels are 1 and 2.", "Not valid exception error."
