#!/usr/bin/env python3

import argparse
import pathlib
import re
import zipfile

import imageio
import numpy as np

from . import mappings


GRID_ROWS = 21
GRID_COLS = 32

FONTS = [
    "_default12x12",
    "cogmind12x12_terminus",
    "cogmind14x14",
    "cogmind14x14_terminus",
    "cogmind14x14_vga",
    "cogmind16x16",
    "cogmind16x16_kaypro",
    "cogmind16x16_terminus",
    "cogmind16x16_verite_fat",
    "cogmind18x18",
    "cogmind18x18_terminus",
    "cogmind20x20",
    "cogmind24x24",
    "cogmind28x28",
    "cogmind32x32",
    "cogmind36x36",
    "cogmind36x36_2",
]


def grayscale(image):
    return image[:, :, 0]


def read_tiles(image):
    for row in np.array_split(image, GRID_ROWS):
        for tile in np.array_split(row, GRID_COLS, axis=1):
            yield tile


def check_key(tiles):
    for i in mappings.ASCII:
        tile = tiles[i]
        if not tile.any():
            print(f"Warning: Replacement tile {i} is empty")


def load_custom(font, directory):
    if not directory:
        return {}

    path = directory / font

    if not path.exists():
        return {}

    return {x.stem: grayscale(imageio.imread(x)) for x in path.iterdir()}


def render(args, image, tiles, custom):
    width = image.shape[0] // GRID_ROWS
    height = image.shape[1] // GRID_COLS

    def tile(i):
        if i in args.keep_code:
            return tiles[i]

        if args.multitile and i in mappings.MULTITILE_PARTS:
            size, x, y = mappings.MULTITILE_PARTS[i]
            char = mappings.REPLACEMENTS[i]
            tile = tiles[mappings.ASCII.inv[char]]
            scaled = np.kron(tile, np.ones((size, size), dtype=int))
            return scaled[y*height:(y+1)*height, x*width:(x+1)*width]
        elif i in mappings.REPLACEMENTS:
            char = mappings.REPLACEMENTS[i]
        elif i in mappings.ASCII:
            char = mappings.ASCII[i]
        else:
            print(f"Warning: Missing ASCII replacement for tile {i}")
            return tiles[i]

        if char in custom:
            return custom[char]

        if char is None or char in args.keep:
            return tiles[i]

        return tiles[mappings.ASCII.inv[char]]

    output = np.zeros_like(image)

    for i in range(len(tiles)):
        if not tiles[i].any():
            if i in mappings.REPLACEMENTS and mappings.REPLACEMENTS[i]:
                print("Warning: Not replacing empty tile {} with '{}'"
                      .format(i, mappings.REPLACEMENTS[i]))
            continue

        x = i % GRID_COLS
        y = i // GRID_COLS
        output[y*height:(y+1)*height, x*width:(x+1)*width] = tile(i)

    return output


def modify_tiles(args, data, font):
    image = grayscale(imageio.imread(data))
    tiles = list(read_tiles(image))
    check_key(tiles)
    custom = load_custom(font, args.custom)
    output = render(args, image, tiles, custom)
    return imageio.imwrite(imageio.RETURN_BYTES, output, format="png")


def main():
    parser = argparse.ArgumentParser(prog="cogmindmod")
    parser.add_argument("cogmind", type=pathlib.Path,
                        help="Path to Cogmind directory")
    parser.add_argument("--keep", action="append", default=[], metavar="CHAR",
                        help="ASCII character to keep as graphical tile")
    parser.add_argument("--keep-code", action="append", type=int, default=[],
                        metavar="CODE",
                        help="Tile number to keep as graphical tile")
    parser.add_argument("--multitile", action="store_true",
                        help="Enable multitile entity scaling")
    parser.add_argument("--custom", type=pathlib.Path, metavar="DIR",
                        help="Directory with custom tiles")
    args = parser.parse_args()

    main_file = args.cogmind / "cogmind.x"
    orig_file = args.cogmind / "cogmind.x.orig"

    try:
        with zipfile.ZipFile(main_file, "r") as main_zip:
            comment = main_zip.comment

        if comment != b"cogmindmod":
            print("Moving the original file to 'cogmind.x.orig...'")
            main_file.replace(orig_file)
    except IOError as e:
        print(f"Warning: {e.strerror}: {e.filename}")

    try:
        with zipfile.ZipFile(orig_file, "r") as zin, \
             zipfile.ZipFile(main_file, "w") as zout:
            zout.comment = b"cogmindmod"

            for item in zin.infolist():
                data = zin.read(item.filename)

                match = re.search("data/fonts/(.+).png", item.filename)
                if match and match[1] in FONTS:
                    data = modify_tiles(args, data, match[1])

                zout.writestr(item, data)
    except IOError as e:
        print(e)


if __name__ == "__main__":
    main()
