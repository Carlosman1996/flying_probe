import math
import re
import json
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from pandas.api.types import is_numeric_dtype

from source.utils import ROOT_PATH
from source.utils import FileOperations
from source.utils import DataframeOperations


pd.set_option('display.max_rows', None, 'display.max_columns', None)


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class PCBMapping:
    def __init__(self, pcb_path=ROOT_PATH + "\\inputs\\pcb_file.kicad_pcb"):
        if not FileOperations.check_file_exists(pcb_path):
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
        # for text in self.board.drawings:
        #     if type(text) is Text:
        #         texts_df.loc[len(texts_df)] = [text.text, text.position]
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
                    coordinates = json.loads(item)
                    for index_particular_coords, particular_coords in enumerate(coordinates):
                        # Placement outline (list of lists):
                        if type(particular_coords) == list:
                            for index_point_coords, point_coords in enumerate(particular_coords):
                                coordinates[index_particular_coords][index_point_coords] /= 1000
                        # Position (list):
                        else:
                            coordinates[index_particular_coords] /= 1000
                    processed_column[key] = coordinates
            return processed_column

        pcb_info_df = DataframeOperations.read_csv(self.pcb_path)

        # Process information: the units must be mm and the coordinates list of points, not strings:
        pcb_info_df = pcb_info_df.apply(lambda row: row / 1000 if is_numeric_dtype(row) else row)
        pcb_info_df.loc[:, ["position", "shape_coordinates"]] = \
            pd.DataFrame({"position": convert_str_to_list(pcb_info_df["position"]),
                          "shape_coordinates": convert_str_to_list(pcb_info_df["shape_coordinates"])})
        return pcb_info_df


