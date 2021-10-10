import pandas as pd
from utils import ROOT_PATH
from utils import DataframeOperations


pd.set_option('display.max_rows', None, 'display.max_columns', None)


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class FlyingMaps:
    def __init__(self):
        pass

    def run(self, test_points_data):
        # Select one test point per net:
        # TODO: total trajectory: minimum distance, not first occurrence
        simplified_tps_data = pd.DataFrame(columns=test_points_data.columns)
        for net_name, net_test_points in test_points_data.groupby("net_name"):
            # Filter by vias:
            net_vias = net_test_points[net_test_points["type"] == "via"].copy()

            if not net_vias.empty:
                simplified_tps_data = simplified_tps_data.append(net_vias.iloc[0], ignore_index=True)
            else:
                # Filter by pads:
                simplified_tps_data = simplified_tps_data.append(net_test_points.iloc[0], ignore_index=True)

        # Plan trajectories:
        # TODO: select minimum distance trajectory and avoid colliding too high objects
        simplified_tps_data["trajectories"] = simplified_tps_data.apply(lambda tp: [{'x': tp.position[0],
                                                                                     'y': tp.position[1]}], axis=1)
        return simplified_tps_data


if __name__ == "__main__":
    pcb_data = DataframeOperations.read_csv(ROOT_PATH + "//inputs//test_points_processed.csv")
    pcb_data.drop('trajectories', axis=1, inplace=True)
    pcb_data["position"] = pcb_data.apply(lambda row: eval(row.position), axis=1)

    flying_maps_obj = FlyingMaps()
    fp_trajectories = flying_maps_obj.run(pcb_data)
    print(fp_trajectories)
