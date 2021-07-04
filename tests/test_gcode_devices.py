__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


def test_engine_inactive(engine_inactive):
    result = engine_inactive.move(movement=-1, speed=1)

    assert type(result) == str, "Output must be a string."

    engine_inactive.close_connection()