class PCBMappingKiCAD:
    def __init__(self, pcb_path=ROOT_PATH + "//inputs//pcb_file.kicad_pcb"):
        if not FileOperations.check_file_exists(pcb_path):
            raise Exception("KiCAD PCB file path cannot be found.")
        self.pcb_path = pcb_path

        # Layers:
        self.borders_layers = ["Edge.Cuts"]
        self.placement_outlines_layers = ["*.SilkS", "F.SilkS", "B.SilkS"]
        self.pads_layers = ["*.Cu *.Mask", "F.Mask", "B.Mask"]
        self.vias_layers = ["top_layer bottom_layer", "top_layer", "bottom_layer"]

        # Dataframe:
        self.df_columns = ["type", "name", "net_name", "position", "drill", "diameter", "shape_coordinates", "height"]

    @staticmethod
    def rotate_point_around_origin(point_increments, angle_degrees):
        angle_radians = angle_degrees * math.pi / 180
        point_rotate = [0, 0]

        # Rotation counterclockwise:
        point_rotate[0] = math.cos(angle_radians) * point_increments[0] + math.sin(angle_radians) * point_increments[1]
        point_rotate[1] = -math.sin(angle_radians) * point_increments[0] + math.cos(angle_radians) * point_increments[1]
        return point_rotate

    def read_components(self):
        # Structure modules information:
        def search_text_between_string(first_string: str, second_string: str, line_string: str):
            regex_result = re.search(f"(?<={first_string})(.*?)(?={second_string})", line_string)
            if regex_result is not None:
                return regex_result.group(0)
            else:
                return None

        def check_element_layer(check_layer: list, line_string: str):
            layer = search_text_between_string(first_string="\\(layer ", second_string="\\)", line_string=line_string)
            if not layer:
                layer = search_text_between_string(first_string="\\(layers ", second_string="\\)",
                                                   line_string=line_string)
            return layer in check_layer

        pcb_data = FileOperations.read_file_lines(self.pcb_path)
        pcb_data_dictionary = {"borders": [],
                               "nets": {},
                               "vias": [],
                               "modules": {}}

        # Read and split kicad_pcb info in general and modules data:
        append_data = False
        modules_data = []
        for line_info in pcb_data:
            # Save PCB borders:
            if line_info[0:11] == "  (gr_line ":
                if check_element_layer(check_layer=self.borders_layers, line_string=line_info):
                    values_start = search_text_between_string(first_string="\\(start ", second_string="\\)",
                                                              line_string=line_info)
                    values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                            line_string=line_info)
                    if values_end is not None and values_start is not None:
                        start_point = [float(number) for number in values_start.split(" ")]
                        end_point = [float(number) for number in values_end.split(" ")]

                        # Read angle:
                        # angle = float(search_text_between_string(first_string="\\(angle ", second_string="\\)",
                        #                                          line_string=line_info))
                        angle = 0

                        # Rotate points before save them:
                        values_dict = {"start": self.rotate_point_around_origin(start_point, angle),
                                       "end": self.rotate_point_around_origin(end_point, angle)}
                        pcb_data_dictionary["borders"].append(values_dict)
                    else:
                        pcb_data_dictionary["borders"].append(None)

            # Save PCB nets:
            if line_info[0:7] == "  (net ":
                net_number = search_text_between_string(first_string='\\(net ', second_string=' ',
                                                        line_string=line_info)
                net_name = search_text_between_string(first_string='\\(net ' + net_number + ' "',
                                                      second_string='\\"\\)', line_string=line_info)
                if not net_name:
                    net_name = search_text_between_string(first_string='\\(net ' + net_number + ' ',
                                                          second_string='\\)', line_string=line_info)

                # Generate key data:
                if net_name == '\"\"':
                    net_name = ""
                pcb_data_dictionary["nets"][net_number] = net_name

            # Save PCB nets:
            if line_info[0:7] == "  (via ":
                if check_element_layer(check_layer=self.vias_layers, line_string=line_info):
                    values_point = search_text_between_string(first_string="\\(at ", second_string="\\)",
                                                              line_string=line_info)
                    if point is not None:
                        point = [float(number) for number in values_point.split(" ")]

                        # Read angle:
                        # angle = float(search_text_between_string(first_string="\\(angle ", second_string="\\)",
                        #                                          line_string=line_info))
                        angle = 0

                        # Rotate points before save them:
                        # TODO: add layer names to avoid filters in this section - it must be later, at processing stage
                        values_dict = {"position": self.rotate_point_around_origin(point, angle),
                                       "size": None,
                                       "drill": None,
                                       "net": None}    # TODO: read net name
                        pcb_data_dictionary["vias"].append(values_dict)
                    else:
                        pcb_data_dictionary["vias"].append(None)

            # Module starts with the string "  (module":
            if line_info[0:10] == "  (module ":
                append_data = True
                modules_data.append([])

            # If a module has been detected, the line must be appended in the corresponding group:
            if append_data:
                modules_data[-1].append(line_info)

                # Module finished with the line "  )":
                if line_info == "  )\n":
                    append_data = False

        for index, module_data in enumerate(modules_data):
            reference = f"Unknown_module_{index}"
            module_info = {"placement_outlines": {"circle": [],
                                                  "line": [],
                                                  "arc": []
                                                  },
                           "pads": {},
                           "rotation": 0
                           }
            pad_number = None
            for line_info in module_data:
                # Search module type and layer:
                if line_info[0:10] == "  (module ":
                    # Find module type:
                    module_info["type"] = search_text_between_string(first_string="module ", second_string=" \\(",
                                                                     line_string=line_info)
                    # Find module layer:
                    module_info["layer"] = search_text_between_string(first_string="layer ", second_string="\\)",
                                                                      line_string=line_info)

                # Search module reference:
                elif line_info[0:23] == "    (fp_text reference ":
                    reference = search_text_between_string(first_string="reference ", second_string=" \\(",
                                                           line_string=line_info)

                # Search origin coordinates:
                if line_info[0:8] == "    (at ":
                    module_info["position"] = search_text_between_string(first_string="\\(at ", second_string="\\)",
                                                                         line_string=line_info)
                    module_info["position"] = [float(number) for number in module_info["position"].split(" ")]
                    # Separate rotation from position:
                    if len(module_info["position"]) == 3:
                        module_info["rotation"] = module_info["position"][2]
                        module_info["position"] = module_info["position"][:2]

                # Search placement outline if it is in silkscreen layers:
                if check_element_layer(check_layer=self.placement_outlines_layers, line_string=line_info):
                    if line_info[0:15] == "    (fp_circle ":
                        values_center = search_text_between_string(first_string="\\(center ", second_string="\\)",
                                                                   line_string=line_info)
                        values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                                line_string=line_info)
                        if values_end is not None and values_center is not None:
                            center_point = [float(number) for number in values_center.split(" ")]
                            end_point = [float(number) for number in values_end.split(" ")]

                            # Rotate points before save them:
                            values_dict = {"center": self.rotate_point_around_origin(center_point, module_info["rotation"]),
                                           "end": self.rotate_point_around_origin(end_point, module_info["rotation"])}
                            module_info["placement_outlines"]["circle"].append(values_dict)
                        else:
                            module_info["placement_outlines"]["circle"].append(None)
                    elif line_info[0:12] == "    (fp_arc ":
                        values_start = search_text_between_string(first_string="\\(start ", second_string="\\)",
                                                                  line_string=line_info)
                        values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                                line_string=line_info)
                        values_angle = search_text_between_string(first_string="\\(angle ", second_string="\\)",
                                                                  line_string=line_info)
                        if values_start is not None and values_end is not None and values_angle is not None:
                            start_point = [float(number) for number in values_start.split(" ")]
                            end_point = [float(number) for number in values_end.split(" ")]
                            angle = float(values_angle)

                            # Rotate points before save them:
                            values_dict = {"start": self.rotate_point_around_origin(start_point, module_info["rotation"]),
                                           "end": self.rotate_point_around_origin(end_point, module_info["rotation"]),
                                           "angle": angle}
                            module_info["placement_outlines"]["arc"].append(values_dict)
                        else:
                            module_info["placement_outlines"]["arc"].append(None)
                    elif line_info[0:13] == "    (fp_line ":
                        values_start = search_text_between_string(first_string="\\(start ", second_string="\\)",
                                                                  line_string=line_info)
                        values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                                line_string=line_info)
                        if values_end is not None and values_start is not None:
                            start_point = [float(number) for number in values_start.split(" ")]
                            end_point = [float(number) for number in values_end.split(" ")]

                            # Rotate points before save them:
                            values_dict = {"start": self.rotate_point_around_origin(start_point,
                                                                                    module_info["rotation"]),
                                           "end": self.rotate_point_around_origin(end_point, module_info["rotation"])}
                            module_info["placement_outlines"]["line"].append(values_dict)
                        else:
                            module_info["placement_outlines"]["line"].append(None)

                # Search pad:
                if line_info[0:9] == "    (pad ":
                    # Check if pad is in a layer allowed:
                    if check_element_layer(check_layer=self.pads_layers, line_string=line_info):
                        simplified_line = search_text_between_string(first_string='\\(pad ', second_string=' \\(at',
                                                                     line_string=line_info)
                        split_line_info = simplified_line.split(" ")

                        pad_number = split_line_info[0]
                        if pad_number == '\"\"':
                            pad_number = "unknown"
                        module_info["pads"][pad_number] = {"type": split_line_info[1],
                                                           "shape": split_line_info[2]}

                        pad_position = search_text_between_string(first_string="\\(at ", second_string="\\)",
                                                                  line_string=line_info)
                        module_info["pads"][pad_number]["position"] = [float(number) for number in pad_position.split(" ")]
                        # Separate rotation from position:
                        if len(module_info["pads"][pad_number]["position"]) == 3:
                            rotation = module_info["pads"][pad_number]["position"][2]
                            position = module_info["pads"][pad_number]["position"][:2]
                            module_info["pads"][pad_number]["rotation"] = rotation
                            module_info["pads"][pad_number]["position"] = self.rotate_point_around_origin(position,
                                                                                                          rotation)
                        else:
                            module_info["pads"][pad_number]["rotation"] = 0

                        pad_size = search_text_between_string(first_string="\\(size ", second_string="\\)",
                                                              line_string=line_info)
                        module_info["pads"][pad_number]["size"] = [float(number) for number in pad_size.split(" ")]

                        pad_drill = search_text_between_string(first_string="\\(drill ", second_string="\\)",
                                                               line_string=line_info)
                        if pad_drill is not None:
                            module_info["pads"][pad_number]["drill"] = float(pad_drill)
                        else:
                            module_info["pads"][pad_number]["drill"] = None
                # Search nets pads:
                elif line_info[0:11] == "      (net ":
                    # Check if the net corresponds to a pad:
                    if pad_number in list(module_info["pads"].keys()):
                        net_name = search_text_between_string(first_string='net ', second_string='\\)',
                                                              line_string=line_info)
                        module_info["pads"][pad_number]["net_name"] = net_name
                else:
                    pad_number = None

            # Append data to global dictionary:
            pcb_data_dictionary["modules"][reference] = module_info
        return pcb_data_dictionary

    @staticmethod
    def pcb_dict_processor(pcb_data_dictionary):
        for module in pcb_data_dictionary["modules"].values():
            start_point = module["position"]

            for point in module["placement_outlines"]["line"]:
                point["start"][0] += start_point[0]
                point["end"][0] += start_point[0]
                point["start"][1] += start_point[1]
                point["end"][1] += start_point[1]

            for point in module["placement_outlines"]["circle"]:
                radius = math.sqrt((point["end"][0] - point["center"][0])**2 + (point["end"][1] - point["center"][1])**2)
                point["center"][0] += start_point[0]
                point["center"][1] += start_point[1]
                point["end"][0] = start_point[0] + radius
                point["end"][1] = start_point[1]

            for point in module["placement_outlines"]["arc"]:
                radius = math.sqrt((point["end"][0] - point["start"][0])**2 + (point["end"][1] - point["start"][1])**2)
                start_angle = math.atan2(point["start"][1], point["start"][0]) * 180 / math.pi
                end_angle = math.atan2(point["end"][1], point["end"][0]) * 180 / math.pi

                point["start"][0] += start_point[0]
                point["start"][1] += start_point[1]
                point["end"][0] = start_point[0]
                point["end"][1] = start_point[1]
                point["angles"] = [start_angle, end_angle]

            for pad_number, par_params in module["pads"].items():
                par_params["position"][0] += start_point[0]
                par_params["position"][1] += start_point[1]
        return pcb_data_dictionary

    def dataframe_constructor(self, pcb_data_dictionary):
        pcb_info_df = pd.DataFrame(columns=self.df_columns)

        return pcb_info_df


