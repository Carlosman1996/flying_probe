import pandas as pd


pd.set_option('display.max_rows', None, 'display.max_columns', None)


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class FlyingMaps:
    def __init__(self):
        pass

    def run(self, test_points_data):
        trajectory = [{'x': 10, 'y': 0},
                      {'x': 20, 'y': -1},
                      {'x': -10, 'y': 40}]
        test_points_data["trayectories"] = test_points_data.apply(lambda row: trajectory, axis=1)
        return test_points_data
