import math
import re
import json
from PIL import Image, ImageDraw
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
        self.modules_layers = ["top_layer", "bottom_layer"]

        # Dataframe:
        self.df_columns = ["type", "name", "layer", "net_name", "net_class", "drill", "diameters", "position",
                           "shape_lines", "shape_circles", "shape_arcs", "height"]

    @staticmethod
    def refer_point_to_origin(reference_point, particular_point, angle_degrees):
        angle_radians = angle_degrees * math.pi / 180
        point_rotate = [0, 0]

        # Rotation counterclockwise:
        point_rotate[0] = math.cos(angle_radians) * particular_point[0] + math.sin(angle_radians) * particular_point[1]
        point_rotate[1] = -math.sin(angle_radians) * particular_point[0] + math.cos(angle_radians) * particular_point[1]

        # Absolute point:
        absolute_point = [reference_point[0] + point_rotate[0], reference_point[1] + point_rotate[1]]
        return absolute_point

    def pcb_reader(self):
        # Structure modules information:
        def search_text_between_string(first_string: str, second_string: str, line_string: str):
            regex_result = re.search(f"(?<={first_string})(.*?)(?={second_string})", line_string)
            if regex_result is not None:
                return regex_result.group(0)
            else:
                return None

        def check_element_layer(line_string: str):
            layer = search_text_between_string(first_string="\\(layer ", second_string="\\)", line_string=line_string)
            if not layer:
                layer = search_text_between_string(first_string="\\(layers ", second_string="\\)",
                                                   line_string=line_string)
            return layer

        pcb_data = FileOperations.read_file_lines(self.pcb_path)
        pcb_data_dict = {"borders": [],
                         "nets": {},
                         "net_classes": {},
                         "vias": [],
                         "modules": {}}

        # TODO: refactor code

        # Read and split kicad_pcb info in general and modules data:
        append_modules_data = False
        append_netclasses_data = False
        netclass_name = None
        modules_data = []
        for line_info in pcb_data:
            # Save PCB borders:
            if line_info[0:11] == "  (gr_line ":
                layer_name = check_element_layer(line_string=line_info)
                if layer_name in self.borders_layers:
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
                        values_dict = {"layer": layer_name,
                                       "start": self.refer_point_to_origin([0, 0], start_point, angle),
                                       "end": self.refer_point_to_origin([0, 0], end_point, angle)}
                        pcb_data_dict["borders"].append(values_dict)
                    else:
                        pcb_data_dict["borders"].append(None)

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
                pcb_data_dict["nets"][net_number] = net_name

            # Save PCB nets classes
            if line_info[0:13] == "  (net_class ":
                netclass_name = search_text_between_string(first_string="\\(net_class ", second_string="\\ ",
                                                           line_string=line_info)
                pcb_data_dict["net_classes"][netclass_name] = {"via_size": None,
                                                               "via_drill": None,
                                                               "uvia_size": None,
                                                               "uvia_drill": None,
                                                               "nets": []}
                append_netclasses_data = True
            elif line_info[0:4] == "    " and append_netclasses_data:
                if line_info[0:13] == "    (via_dia ":
                    pcb_data_dict["net_classes"][netclass_name]["via_size"] = \
                        search_text_between_string(first_string="\\(via_dia ", second_string="\\)",
                                                   line_string=line_info)
                elif line_info[0:15] == "    (via_drill ":
                    pcb_data_dict["net_classes"][netclass_name]["via_drill"] = \
                        search_text_between_string(first_string="\\(via_drill ", second_string="\\)",
                                                   line_string=line_info)
                elif line_info[0:14] == "    (uvia_dia ":
                    pcb_data_dict["net_classes"][netclass_name]["uvia_size"] = \
                        search_text_between_string(first_string="\\(uvia_dia ", second_string="\\)",
                                                   line_string=line_info)
                elif line_info[0:15] == "    (uvia_drill ":
                    pcb_data_dict["net_classes"][netclass_name]["uvia_drill"] = \
                        search_text_between_string(first_string="\\(uvia_drill ", second_string="\\)",
                                                   line_string=line_info)
                elif line_info[0:13] == "    (add_net ":
                    net_name = search_text_between_string(first_string='\\(add_net "',
                                                          second_string='\\"\\)', line_string=line_info)
                    if not net_name:
                        net_name = search_text_between_string(first_string='\\(add_net ',
                                                              second_string='\\)', line_string=line_info)

                    pcb_data_dict["net_classes"][netclass_name]["nets"].append(net_name)
            elif line_info == "  )\n":
                netclass_name = None
                append_netclasses_data = False

            # Save PCB vias:
            if line_info[0:7] == "  (via ":
                layer_name = check_element_layer(line_string=line_info)
                if layer_name in self.vias_layers:
                    values_point = search_text_between_string(first_string="\\(at ", second_string="\\)",
                                                              line_string=line_info)
                    if values_point is not None:
                        point = [float(number) for number in values_point.split(" ")]

                        # Read angle:
                        # angle = float(search_text_between_string(first_string="\\(angle ", second_string="\\)",
                        #                                          line_string=line_info))
                        angle = 0

                        # Rotate points before save them:
                        values_dict = {"position": self.refer_point_to_origin([0, 0], point, angle),
                                       "layer": layer_name,
                                       "diameters": float(search_text_between_string(first_string="\\(size ",
                                                                                     second_string="\\)",
                                                                                     line_string=line_info)),
                                       "net": search_text_between_string(first_string="\\(net ", second_string="\\)",
                                                                         line_string=line_info)}
                        pcb_data_dict["vias"].append(values_dict)
                    else:
                        pcb_data_dict["vias"].append(None)

            # Module starts with the string "  (module":
            if line_info[0:10] == "  (module ":
                layer_name = check_element_layer(line_string=line_info)
                if layer_name in self.modules_layers:
                    append_modules_data = True
                    modules_data.append([])

            # If a module has been detected, the line must be appended in the corresponding group:
            if append_modules_data:
                modules_data[-1].append(line_info)

                # Module finished with the line "  )":
                if line_info == "  )\n":
                    append_modules_data = False

        for index, module_data in enumerate(modules_data):
            reference = f"Unknown_module_{index}"
            module_info = {"placement_outlines": {"circles": [],
                                                  "lines": [],
                                                  "arcs": []
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
                    start_point_string = search_text_between_string(first_string="\\(at ", second_string="\\)",
                                                                    line_string=line_info)
                    module_info["position"] = [float(number) for number in start_point_string.split(" ")]
                    # Separate rotation from position:
                    if len(module_info["position"]) == 3:
                        module_info["rotation"] = module_info["position"][2]
                        module_info["position"] = module_info["position"][:2]

                # Search placement outline if it is in silkscreen layers:
                if line_info[0:15] == "    (fp_circle ":
                    layer_name = check_element_layer(line_string=line_info)
                    if layer_name in self.placement_outlines_layers:
                        values_center = search_text_between_string(first_string="\\(center ", second_string="\\)",
                                                                   line_string=line_info)
                        values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                                line_string=line_info)
                        if values_end is not None and values_center is not None:
                            relative_center_point = [float(number) for number in values_center.split(" ")]
                            relative_end_point = [float(number) for number in values_end.split(" ")]
                            center_point = self.refer_point_to_origin(module_info["position"], relative_center_point,
                                                                      module_info["rotation"])
                            end_point = self.refer_point_to_origin(module_info["position"], relative_end_point,
                                                                   module_info["rotation"])

                            radius = math.sqrt((end_point[0] - center_point[0]) ** 2 + (end_point[1] - center_point[1]) ** 2)

                            # Rotate points before save them:
                            values_dict = {"layer": layer_name,
                                           "center": center_point,
                                           "radius": radius}
                            module_info["placement_outlines"]["circles"].append(values_dict)
                        else:
                            module_info["placement_outlines"]["circles"].append(None)
                elif line_info[0:12] == "    (fp_arc ":
                    layer_name = check_element_layer(line_string=line_info)
                    if layer_name in self.placement_outlines_layers:
                        values_start = search_text_between_string(first_string="\\(start ", second_string="\\)",
                                                                  line_string=line_info)
                        values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                                line_string=line_info)
                        values_angle = search_text_between_string(first_string="\\(angle ", second_string="\\)",
                                                                  line_string=line_info)
                        if values_start is not None and values_end is not None and values_angle is not None:
                            relative_start_point = [float(number) for number in values_start.split(" ")]
                            relative_end_point = [float(number) for number in values_end.split(" ")]

                            start_point = self.refer_point_to_origin(module_info["position"], relative_start_point,
                                                                     module_info["rotation"])
                            end_point = self.refer_point_to_origin(module_info["position"], relative_end_point,
                                                                   module_info["rotation"])

                            radius = math.sqrt((end_point[0] - start_point[0]) ** 2 + (end_point[1] - start_point[1]) ** 2)
                            start_angle = math.atan2(start_point[1], start_point[0]) * 180 / math.pi
                            end_angle = math.atan2(end_point[1], end_point[0]) * 180 / math.pi

                            # Rotate points before save them:
                            values_dict = {"layer": layer_name,
                                           "start": start_point,
                                           "end": end_point,
                                           "radius": radius,
                                           "angles": [start_angle, end_angle]}
                            module_info["placement_outlines"]["arcs"].append(values_dict)
                        else:
                            module_info["placement_outlines"]["arcs"].append(None)
                elif line_info[0:13] == "    (fp_line ":
                    layer_name = check_element_layer(line_string=line_info)
                    if layer_name in self.placement_outlines_layers:
                        values_start = search_text_between_string(first_string="\\(start ", second_string="\\)",
                                                                  line_string=line_info)
                        values_end = search_text_between_string(first_string="\\(end ", second_string="\\)",
                                                                line_string=line_info)
                        if values_end is not None and values_start is not None:
                            start_point = [float(number) for number in values_start.split(" ")]
                            end_point = [float(number) for number in values_end.split(" ")]

                            # Rotate points before save them:
                            values_dict = {"layer": layer_name,
                                           "start": self.refer_point_to_origin(module_info["position"], start_point,
                                                                               module_info["rotation"]),
                                           "end": self.refer_point_to_origin(module_info["position"], end_point,
                                                                             module_info["rotation"])}
                            module_info["placement_outlines"]["lines"].append(values_dict)
                        else:
                            module_info["placement_outlines"]["lines"].append(None)

                # Search pad:
                if line_info[0:9] == "    (pad ":
                    layer_name = check_element_layer(line_string=line_info)
                    if layer_name in self.pads_layers:
                        simplified_line = search_text_between_string(first_string='\\(pad ', second_string=' \\(at',
                                                                     line_string=line_info)
                        split_line_info = simplified_line.split(" ")

                        pad_number = split_line_info[0]
                        if pad_number == '\"\"':
                            pad_number = "unknown"
                        module_info["pads"][str(pad_number)] = {"layer": layer_name,
                                                                "type": split_line_info[1],
                                                                "shape": split_line_info[2]}

                        pad_position_string = search_text_between_string(first_string="\\(at ", second_string="\\)",
                                                                         line_string=line_info)
                        pad_position = [float(number) for number in pad_position_string.split(" ")]
                        # Separate rotation from position:
                        if len(pad_position) == 3:
                            position = pad_position[:2]
                            rotation = pad_position[2]
                        else:
                            position = pad_position
                            rotation = 0
                        module_info["pads"][pad_number]["position"] = \
                            self.refer_point_to_origin(module_info["position"], position, rotation)
                        module_info["pads"][pad_number]["rotation"] = rotation

                        pad_size = search_text_between_string(first_string="\\(size ", second_string="\\)",
                                                              line_string=line_info)
                        module_info["pads"][pad_number]["diameters"] = [float(number) for number in pad_size.split(" ")]

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
            pcb_data_dict["modules"][reference] = module_info
        return pcb_data_dict

    def dataframe_constructor(self, pcb_data_dict):
        pcb_info_df = pd.DataFrame(columns=self.df_columns)

        def append_dict_in_df(data_df, element_type="", name="", layer="", net_name="", net_class="", drill=None,
                              diameters=None, position=None, shape_lines=None, shape_circles=None, shape_arcs=None,
                              height=0):
            data_df = data_df.append({"type": element_type,
                                      "name": name,
                                      "layer": layer,
                                      "net_name": net_name,
                                      "net_class": net_class,
                                      "drill": drill,
                                      "diameters": diameters,
                                      "position": position,
                                      "shape_lines": shape_lines if shape_lines else [],
                                      "shape_circles": shape_circles if shape_circles else [],
                                      "shape_arcs": shape_arcs if shape_arcs else [],
                                      "height": height},
                                     ignore_index=True)
            return data_df

        # Restructure borders information:
        border_per_layer = {}
        for border in pcb_data_dict["borders"]:
            if border["layer"] not in list(border_per_layer.keys()):
                border_per_layer[border["layer"]] = [border["start"], border["end"]]
            else:
                border_per_layer[border["layer"]].append(border["start"])
                border_per_layer[border["layer"]].append(border["end"])

        # Append borders information:
        for layer_name, shape in border_per_layer.items():
            pcb_info_df = append_dict_in_df(pcb_info_df,
                                            element_type="border",
                                            layer=layer_name,
                                            shape_lines=shape)

        # Restructure nets information:
        for net_key, net_name in pcb_data_dict["nets"].items():
            for net_class_key, net_class_values in pcb_data_dict["net_classes"].items():
                if net_name in net_class_values["nets"]:
                    pcb_data_dict["nets"][net_key] = {"name": net_name,
                                                      "net_class": net_class_key}

        # Append vias information:
        for via_info in pcb_data_dict["vias"]:
            net_name = pcb_data_dict["nets"][via_info["net"]]["name"]
            net_class = pcb_data_dict["nets"][via_info["net"]]["net_class"]
            drill = pcb_data_dict["net_classes"][net_class]["via_drill"]
            pcb_info_df = append_dict_in_df(pcb_info_df,
                                            element_type="via",
                                            layer=via_info["layer"],
                                            net_name=net_name,
                                            net_class=net_class,
                                            drill=drill,
                                            diameters=via_info["diameters"],
                                            position=via_info["position"])

        # Append components information:
        for module_key, module_info in pcb_data_dict["modules"].items():
            # TODO: join all information in one list -
            # Create lines list:
            line_list = []
            for line in module_info["placement_outlines"]["lines"]:
                line_list.append(line["start"])
                line_list.append(line["end"])

            # Create circles list:
            circles_list = []
            for circle in module_info["placement_outlines"]["circles"]:
                circles_list.append({"center": circle["center"],
                                     "radius": circle["radius"]})

            # Create circles list:
            arcs_list = []
            for arc in module_info["placement_outlines"]["arcs"]:
                arcs_list.append({"start": arc["start"],
                                  "end": arc["end"],
                                  "radius": arc["radius"],
                                  "angles": arc["angles"]})

            # Append modules information:
            pcb_info_df = append_dict_in_df(pcb_info_df,
                                            element_type="module",
                                            name=module_key,
                                            layer=module_info["layer"],
                                            position=module_info["position"],
                                            shape_lines=line_list,
                                            shape_circles=circles_list,
                                            shape_arcs=arcs_list,
                                            height=0)

            # Append pads information:
            for pad_key, pad_info in module_info["pads"].items():
                # Get shape type:
                if pad_info["shape"] in ["circle", "oval"]:
                    diameters = pad_info["diameters"]
                else:
                    diameters = None
                if pad_info["shape"] == "rect":
                    dx = pad_info["diameters"][0] / 2
                    dy = pad_info["diameters"][1] / 2
                    shape_lines = [[pad_info["position"][0] + dx, pad_info["position"][1] + dy],
                                   [pad_info["position"][0] - dx, pad_info["position"][1] + dy],
                                   [pad_info["position"][0] - dx, pad_info["position"][1] + dy],
                                   [pad_info["position"][0] - dx, pad_info["position"][1] - dy],
                                   [pad_info["position"][0] - dx, pad_info["position"][1] - dy],
                                   [pad_info["position"][0] + dx, pad_info["position"][1] - dy],
                                   [pad_info["position"][0] + dx, pad_info["position"][1] - dy],
                                   [pad_info["position"][0] + dx, pad_info["position"][1] + dy]]
                else:
                    shape_lines = None

                # Get net names:
                if "net_name" in list(pad_info.keys()):
                    net_id = str(pad_info["net_name"].split(" ")[0])
                    net_name = pcb_data_dict["nets"][net_id]["name"]
                    net_class = pcb_data_dict["nets"][net_id]["net_class"]
                else:
                    net_name = None
                    net_class = None

                pcb_info_df = append_dict_in_df(pcb_info_df,
                                                element_type="pad",
                                                name=module_key + "_pad_" + pad_key,
                                                layer=pad_info["layer"],
                                                net_name=net_name,
                                                net_class=net_class,
                                                drill=pad_info["drill"],
                                                diameters=diameters,
                                                position=pad_info["position"],
                                                shape_lines=shape_lines)

        return pcb_info_df

    def run(self):
        pcb_data_dict = self.pcb_reader()
        pcb_data_df = self.dataframe_constructor(pcb_data_dict)
        return pcb_data_df


