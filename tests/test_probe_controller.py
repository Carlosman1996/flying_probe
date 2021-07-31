__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


def test_probe_inactive_integration_test(probe_inactive):
    trajectory = [{'x': 10,
                   'y': 0},
                  {'x': 20,
                   'y': -1},
                  {'x': -10,
                   'y': 40}]
    measurement = {"channel": 1,
                   "trigger_edge_slope": "RISE",
                   "coupling": "DC",
                   "probe_attenuation": "X10",
                   "signal_max_value": 5,
                   "signal_min_value": 0,
                   "frequency": 1000,
                   "measurements": ["FREQUENCY", "CYCRMS", "MAX", "MIN"]}

    result = probe_inactive.measure_test_point(trajectory=trajectory, measurement_inputs=measurement)

    # Check measurement results:
    assert len(result["measurements"].keys()) == 4, "The method must return 4 measurements."
    for measurement in result["measurements"].values():
        assert type(measurement) == float, "The measurements must return float values."

    # Check probe current position:
    current_position = {'x': -10,
                        'y': 40}
    assert current_position == probe_inactive.current_position, f"The current position must be: {current_position}"
