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
def test_pcb_pic_programmer_example_one_probe(test_points_selector_one_probe, pcb_pic_programmer_example_info,
                                              user_inputs, probe_thickness, general_expected_result,
                                              pads_expected_result):
    test_points_selector_one_probe.probes_surface_increment = probe_thickness
    tp_selector_result = test_points_selector_one_probe.run(user_inputs, pcb_pic_programmer_example_info)

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
def test_pcb_pic_programmer_example_two_probes(test_points_selector_two_probes, pcb_pic_programmer_example_info,
                                               user_inputs, probe_thickness, general_expected_result,
                                               pads_expected_result):
    test_points_selector_two_probes.probes_surface_increment = probe_thickness
    tp_selector_result = test_points_selector_two_probes.run(user_inputs, pcb_pic_programmer_example_info)

    # Check test point selector results:
    assert len(tp_selector_result) == general_expected_result, f"The method must return {general_expected_result} " \
                                                               f"test points."
    assert len(tp_selector_result["net_name"].unique()) == pads_expected_result, f"The method must return " \
                                                                                 f"{pads_expected_result} " \
                                                                                 f"different nets."
