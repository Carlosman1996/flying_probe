from __future__ import print_function

from kicad.pcbnew import Board
from kicad.pcbnew import Text


def list_pcb(board):
    print()
    print("LIST VIAS:")
    for via in board.vias:
        print(" * Via:   {} - {}/{}".format(via.position, via.drill, via.width))

    print()
    print("LIST TRACKS:")
    for track in board.tracks:
        print(" * Track: {} to {}, width {}".format(track.start, track.end, track.width))

    print()
    print("LIST DRAWINGS:")
    for drawing in board.drawings:
        if type(drawing) is Text:
            print("* Text:    '{}' at {}".format(drawing.text, drawing.position))
        else:
            print("* Drawing: {}".format(drawing))

    print()
    print("LIST MODULES:")
    for module in board.modules:
        print("* Module: {} at {}".format(module.reference, module.position))

    print()
    print("LIST ZONES:")
    for zone in board.zones:
        print("* Zone: '{}' with priority {}".format(zone.net.name, zone.priority))


if __name__ == "__main__":
    file_path = "C:\\Users\\cmmol\\OneDrive\\Desktop\\flying_probe\\docs\\pcb\\schematic_example\\GR_IO_Board-master\\GR_IO_Board.kicad_pcb"

    board = Board.from_file(file_path)

    list_pcb(board)
