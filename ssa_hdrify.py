from __future__ import annotations

import re
import os
import ass as ssa
import colour
from tkinter import Tk, filedialog
from colour.models import RGB_COLOURSPACE_sRGB, RGB_COLOURSPACE_BT2020, RGB_COLOURSPACE_DCI_P3
import numpy as np

SRGB_PEAK_BRIGHTNESS = 120
SCREEN_PEAK_BRIGHTNESS = 1000
D65_ILLUMINANT = RGB_COLOURSPACE_sRGB.whitepoint

def file_picker() -> str:
    """询问用户并返回一个文件夹"""
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilename()


def sRgbToBt2020(source:tuple[int,int,int]) -> tuple[int,int,int]:
    """
    大致思路：先做gamma correction，然后转入XYZ。 在xyY内将Y的极值由sRGB亮度调为输出
    亮度，然后转回2020的RGB。
    args:
    colour -- (0-255, 0-255, 0-255)
    """
    source = np.array(source)
    source = source / 255
    source = colour.oetf_inverse(source, 'ITU-R BT.709')
    xyz = colour.RGB_to_XYZ(
        source,
        RGB_COLOURSPACE_sRGB.whitepoint,
        D65_ILLUMINANT,
        RGB_COLOURSPACE_sRGB.matrix_RGB_to_XYZ)
    xyy = colour.XYZ_to_xyY(xyz)
    xyy[2] = xyy[2] * SRGB_PEAK_BRIGHTNESS / SCREEN_PEAK_BRIGHTNESS
    xyz = colour.xyY_to_XYZ(xyy)
    output = colour.XYZ_to_RGB(
        xyz,
        D65_ILLUMINANT,
        RGB_COLOURSPACE_BT2020.whitepoint,
        RGB_COLOURSPACE_BT2020.matrix_XYZ_to_RGB)
    output = colour.oetf(output, 'ITU-R BT.2100 PQ')
    output = np.trunc(output * 255)
    return (int(output[0]), int(output[1]), int(output[2]))

def transformColour(colour: ssa.data.Color):
    rgb = (colour.r, colour.g, colour.b)
    transformed = sRgbToBt2020(rgb)
    colour.r = transformed[0]
    colour.g = transformed[1]
    colour.b = transformed[2]

    print(f'process {rgb}, output {transformed}')

def transformEvent(event):
    line = event.text
    matches = []
    for match in re.finditer(r'\\[0-9]?c&H([0-9a-fA-F]{2,})&', line):
        start = match.start(1)
        end = match.end(1)
        hex_colour = match.group(1)
        hex_colour.rjust(6, '0')
        b = int(hex_colour[0:2], 16)
        g = int(hex_colour[2:4], 16)
        r = int(hex_colour[4:6], 16)
        (r,g,b) = sRgbToBt2020((r,g,b))
        hex_colour = '{:02x}{:02x}{:02x}'.format(b, g, r)
        matches.append((start, end, hex_colour.upper()))

    for start,end,hex_colour in matches:
        line = line[:start] + hex_colour + line[end:]

    event.text = line

def ssaProcessor(fname:str):
    with open(fname, encoding='utf_8_sig') as f:
        sub = ssa.parse(f)
    for s in sub.styles:
        transformColour(s.primary_color)
        transformColour(s.secondary_color)
        transformColour(s.outline_color)
        transformColour(s.back_color)

    for e in sub.events:
        transformEvent(e)

    output_fname = os.path.splitext(fname)
    output_fname = output_fname[0] + '.hdr.ass'

    with open(output_fname, 'w', encoding='utf_8_sig') as f:
        sub.dump_file(f)

if __name__ == '__main__':
    ssaProcessor(file_picker())
