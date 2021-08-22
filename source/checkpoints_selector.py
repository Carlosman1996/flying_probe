import math
import pandas as pd
from shapely.geometry.polygon import Polygon
from source import utils


pd.set_option('display.max_rows', None, 'display.max_columns', None)


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class TestPointsSelector:
    def __init__(self, probes_configuration):
        # Hardcoded values
        self.probes = probes_configuration
        self.probes_surface_increment = 0.01    # Hardcoded parameter
        self.min_distance_multiplier = 5    # Hardcoded parameter

    @staticmethod
    def get_shape_extreme_apexes(shape_coordinates):
        all_x_coordinates = [point_coords[0] for point_coords in shape_coordinates]
        all_y_coordinates = [point_coords[1] for point_coords in shape_coordinates]
        apexes = [[max(all_x_coordinates), max(all_y_coordinates)],
                  [max(all_x_coordinates), min(all_y_coordinates)],
                  [min(all_x_coordinates), max(all_y_coordinates)],
                  [min(all_x_coordinates), min(all_y_coordinates)]]
        return apexes

    @staticmethod
    def get_tp_extreme_apexes(position, diameter):
        apexes = [[position[0] + diameter / 2, position[1] + diameter / 2],
                  [position[0] + diameter / 2, position[1] - diameter / 2],
                  [position[0] - diameter / 2, position[1] + diameter / 2],
                  [position[0] - diameter / 2, position[1] - diameter / 2]]
        return apexes

    @staticmethod
    def calculate_distance_between_points(point_1, point_2):
        distance = math.sqrt((point_2[0] - point_1[0])**2 + (point_2[1] - point_1[1])**2)
        return distance

    def get_minimum_distance(self, tp_position, component_apexes):
        minimum_distance = float('inf')
        for point in component_apexes:
            distance = self.calculate_distance_between_points(tp_position, point)
            if distance < minimum_distance:
                minimum_distance = distance
        return minimum_distance

    def get_probe_projection(self, test_point_position, shape, thickness, inclination, component_height):
        # TODO: calculate projection over XY axis
        shape = [[test_point_position[0] + self.probes_surface_increment,
                  test_point_position[1] + self.probes_surface_increment],
                 [test_point_position[0] - self.probes_surface_increment,
                  test_point_position[1] + self.probes_surface_increment],
                 [test_point_position[0] - self.probes_surface_increment,
                  test_point_position[1] - self.probes_surface_increment],
                 [test_point_position[0] + self.probes_surface_increment,
                  test_point_position[1] - self.probes_surface_increment]]
        return shape

    def add_probes_to_test_points_dataframe(self, test_points_df):
        tps_per_probe_frames = []

        for probe_key, probe_parameters in self.probes.items():
            test_points_df["probe"] = probe_key
            tps_per_probe_frames.append(test_points_df.copy())
        test_points_df = pd.concat(tps_per_probe_frames).reset_index()
        return test_points_df

    def check_probe_in_tp(self, test_point, components_df):
        # Calculate an approximated minimum distance between all components and the current test point:
        components_df["minimum_distance"] = \
            components_df.apply(lambda component: self.get_minimum_distance(test_point["position"],
                                                                            component["extreme_apexes"]), axis=1)

        # Select components close to the test point:
        # TODO: valid components can be filtered. Eg: test points inside placement outlines or components with L shape.
        components_df = components_df[
            components_df["minimum_distance"] < self.probes_surface_increment * self.min_distance_multiplier]

        # Iterate over each component:
        for index, component in components_df.iterrows():
            # Calculate the probe shape at height equal to the component height.
            probe_shape = self.get_probe_projection(test_point["position"], None, None, None, None)

            # Define shapely polygon for probe shape:
            probe_polygon = Polygon(probe_shape)
            # Define shapely polygon for component shape:
            component_polygon = Polygon(component["shape_coordinates"])

            # Check intersection between polygons:
            intersection = probe_polygon.intersects(component_polygon)
            if intersection:
                return False
        return True

    def run(self, user_nets, pcb_info_df):
        # Separate vias and placement outlines in different dataframes:
        test_points_df = pcb_info_df[pcb_info_df["type"] == "via"].copy()
        components_df = pcb_info_df[pcb_info_df["type"] == "placement_outline"].copy()

        # Check the number of pads available per user net:
        test_points_df = test_points_df[test_points_df["net_name"].isin(user_nets)]

        # Filter pads: only are testable those whose distance with components are big enough to avoid probes collision
        if not test_points_df.empty:
            # Add all probes to test points: duplicate each test point depending on the probe
            test_points_df = self.add_probes_to_test_points_dataframe(test_points_df)

            # Calculate extreme apexes of each component:
            components_df["extreme_apexes"] = \
                components_df.apply(lambda component:
                                    self.get_shape_extreme_apexes(component["shape_coordinates"]), axis=1)

            # Check if probe can be used:
            test_points_df["probe_usable"] = \
                test_points_df.apply(lambda test_point: self.check_probe_in_tp(test_point,
                                                                               components_df.copy()), axis=1)

            # Remove those test points which has not usable probes
            test_points_df = test_points_df[test_points_df.probe_usable]
        return test_points_df


if __name__ == "__main__":
    from source.pcb_mapping import PCBMapping
    file_path = str(utils.ROOT_PATH) + "//assets//PCB//pic_programmer//API_info//API_info_pcb.csv"
    pcb_obj = PCBMapping(file_path)
    info_df = pcb_obj.run()

    configuration = {"1": {"inclination": 0,
                           "diameter": 0.005,
                           "shape": [[0, 0], [0.25, 0], [0.25, 2], [1.25, 2], [2.25, 2], [2.25, 6], [-2.25, 6],
                                     [-2.25, 2], [-1.25, 2], [-0.25, 2], [-0.25, 0]]},
                     "2": {"inclination": 12,
                           "diameter": 0.005,
                           "shape": [[0, 0], [0.25, 0], [0.25, 2], [1.25, 2], [2.25, 2], [2.25, 6], [-2.25, 6],
                                     [-2.25, 2], [-1.25, 2], [-0.25, 2], [-0.25, 0]]}}
    user_nets_list = {"DATA-RB7": {}}
    test_points_obj = TestPointsSelector(configuration)
    tp_selector_result = test_points_obj.run(list(user_nets_list.keys()), info_df)
    print(tp_selector_result)
