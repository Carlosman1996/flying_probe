__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


def test_vds1022_inactive(vds1022_inactive):
    conf_dict = [{"channel": 1,
                  "trigger_edge_slope": "RISE",
                  "coupling": "DC",
                  "probe_attenuation": "X10"}]

    meas_dict = {"channel": 1,
                 "signal_max_value": 5,
                 "signal_min_value": 0,
                 "frequency": 1000,
                 "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]}

    vds1022_inactive.initialize(conf_dict)
    result = vds1022_inactive.measure(meas_dict)
    vds1022_inactive.stop()

    assert len(result["measurements"].keys()) == 4, "The method must return 4 measurements."
    for measurement in result["measurements"].values():
        assert type(measurement) == float, "The measurements must return float values."

    vds1022_inactive.close_connection()


def test_vds1022_inactive_multiple_channels(vds1022_inactive):
    conf_dict = [{"channel": 2,
                  "trigger_edge_slope": "RISE",
                  "coupling": "DC",
                  "probe_attenuation": "X10"},
                 {"channel": 1,
                  "trigger_edge_slope": "FALL",
                  "coupling": "AC",
                  "probe_attenuation": "X1"}
                 ]

    vds1022_inactive.initialize(conf_dict)

    results = []
    meas_dict = {"channel": 2,
                 "signal_max_value": 5,
                 "signal_min_value": 0,
                 "frequency": 1000,
                 "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]}
    results.append(vds1022_inactive.measure(meas_dict))
    meas_dict = {"channel": 1,
                 "signal_max_value": 5,
                 "signal_min_value": 0,
                 "frequency": 0,
                 "measurements": []}
    results.append(vds1022_inactive.measure(meas_dict))

    vds1022_inactive.stop()

    assert len(results) == 2, "Only one channel was specified."
    assert len(results[0]["measurements"].keys()) == 4, "The method must return 4 measurements."
    assert len(results[1]["measurements"].keys()) == 0, "The method must return 4 measurements."
    for measurement in results[0]["measurements"].values():
        assert type(measurement) == float, "The measurements must return float values."

    vds1022_inactive.close_connection()


def test_vds1022_inactive_channel_not_valid_conf_stage(vds1022_inactive):
    conf_dict = [{"channel": 3,
                  "trigger_edge_slope": "RISE",
                  "coupling": "DC",
                  "probe_attenuat ion": "X10"}]

    try:
        vds1022_inactive.initialize(conf_dict)
        assert 0, "Channel not valid."
    except Exception as exception:
        assert str(exception) == "Channel is not valid. Available channels are 1 and 2.", "Not valid exception error."


def test_vds1022_inactive_channel_not_valid_meas_stage(vds1022_inactive):
    meas_dict = {"channel": 3,
                 "signal_max_value": 5,
                 "signal_min_value": 0,
                 "frequency": 0,
                 "measurements": []}

    try:
        vds1022_inactive.measure(meas_dict)
        assert 0, "Channel not valid."
    except Exception as exception:
        assert str(exception) == "Channel is not valid. Available channels are 1 and 2.", "Not valid exception error."
