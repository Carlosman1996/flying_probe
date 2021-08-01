import os
from pathlib import Path
import math
import json
import pandas as pd
from pandas.api.types import is_numeric_dtype
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

# from kicad.pcbnew import Board
# from kicad.pcbnew import Text
from utils import DataframeOperations

__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"

pd.set_option('display.max_rows', None, 'display.max_columns', None)
FILE_DIRECTORY = Path(os.path.dirname(os.path.abspath(__file__)))


class PCBMapping:
    def __init__(self, pcb_path):
        if not os.path.isfile(pcb_path):
            raise Exception("KiCAD PCB file path cannot be found.")
        self.pcb_path = pcb_path  # File path must be a "kicad_pcb" type.
        # self.board = Board.from_file(pcb_path)
        self.board = None

    def read_vias(self):
        vias_df = pd.DataFrame(columns=["position", "drill", "width"])
        for via in self.board.vias:
            vias_df.loc[len(vias_df)] = [via.position, via.drill, via.width]
        return vias_df

    def read_tracks(self):
        tracks_df = pd.DataFrame(columns=["start", "end", "width"])
        for track in self.board.tracks:
            tracks_df.loc[len(tracks_df)] = [track.start, track.end, track.width]
        return tracks_df

    def read_texts(self):
        texts_df = pd.DataFrame(columns=["text", "position"])
        for text in self.board.drawings:
            if type(text) is Text:
                texts_df.loc[len(texts_df)] = [text.text, text.position]
        return texts_df

    def read_modules(self):
        modules_df = pd.DataFrame(columns=["reference", "position"])
        for module in self.board.modules:
            modules_df.loc[len(modules_df)] = [module.reference, module.position]
        return modules_df

    def read_zones(self):
        zones_df = pd.DataFrame(columns=["name", "priority"])
        for zone in self.board.zones:
            zones_df.loc[len(zones_df)] = [zone.net.name, zone.priority]
        return zones_df

    # Hardcoded
    def run(self):
        def convert_str_to_list(column):
            processed_column = column.copy()

            for key, item in processed_column.items():
                if type(item) == str:
                    processed_column[key] = json.loads(item)
            return processed_column

        pcb_info_df = DataframeOperations.read_csv(self.pcb_path)

        # Process information: the units must be mm and the coordinates list of points, not strings:
        pcb_info_df = pcb_info_df.apply(lambda row: row / 1000 if is_numeric_dtype(row) else row)
        pcb_info_df.loc[:, ["position", "shape_coordinates"]] = \
            pd.DataFrame({"position": convert_str_to_list(pcb_info_df["position"]),
                          "shape_coordinates": convert_str_to_list(pcb_info_df["shape_coordinates"])})
        return pcb_info_df