class PCBDrawing:
    @staticmethod
    def draw_lines(draw_obj, shape_points, factor=1):
        line_index = 0
        for _ in range(0, int(len(shape_points) / 2)):
            current_point = shape_points[line_index]
            next_point = shape_points[line_index + 1]
            line_index += 2

            draw_obj.line((current_point[0] * factor, current_point[1] * factor,
                           next_point[0] * factor, next_point[1] * factor),
                          fill=(255, 255, 0), width=1)

    @staticmethod
    def draw_ellipse(draw_obj, center, size, factor=1):
        if type(size) == list:
            x_size = size[0]
            y_size = size[1]
        else:
            x_size = size
            y_size = size
        left_up_x = center[0] - x_size
        left_up_y = center[1] - y_size
        right_down_x = center[0] + x_size
        right_down_y = center[1] + y_size
        draw_obj.ellipse((left_up_x * factor, left_up_y * factor, right_down_x * factor, right_down_y * factor),
                         fill=(255, 255, 0), width=1)

    @staticmethod
    def draw_arc(draw_obj, start, angles, radius, factor=1):
        left_up_x = start[0] - radius
        left_up_y = start[1] - radius
        right_down_x = start[0] + radius
        right_down_y = start[1] + radius
        draw_obj.arc((left_up_x * factor, left_up_y * factor, right_down_x * factor, right_down_y * factor),
                     start=angles[0], end=angles[1], fill=(255, 255, 255), width=1)

    def run(self, pcb_data):
        factor = 4
        image_obj = Image.new("RGB", (512 * factor, 512 * factor), (0, 0, 0))
        draw_obj = ImageDraw.Draw(image_obj)

        # Iterate over all dataframe rows:
        for index, pcb_element in pcb_data.iterrows():
            # Draw PCB general data:
            if pcb_element.type == "border":
                self.draw_lines(draw_obj, pcb_element.shape_lines, factor)

            # Draw via:
            if pcb_element.type == "via":
                self.draw_ellipse(draw_obj, pcb_element.position, pcb_element.diameters, factor)

            # Draw pad:
            if pcb_element.type == "pad":
                if pcb_element.diameters is None:
                    # Rectangular pad:
                    self.draw_lines(draw_obj, pcb_element.shape_lines, factor)
                else:
                    # Circular pad:
                    self.draw_ellipse(draw_obj, pcb_element.position, pcb_element.diameters, factor)

            # Draw module placement outlines:
            if pcb_element.type == "module":
                if pcb_element.shape_lines is not None:
                    self.draw_lines(draw_obj, pcb_element.shape_lines, factor)
                if pcb_element.shape_circles is not None:
                    for circle in pcb_element.shape_circles:
                        self.draw_ellipse(draw_obj, circle["center"], circle["radius"], factor)
                if pcb_element.shape_arcs is not None:
                    for arc in pcb_element.shape_arcs:
                        self.draw_arc(draw_obj, arc["start"], arc["angles"], arc["radius"], factor)

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
    pcb_info = pcb_obj.pcb_reader()
    pcb_df = pcb_obj.dataframe_constructor(pcb_info)

    with open(ROOT_PATH + "//inputs//pcb_data.json", 'w') as json_obj:
        json.dump(pcb_info, json_obj, indent=4)
    DataframeOperations.save_csv(ROOT_PATH + "//inputs//pcb_data.csv", pcb_df)

    pcb_draw_obj = PCBDrawing()
    pcb_draw_obj.run(pcb_df)
