#!/usr/bin/env python3
"""
Generate a complex redstone circuit based on an electronic differential amplifier design.
This translates the electronic circuit into Minecraft redstone components and exports it as a Structure NBT file.

The design includes:
- Multiple redstone torch stages (representing transistors)
- Redstone dust networks (representing wiring)
- Comparators for signal processing
- Repeaters for signal amplification
- Input/output connections

Output: camera.nbt (Structure NBT)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, List as TypingList, Optional, Tuple

import nbtlib
from nbtlib import Compound, Int, List, String


# Reasonable default for modern Java editions; structure blocks will upgrade on load.
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


def design_camera_circuit(builder: StructureBuilder) -> None:
    """Place a complex redstone circuit based on the electronic differential amplifier design."""
    
    # Foundation - larger base to accommodate the complex circuit
    for x in range(0, 12):
        for z in range(0, 8):
            builder.add_block(x, 0, z, 'minecraft:stone')
    
    # Layer 1: Base redstone components and wiring
    # Input section (left side)
    builder.add_block(1, 1, 1, 'minecraft:stone_button', {'face': 'wall', 'facing': 'east', 'powered': 'false'})
    builder.add_block(1, 1, 2, 'minecraft:redstone_torch')
    builder.add_block(1, 1, 3, 'minecraft:redstone_wire')
    
    # First stage - differential pair representation
    builder.add_block(3, 1, 1, 'minecraft:redstone_torch')
    builder.add_block(3, 1, 3, 'minecraft:redstone_torch')
    builder.add_block(3, 1, 2, 'minecraft:redstone_wire')
    
    # Second stage - amplification
    builder.add_block(5, 1, 1, 'minecraft:comparator', {'facing': 'east', 'mode': 'compare', 'powered': 'false'})
    builder.add_block(5, 1, 3, 'minecraft:comparator', {'facing': 'east', 'mode': 'compare', 'powered': 'false'})
    builder.add_block(5, 1, 2, 'minecraft:redstone_wire')
    
    # Third stage - output transistors representation
    builder.add_block(7, 1, 1, 'minecraft:redstone_torch')
    builder.add_block(7, 1, 3, 'minecraft:redstone_torch')
    builder.add_block(7, 1, 2, 'minecraft:redstone_wire')
    
    # Output section (right side)
    builder.add_block(9, 1, 1, 'minecraft:redstone_lamp')
    builder.add_block(9, 1, 3, 'minecraft:redstone_lamp')
    builder.add_block(9, 1, 2, 'minecraft:redstone_wire')
    
    # Layer 2: Upper circuit elements (representing the stacked transistors)
    # Top left stacked transistors
    builder.add_block(2, 2, 1, 'minecraft:redstone_torch')
    builder.add_block(2, 2, 3, 'minecraft:redstone_torch')
    builder.add_block(2, 2, 2, 'minecraft:redstone_wire')
    
    # Top right stacked transistors
    builder.add_block(8, 2, 1, 'minecraft:redstone_torch')
    builder.add_block(8, 2, 3, 'minecraft:redstone_torch')
    builder.add_block(8, 2, 2, 'minecraft:redstone_wire')
    
    # Layer 3: Control and feedback network
    # Current mirror representation (middle section)
    builder.add_block(4, 3, 1, 'minecraft:redstone_torch')
    builder.add_block(4, 3, 3, 'minecraft:redstone_torch')
    builder.add_block(4, 3, 2, 'minecraft:redstone_wire')
    
    # Feedback network
    builder.add_block(6, 3, 1, 'minecraft:repeater', {'facing': 'west', 'delay': '1', 'locked': 'false', 'powered': 'false'})
    builder.add_block(6, 3, 3, 'minecraft:repeater', {'facing': 'west', 'delay': '1', 'locked': 'false', 'powered': 'false'})
    builder.add_block(6, 3, 2, 'minecraft:redstone_wire')
    
    # Additional wiring connections
    # Horizontal connections
    for x in range(2, 10):
        builder.add_block(x, 1, 4, 'minecraft:redstone_wire')
        builder.add_block(x, 1, 5, 'minecraft:redstone_wire')
    
    # Vertical connections
    for z in range(1, 6):
        builder.add_block(4, 1, z, 'minecraft:redstone_wire')
        builder.add_block(6, 1, z, 'minecraft:redstone_wire')
    
    # Cross connections
    builder.add_block(4, 1, 4, 'minecraft:redstone_wire')
    builder.add_block(6, 1, 4, 'minecraft:redstone_wire')
    
    # Input/output connections
    builder.add_block(0, 1, 2, 'minecraft:redstone_wire')  # Input
    builder.add_block(11, 1, 2, 'minecraft:redstone_wire')  # Output
    
    # Power distribution
    builder.add_block(5, 1, 6, 'minecraft:redstone_block')  # Power source
    builder.add_block(5, 1, 7, 'minecraft:redstone_wire')
    
    # Ground connections (represented by redstone dust going to stone)
    for x in [1, 3, 5, 7, 9]:
        builder.add_block(x, 1, 0, 'minecraft:redstone_wire')


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate a complex redstone camera circuit Structure NBT file.')
    parser.add_argument('-o', '--output', default='camera.nbt', help='Output .nbt filename (default: camera.nbt)')
    parser.add_argument('--no-gzip', action='store_true', help='Disable gzip compression (enabled by default)')
    parser.add_argument('--data-version', type=int, default=DEFAULT_DATA_VERSION, help=f'DataVersion integer (default: {DEFAULT_DATA_VERSION})')
    args = parser.parse_args()

    builder = StructureBuilder()
    design_camera_circuit(builder)

    nbt_file = builder.build(data_version=args.data_version)
    if args.no_gzip:
        nbt_file.save(args.output)
        print(f'Wrote camera circuit structure: {args.output} (gzip=False)')
    else:
        nbt_file.save(args.output, gzipped=True)
        print(f'Wrote camera circuit structure: {args.output} (gzip=True)')


if __name__ == '__main__':
    main()
