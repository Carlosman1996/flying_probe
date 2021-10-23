import pytest


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


@pytest.mark.parametrize("user_inputs, probe_thickness, general_expected_result, pads_expected_result", [
                        (["DATA-RB7", "CLOCK-RB6"], 0.01, 2, 2),
                        ([], 0.01, 0, 0),
                        (["DATA-RB7"], 0.01, 1, 1),
                        (["CLOCK-RB6"], 0.01, 1, 1),
                        (["DATA-RB7", "CLOCK-RB6"], 0.005, 3, 2),
                        (["DATA-RB7"], 0.005, 2, 1)

])
def test_pcb_pic_programmer_example_one_probe(test_points_selector, pcb_pic_programmer_example_info,
                                              user_inputs, probe_thickness, general_expected_result,
                                              pads_expected_result):
    probes_configuration = {"1": {"inclination": 0,  # degrees
                                  "diameter": 0.001}}
    test_points_selector.probes_surface_increment = probe_thickness
    tp_selector_result = test_points_selector.run(probes_configuration, user_inputs, pcb_pic_programmer_example_info)

    # Check test point selector results:
    assert len(tp_selector_result) == general_expected_result, f"The method must return {general_expected_result} " \
                                                               f"test points."
    assert len(tp_selector_result["net_name"].unique()) == pads_expected_result, f"The method must return " \
                                                                                 f"{pads_expected_result} " \
                                                                                 f"different nets."


@pytest.mark.parametrize("user_inputs, probe_thickness, general_expected_result, pads_expected_result", [
                        (["DATA-RB7", "CLOCK-RB6"], 0.01, 4, 2),
                        ([], 0.01, 0, 0),
                        (["DATA-RB7"], 0.01, 2, 1),
                        (["CLOCK-RB6"], 0.01, 2, 1),
                        (["DATA-RB7", "CLOCK-RB6"], 0.005, 6, 2),
                        (["DATA-RB7"], 0.005, 4, 1)

])
def test_pcb_pic_programmer_example_two_probes(test_points_selector, pcb_pic_programmer_example_info,
                                               user_inputs, probe_thickness, general_expected_result,
                                               pads_expected_result):
    probes_configuration = {"1": {"inclination": 0,  # degrees
                                  "diameter": 0.001},
                            "2": {"inclination": 12,  # degrees
                                  "diameter": 0.001}}
    test_points_selector.probes_surface_increment = probe_thickness
    tp_selector_result = test_points_selector.run(probes_configuration, user_inputs, pcb_pic_programmer_example_info)

    # Check test point selector results:
    assert len(tp_selector_result) == general_expected_result, f"The method must return {general_expected_result} " \
                                                               f"test points."
    assert len(tp_selector_result["net_name"].unique()) == pads_expected_result, f"The method must return " \
                                                                                 f"{pads_expected_result} " \
                                                                                 f"different nets."


@pytest.mark.parametrize("calibration_nets, calibration_points, cal_nets_result, cal_points_result", [
                        (["CLOCK-RB6", "DATA-RB7"], 0, [], 0),
                        (["CLOCK-RB6", "DATA-RB7"], 1, ["CLOCK-RB6"], 1),
                        (["CLOCK-RB6", "DATA-RB7"], 5, ["CLOCK-RB6", "DATA-RB7"], 5),
                        (["CLOCK-RB6", "DATA-RB7"], 10, ["CLOCK-RB6", "DATA-RB7"], 6),
                        (["DATA-RB7"], 10, ["DATA-RB7"], 3)
])
def test_calibration_points_selector(calibration_points_selector, pcb_pic_programmer_example_info,
                                     calibration_nets, calibration_points, cal_nets_result, cal_points_result):
    configuration = {"nets": calibration_nets,
                     "points": calibration_points}

    calibration_points_df = calibration_points_selector.run(pcb_pic_programmer_example_info, configuration)

    # Check test point selector results:
    assert len(calibration_points_df) == cal_points_result, f"The method must return {cal_points_result} " \
                                                            f"test points."
    assert list(calibration_points_df["net_name"].unique()) == cal_nets_result, f"The method must return " \
                                                                                f"{cal_nets_result} " \
                                                                                f"different nets."

