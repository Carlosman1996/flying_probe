import os
import pandas as pd
from kicad.pcbnew import Board
from kicad.pcbnew import Text
from utils import DataframeOperations


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class PCB:
    def __init__(self, pcb_path):
        if not os.path.isfile(pcb_path):
            raise Exception("KiCAD PCB file path cannot be found.")
        self.board = Board.from_file(pcb_path)

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


if __name__ == "__main__":
    file_path = "//usr//share//kicad//demos//pic_programmer//pic_programmer.kicad_pcb"
    pcb = PCB(file_path)

    vias_df = pcb.read_vias()
    DataframeOperations.save_csv(vias_df, "..\\assets\\PCB\\pic_programmer\\API_info\\vias_df.csv")
    tracks_df = pcb.read_tracks()
    DataframeOperations.save_csv(tracks_df, "..\\assets\\PCB\\pic_programmer\\API_info\\tracks_df.csv")
    texts_df = pcb.read_texts()
    DataframeOperations.save_csv(texts_df, "..\\assets\\PCB\\pic_programmer\\API_info\\texts_df.csv")
    modules_df = pcb.read_modules()
    DataframeOperations.save_csv(modules_df, "..\\assets\\PCB\\pic_programmer\\API_info\\modules_df.csv")
    zones_df = pcb.read_zones()
    DataframeOperations.save_csv(zones_df, "..\\assets\\PCB\\pic_programmer\\API_info\\zones_df.csv")