class TestPointsSelector:
    def __init__(self):
        # Hardcoded values
        self.probes = {"1": {"inclination": 0,  # degrees
                             "diameter": 0.005},
                       "2": {"inclination": 12,  # degrees
                             "diameter": 0.005},
                       "3": {"inclination": -12,  # degrees
                             "diameter": 0.005}}
        self.minimum_distance_error = 0.005
        self.test_point_surface_number_layers = 3
        self.test_point_surface_number_points = 12

    def calculate_component_minimum_distance(self, test_point_position, test_point_width, probe_inclination,
                                             probe_diameter, component_shape_coordinates, component_height):
        # The probes inclination only affects in X axis, so components placed above or below the test point do not
        # affect to movement. Also, components placed at right affect to probes with negative inclination and components
        # placed at left affect to probes with positive inclination:
        component_x_axis = False
        component_x_right_axis = False  # TODO: components placed at right affect to probes with negative inclination.
        component_y_right_axis = False  # TODO: components placed at left affect to probes with positive inclination.
        for index, coordinate in enumerate(component_shape_coordinates):
            if index != 0:
                last_coordinate = component_shape_coordinates[index - 1]

                # Check if component is above or below:
                if coordinate[1] > test_point_position[1] and last_coordinate[1] > test_point_position[1]:
                    pass
                elif coordinate[1] < test_point_position[1] and last_coordinate[1] < test_point_position[1]:
                    pass
                else:
                    component_x_axis = True
                    break

        # Calculate minimum distance:
        if component_x_axis:
            try:
                minimum_distance = component_height / math.tan(abs(probe_inclination))
            except ZeroDivisionError:
                minimum_distance = 0
        else:
            minimum_distance = 0
        minimum_distance += probe_diameter / 2 + self.minimum_distance_error

        # The probe can be placed at any point of the pad, so the half of the test point width must be added to the
        # minimum distance (worst case - the current distance is referred to the centre of the test point):
        minimum_distance += test_point_width / 2
        return minimum_distance

    def create_test_point_surface_points(self, test_point_coordinates, minimum_distance):
        points = []

        # Create points list:
        number_points_per_side = int(self.test_point_surface_number_points / 4)
        # Iterate per number layer:
        for layer_index in range(self.test_point_surface_number_layers):
            # The pad is supposed to be a square area to simplify code. Iterate per square side:
            for side_index in range(4):
                # Iterate over the number of points per layer:
                for point_index in range(number_points_per_side):
                    if side_index == 0:
                        x_coordinate = test_point_coordinates[0] + minimum_distance / 2
                        y_coordinate = test_point_coordinates[1] - minimum_distance / 2 + \
                            minimum_distance * point_index / number_points_per_side
                    elif side_index == 1:
                        x_coordinate = test_point_coordinates[0] + minimum_distance / 2 - \
                            minimum_distance * point_index / number_points_per_side
                        y_coordinate = test_point_coordinates[1] + minimum_distance / 2
                    elif side_index == 2:
                        x_coordinate = test_point_coordinates[0] - minimum_distance / 2
                        y_coordinate = test_point_coordinates[1] + minimum_distance / 2 - \
                            minimum_distance * point_index / number_points_per_side
                    else:
                        x_coordinate = test_point_coordinates[0] - minimum_distance / 2 + \
                            minimum_distance * point_index / number_points_per_side
                        y_coordinate = test_point_coordinates[1] - minimum_distance / 2

                    points.append([x_coordinate * layer_index / self.test_point_surface_number_layers,
                                   y_coordinate * layer_index / self.test_point_surface_number_layers])
        return points

    def get_usable_probes(self, test_point_position, test_point_width, components_df):
        usable_probes = []

        for probe_key, probe_parameters in self.probes.items():
            is_probe_usable = True
            for index, component in components_df.iterrows():
                # Calculate the minimum distance necessary between the test point and the components to avoid a probe
                # collision in the measurement process:
                minimum_distance = self.calculate_component_minimum_distance(test_point_position,
                                                                             test_point_width,
                                                                             probe_parameters["inclination"],
                                                                             probe_parameters["diameter"],
                                                                             component["shape_coordinates"],
                                                                             component["height"])

                # Create a point cloud around the test point centre of coordinates:
                test_point_surface_points = self.create_test_point_surface_points(test_point_position, minimum_distance)
                for test_point_surface_point in test_point_surface_points:
                    # Define shapely point:
                    point = Point(*test_point_surface_point)
                    # Define shapely polygon:
                    polygon = Polygon(component["shape_coordinates"])
                    # Check if point is inside the polygon:
                    if polygon.contains(point):
                        is_probe_usable = False
                        break

                # If any point of the test point theoretical surface is inside the component, the probe cannot be used:
                if not is_probe_usable:
                    break

            # The probe can be used to measure test point:
            if is_probe_usable:
                usable_probes.append(probe_key)
        return usable_probes

    def run(self, user_nets, pcb_info_df):
        # Separate vias and placement outlines in different dataframes:
        test_points_df = pcb_info_df[pcb_info_df["type"] == "via"].copy()
        components_df = pcb_info_df[pcb_info_df["type"] == "placement_outline"].copy()

        # Check the number of pads available per user net:
        test_points_df = test_points_df[test_points_df["net_name"].isin(user_nets)]

        # Filter pads: only are testable those whose distance with components are big enough to avoid probes collision
        test_points_df["probes_usable"] = \
            test_points_df.apply(lambda test_point: self.get_usable_probes(test_point["position"],
                                                                           test_point["diameter"],
                                                                           components_df), axis=1)
        return test_points_df


if __name__ == "__main__":
    file_path = str(FILE_DIRECTORY.parent) + "\\assets\\PCB\\pic_programmer\\API_info\\API_info_pcb.csv"

    pcb_obj = PCBMapping(file_path)
    info_df = pcb_obj.run()

    user_nets_list = {"DATA-RB7": {}}
    test_points_obj = TestPointsSelector()
    tp_selector_result = test_points_obj.run(list(user_nets_list.keys()), info_df)
    print(tp_selector_result)
