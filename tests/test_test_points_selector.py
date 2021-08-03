import pytest


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


@pytest.mark.parametrize("user_inputs, general_expected_result, pads_expected_result", [
                        (["DATA-RB7", "CLOCK-RB6"], 5, 2),
                        ([], 0, 0),
                        (["DATA-RB7"], 2, 1),
                        (["CLOCK-RB6"], 3, 1)

])
def test_pcb_pic_programmer_example_nets_filter(test_points_selector, pcb_pic_programmer_example_info, user_inputs,
                                                general_expected_result, pads_expected_result):
    print(pcb_pic_programmer_example_info)
    tp_selector_result = test_points_selector.run(user_inputs, pcb_pic_programmer_example_info)
    print(tp_selector_result)
    # Check test point selector results:
    assert len(tp_selector_result) == general_expected_result, f"The method must return {general_expected_result} " \
                                                               f"test points."
    assert len(tp_selector_result["net_name"].unique()) == pads_expected_result, f"The method must return " \
                                                                                 f"{pads_expected_result} " \
                                                                                 f"different nets."
