#!/usr/bin/env python3
"""
Generate a simple redstone T flip-flop structure and export it as a Structure NBT file.

The design uses a classic hopper-dropper pair as the toggle storage and a comparator
as the readable output. A wall button is mounted on the side of the bottom dropper
as a simple input pulse source. The generated file can be loaded with a Structure Block.

Output: flip_flop.nbt (Structure NBT)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, List as TypingList, Optional, Tuple

import nbtlib
from nbtlib import Compound, Int, List, String


# Reasonable default for modern Java editions; structure blocks will upgrade on load.
# If you know your target version, override with --data-version.
DEFAULT_DATA_VERSION = 3700


@dataclass(frozen=True)
class BlockStateKey:
    name: str
    properties: Tuple[Tuple[str, str], ...]


class StructureBuilder:
    def __init__(self) -> None:
        self._palette: TypingList[Compound] = []
        self._palette_index: Dict[BlockStateKey, int] = {}
        self._blocks: TypingList[Compound] = []
        self._min_x = 10**9
        self._min_y = 10**9
        self._min_z = 10**9
        self._max_x = -10**9
        self._max_y = -10**9
        self._max_z = -10**9

    def add_block(self, x: int, y: int, z: int, name: str, properties: Optional[Dict[str, str]] = None, nbt: Optional[Compound] = None) -> None:
        key = BlockStateKey(name=name, properties=tuple(sorted((properties or {}).items())))
        if key not in self._palette_index:
            palette_entry = Compound({
                'Name': String(name),
            })
            if properties:
                palette_entry['Properties'] = Compound({k: String(v) for k, v in properties.items()})
            self._palette_index[key] = len(self._palette)
            self._palette.append(palette_entry)

        state_index = Int(self._palette_index[key])
        block_entry = Compound({
            'pos': List[Int]([Int(x), Int(y), Int(z)]),
            'state': state_index,
        })
        if nbt is not None:
            block_entry['nbt'] = nbt

        self._blocks.append(block_entry)
        self._track_bounds(x, y, z)

    def _track_bounds(self, x: int, y: int, z: int) -> None:
        self._min_x = min(self._min_x, x)
        self._min_y = min(self._min_y, y)
        self._min_z = min(self._min_z, z)
        self._max_x = max(self._max_x, x)
        self._max_y = max(self._max_y, y)
        self._max_z = max(self._max_z, z)

    def size(self) -> Tuple[int, int, int]:
        if self._max_x < self._min_x:
            return (0, 0, 0)
        return (
            (self._max_x - self._min_x + 1),
            (self._max_y - self._min_y + 1),
            (self._max_z - self._min_z + 1),
        )

    def translate_to_origin(self) -> None:
        """Shift all blocks so the minimum coordinate becomes (0,0,0)."""
        if self._max_x < self._min_x:
            return
        dx, dy, dz = -self._min_x, -self._min_y, -self._min_z
        for blk in self._blocks:
            px, py, pz = [int(v) for v in blk['pos']]
            blk['pos'] = List[Int]([Int(px + dx), Int(py + dy), Int(pz + dz)])
        self._max_x += dx
        self._max_y += dy
        self._max_z += dz
        self._min_x = 0
        self._min_y = 0
        self._min_z = 0

    def build(self, data_version: int) -> nbtlib.File:
        self.translate_to_origin()
        sx, sy, sz = self.size()
        root = Compound({
            'size': List[Int]([Int(sx), Int(sy), Int(sz)]),
            'palette': List[Compound](self._palette),
            'blocks': List[Compound](self._blocks),
            'entities': List[Compound]([]),
            'DataVersion': Int(int(data_version)),
        })
        return nbtlib.File(root)


def design_t_flip_flop(builder: StructureBuilder) -> None:
    """Place a compact hopper-dropper T flip-flop with a comparator output."""
    # Foundation
    for x in range(0, 6):
        for z in range(0, 3):
            builder.add_block(x, 0, z, 'minecraft:stone')

    # Storage: two droppers vertically stacked
    builder.add_block(1, 1, 1, 'minecraft:dropper', {'facing': 'up'})    # bottom
    builder.add_block(1, 2, 1, 'minecraft:dropper', {'facing': 'down'})  # top

    # Hopper feeding into the bottom dropper
    builder.add_block(2, 1, 1, 'minecraft:hopper', {'facing': 'west', 'enabled': 'true'})

    # Comparator reading the bottom dropper (output)
    builder.add_block(3, 1, 1, 'minecraft:comparator', {'facing': 'east', 'mode': 'compare', 'powered': 'false'})

    # Output indicator: redstone lamp one block further
    builder.add_block(4, 1, 1, 'minecraft:redstone_lamp')

    # Redstone dust to connect comparator output to the lamp
    builder.add_block(4, 1, 0, 'minecraft:redstone_wire')
    builder.add_block(4, 1, 2, 'minecraft:redstone_wire')
    builder.add_block(5, 1, 1, 'minecraft:redstone_wire')

    # Simple input: a wall-mounted stone button on the north face of the bottom dropper
    builder.add_block(1, 1, 0, 'minecraft:stone_button', {'face': 'wall', 'facing': 'north', 'powered': 'false'})


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate a simple redstone T flip-flop Structure NBT file.')
    parser.add_argument('-o', '--output', default='flip_flop.nbt', help='Output .nbt filename (default: flip_flop.nbt)')
    parser.add_argument('--gzip', action='store_true', help='Gzip-compress the NBT output (off by default)')
    parser.add_argument('--data-version', type=int, default=DEFAULT_DATA_VERSION, help=f'DataVersion integer (default: {DEFAULT_DATA_VERSION})')
    args = parser.parse_args()

    builder = StructureBuilder()
    design_t_flip_flop(builder)

    nbt_file = builder.build(data_version=args.data_version)
    if args.gzip:
        nbt_file.save(args.output, gzipped=True)
    else:
        nbt_file.save(args.output)
    print(f'Wrote structure: {args.output} (gzip={bool(args.gzip)})')


if __name__ == '__main__':
    main()


