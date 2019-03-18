#!/usr/bin/env python3

import argparse
import pathlib

import imageio
import numpy as np

from . import mappings


GRID_ROWS = 21
GRID_COLS = 32


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


def load_custom(args):
    custom = {}

    if args.custom:
        for tile in args.custom.iterdir():
            custom[tile.stem] = grayscale(imageio.imread(tile))

    return custom


def render(args, image, tiles, custom):
    def tile(i):
        if i in args.keep_code:
            return tiles[i]

        if i in mappings.REPLACEMENTS:
            char = mappings.REPLACEMENTS[i]
        elif i in mappings.ASCII:
            char = mappings.ASCII[i]
        else:
            print(f"Warning: Missing ASCII replacement for tile {i}")
            return tiles[i]

        if char in custom:
            return custom[char]

        if char in args.keep:
            return tiles[i]

        return tiles[mappings.ASCII.inv[char]]

    width = image.shape[0] // GRID_ROWS
    height = image.shape[1] // GRID_COLS

    output = np.zeros_like(image)

    for i in range(len(tiles)):
        if not tiles[i].any():
            if i in mappings.REPLACEMENTS:
                print("Warning: Not replacing empty tile {} with '{}'"
                      .format(i, mappings.REPLACEMENTS[i]))
            continue

        x = i % GRID_COLS
        y = i // GRID_COLS
        output[y*height:(y+1)*height, x*width:(x+1)*width] = tile(i)

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("output")
    parser.add_argument("--keep", action="append", default=[],
                        help="ASCII character to keep as graphical tile")
    parser.add_argument("--keep-code", action="append", type=int, default=[],
                        help="Tile number to keep as graphical tile")
    parser.add_argument("--custom", type=pathlib.Path,
                        help="Directory with custom tiles")
    args = parser.parse_args()

    image = grayscale(imageio.imread(args.image))
    tiles = list(read_tiles(image))
    check_key(tiles)
    custom = load_custom(args)

    output = render(args, image, tiles, custom)
    imageio.imwrite(args.output, output)


if __name__ == "__main__":
    main()
