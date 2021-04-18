"""调整SSA字幕亮度。"""

from __future__ import annotations

import argparse
import os
import re
from tkinter import Tk, filedialog

import ass as ssa
import colour
import numpy as np
from colour.models import (RGB_COLOURSPACE_BT2020, RGB_COLOURSPACE_DCI_P3,
                           RGB_COLOURSPACE_sRGB)

D65_ILLUMINANT = RGB_COLOURSPACE_sRGB.whitepoint


def files_picker() -> list[str]:
    """询问用户并返回字幕文件"""
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilenames(filetypes=[('ASS files', '.ass .ssa'),
                                                  ('all files', '.*')])


def sRgbToHdr(source: tuple[int, int, int]) -> tuple[int, int, int]:
    """
    大致思路：先做gamma correction，然后转入XYZ。 在xyY内将Y的极值由sRGB亮度调为输出
    亮度，然后转回2020的RGB。
    args:
    colour -- (0-255, 0-255, 0-255)
    """
    if source == (0, 0, 0):
        return (0, 0, 0)

    args = parse_args()
    srgb_brightness = args.sub_brightness
    screen_brightness = args.output_brightness
    target_colourspace = RGB_COLOURSPACE_BT2020
    if args.colourspace == 'dcip3':
        target_colourspace = RGB_COLOURSPACE_DCI_P3

    normalized_source = np.array(source) / 255
    linear_source = colour.oetf_inverse(normalized_source, 'ITU-R BT.709')
    xyz = colour.RGB_to_XYZ(linear_source, RGB_COLOURSPACE_sRGB.whitepoint,
                            D65_ILLUMINANT,
                            RGB_COLOURSPACE_sRGB.matrix_RGB_to_XYZ)
    xyy = colour.XYZ_to_xyY(xyz)
    xyy[2] = xyy[2] * srgb_brightness / screen_brightness
    xyz = colour.xyY_to_XYZ(xyy)
    output = colour.XYZ_to_RGB(xyz, D65_ILLUMINANT,
                               target_colourspace.whitepoint,
                               target_colourspace.matrix_XYZ_to_RGB)
    output = colour.oetf(output, 'ITU-R BT.2100 PQ')
    output = np.trunc(output * 255)
    return (int(output[0]), int(output[1]), int(output[2]))


def transformColour(colour):
    rgb = (colour.r, colour.g, colour.b)
    transformed = sRgbToHdr(rgb)
    colour.r = transformed[0]
    colour.g = transformed[1]
    colour.b = transformed[2]


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
        (r, g, b) = sRgbToHdr((r, g, b))
        hex_colour = '{:02x}{:02x}{:02x}'.format(b, g, r)
        matches.append((start, end, hex_colour.upper()))

    for start, end, hex_colour in matches:
        line = line[:start] + hex_colour + line[end:]

    event.text = line


def ssaProcessor(fname: str):
    if not os.path.isfile(fname):
        print(f'文件不存在: {fname}')
        return

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
        print(f'写入 {output_fname}')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        '--sub-brightness',
                        metavar='val',
                        type=int,
                        help=("设置字幕最大亮度，纯白色字幕将被映射为该亮度。"
                              "(默认: %(default)s)"),
                        default=100)

    parser.add_argument('-o',
                        '--output-brightness',
                        metavar='val',
                        type=int,
                        help=("设置输出屏幕最大亮度。"
                              "(默认: %(default)s)"),
                        default=1000)
    parser.add_argument('-c',
                        '--colourspace',
                        metavar='{dcip3,bt2020}',
                        type=str,
                        help=('选择输出的色彩空间。可用值为 dcip3 和 bt2020。'
                              '(默认: %(default)s)'),
                        default='bt2020')

    parser.add_argument('-f',
                        '--file',
                        metavar='path',
                        type=str,
                        help=('输入字幕文件。可重复添加。'),
                        action='append')

    args = parser.parse_args()

    args.output_brightness

    return args


if __name__ == '__main__':
    args = parse_args()
    files = args.file
    if not files:
        files = files_picker()
    for f in files:
        ssaProcessor(f)

    input("按回车键退出……...")
