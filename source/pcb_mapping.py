import re
import json
import pandas as pd
from pandas.api.types import is_numeric_dtype

from source.utils import ROOT_PATH
from source.utils import FileOperations
from source.utils import DataframeOperations


pd.set_option('display.max_rows', None, 'display.max_columns', None)


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class PCBMapping:
    def __init__(self, pcb_path=ROOT_PATH + "//inputs//pcb_file.kicad_pcb"):
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

    def read_components(self):
        pcb_data = FileOperations.read_file_lines(self.pcb_path)

        # Read and split modules:
        append_data = False
        modules_data = []
        for line in pcb_data:
            # Module starts with the string "  (module":
            if line[0:9] == "  (module":
                append_data = True
                modules_data.append([])

            # If a module has been detected, the line must be appended in the corresponding group:
            if append_data:
                modules_data[-1].append(line)

                # Module finished with the line "  )":
                if line == "  )\n":
                    append_data = False

        # Structure modules information:
        def search_text_between_string(first_string, second_string):
            regex_result = re.search(f"(?<={first_string})(.*?)(?={second_string})", line_info)
            if regex_result is not None:
                return regex_result.group(0)
            else:
                return None

        modules = {}
        for index, module_data in enumerate(modules_data):
            reference = f"Unknown_module_{index}"
            module_info = {"placement_outlines": {"circle": [],
                                                  "line": {}
                                                  }
                           }
            for line_info in module_data:
                # Search module type and layer:
                if "module" in line_info:
                    # Find module type:
                    module_info["type"] = search_text_between_string(first_string="module ", second_string=" \(")
                    # Find module layer:
                    module_info["layer"] = search_text_between_string(first_string="layer ", second_string="\)")

                # Search module reference:
                elif "reference" in line_info:
                    reference = search_text_between_string(first_string="reference ", second_string=" \(")

                # Search origin coordinates:
                if line_info[0:8] == "    (at ":
                    module_info["position"] = search_text_between_string(first_string="\(at ", second_string="\)")
                    module_info["position"] = [float(number) for number in module_info["position"].split(" ")]

                # Search placement outlines:
                if line_info[0:15] == "    (fp_circle ":
                    values_center = search_text_between_string(first_string="\(center ", second_string="\)")
                    values_end = search_text_between_string(first_string="\(end ", second_string="\)")
                    if values_end is not None and values_center is not None:
                        values_dict = {"center": [float(number) for number in values_center.split(" ")],
                                       "end": [float(number) for number in values_end.split(" ")]}
                        module_info["placement_outlines"]["circle"].append(values_dict)
                    else:
                        module_info["placement_outlines"]["circle"].append(None)

            # Append data to global dictionary:
            print(reference, module_info)
            modules[reference] = module_info
        print(len(modules.keys()), modules)


if __name__ == "__main__":
    # file_path = ROOT_PATH + "//assets//PCB//pic_programmer//API_info//API_info_pcb.csv"
    # pcb_obj = PCBMapping(file_path)
    # info_df = pcb_obj.run()
    # print(info_df)
    pcb_obj = PCBMappingKiCAD()
    pcb_obj.read_components()
