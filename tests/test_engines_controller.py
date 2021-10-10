__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


def test_engine_inactive_integration_test(engines_inactive):
    engines_inactive.xy_axis_ctrl.homing(probe=2)
    engines_inactive.xy_axis_ctrl.move(probe=1, x_move=-1, y_move=0, speed=1)
    engines_inactive.z_axis_ctrl.measure(probe=3)

    engines_inactive.stop()