class PCBDrawing:
    def run(self, pcb_data):
        factor = 4
        image_obj = Image.new("RGB", (512 * factor, 512 * factor), (0, 0, 0))
        draw_obj = ImageDraw.Draw(image_obj)

        # Draw PCB general data:
        for line in pcb_data["borders"]:
            draw_obj.line((line["start"][0] * factor, line["start"][1] * factor,
                           line["end"][0] * factor, line["end"][1] * factor), fill=(255, 255, 0), width=1)

        # Draw modules:
        for module in pcb_data["modules"].values():
            start_point = module["position"]
            for point in module["placement_outlines"]["line"]:
                initial_x = point["start"][0] + start_point[0]
                final_x = point["end"][0] + start_point[0]
                initial_y = point["start"][1] + start_point[1]
                final_y = point["end"][1] + start_point[1]
                draw_obj.line((initial_x * factor, initial_y * factor, final_x * factor, final_y * factor),
                              fill=(255, 255, 255), width=1)
            for point in module["placement_outlines"]["circle"]:
                radius = math.sqrt((point["end"][0] - point["center"][0])**2 + (point["end"][1] - point["center"][1])**2)
                left_up_x = start_point[0] + point["center"][0] - radius
                left_up_y = start_point[1] + point["center"][1] - radius
                right_down_x = start_point[0] + point["center"][0] + radius
                right_down_y = start_point[1] + point["center"][1] + radius
                draw_obj.ellipse((left_up_x * factor, left_up_y * factor, right_down_x * factor, right_down_y * factor),
                                 fill=(255, 255, 255), width=1)
            for point in module["placement_outlines"]["arc"]:
                radius = math.sqrt((point["end"][0] - point["start"][0])**2 + (point["end"][1] - point["start"][1])**2)
                start_angle = math.atan2(point["start"][1], point["start"][0]) * 180 / math.pi
                end_angle = math.atan2(point["end"][1], point["end"][0]) * 180 / math.pi

                left_up_x = start_point[0] + point["start"][0] - radius
                left_up_y = start_point[1] + point["start"][1] - radius
                right_down_x = start_point[0] + point["start"][0] + radius
                right_down_y = start_point[1] + point["start"][1] + radius

                draw_obj.arc((left_up_x * factor, left_up_y * factor, right_down_x * factor, right_down_y * factor),
                             start=start_angle, end=end_angle, fill=(255, 255, 255), width=1)
            for pad_number, par_params in module["pads"].items():
                left_up_x = start_point[0] + par_params["position"][0] - par_params["size"][0]
                left_up_y = start_point[1] + par_params["position"][1] - par_params["size"][0]
                right_down_x = start_point[0] + par_params["position"][0] + par_params["size"][0]
                right_down_y = start_point[1] + par_params["position"][1] + par_params["size"][0]
                draw_obj.ellipse((left_up_x * factor, left_up_y * factor, right_down_x * factor, right_down_y * factor),
                                 fill=(255, 255, 0), width=0)

        image_obj.show()
        image_obj.save(ROOT_PATH + "//inputs//pcb_data.png")


if __name__ == "__main__":
    # METHOD 1:
    # file_path = ROOT_PATH + "//assets//PCB//pic_programmer//API_info//API_info_pcb.csv"
    # pcb_obj = PCBMapping(file_path)
    # info_df = pcb_obj.run()
    # print(info_df)

    # METHOD 2:
    pcb_obj = PCBMappingKiCAD()
    pcb_info = pcb_obj.read_components()
    pcb_info_processed = pcb_obj.pcb_dict_processor(pcb_info)
    pcb_obj.dataframe_constructor(pcb_info)
    # print(json.dumps(pcb_info, sort_keys=True, indent=4))
    with open(ROOT_PATH + "//inputs//pcb_data.json", 'w') as json_obj:
        json.dump(pcb_info_processed, json_obj, indent=4)

    # pcb_draw_obj = PCBDrawing()
    # pcb_draw_obj.run(pcb_info)
