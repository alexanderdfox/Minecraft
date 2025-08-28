#!/usr/bin/env python3
"""
Convert a PNG image into a Minecraft redstone structure (.nbt) and optionally
package it as a datapack that places the structure via a summonable function.

Usage examples:
  - Basic NBT export from image:
      png_to_redstone.py circuit.png -o circuit.nbt

  - With a custom legend:
      png_to_redstone.py circuit.png --legend legend.json -o circuit.nbt

  - Export as datapack (plugin-like) that places the structure at player:
      png_to_redstone.py circuit.png --datapack out_pack --namespace mypack --pack-name "PNG Circuits"

Legend format (JSON):
  {
    "#ff0000": {"name": "minecraft:redstone_wire"},
    "#00ff00": {"name": "minecraft:repeater", "properties": {"facing": "east", "delay": "1"}},
    "#0000ff": {"name": "minecraft:redstone_torch"}
  }
Colors not in legend are treated as air by default (skipped).
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, List as TypingList, Optional, Tuple

from PIL import Image
import nbtlib
from nbtlib import Compound, Int, List, String


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

    def add_block(self, x: int, y: int, z: int, name: str, properties: Optional[Dict[str, str]] = None) -> None:
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
        self._blocks.append(block_entry)

    def build(self, data_version: int) -> nbtlib.File:
        # Compute size automatically from placed blocks; translate to origin.
        if not self._blocks:
            root = Compound({
                'size': List[Int]([Int(0), Int(0), Int(0)]),
                'palette': List[Compound](self._palette),
                'blocks': List[Compound]([]),
                'entities': List[Compound]([]),
                'DataVersion': Int(int(data_version)),
            })
            return nbtlib.File(root)

        min_x = min(int(b['pos'][0]) for b in self._blocks)
        min_y = min(int(b['pos'][1]) for b in self._blocks)
        min_z = min(int(b['pos'][2]) for b in self._blocks)
        # translate
        for blk in self._blocks:
            px, py, pz = [int(v) for v in blk['pos']]
            blk['pos'] = List[Int]([Int(px - min_x), Int(py - min_y), Int(pz - min_z)])
        max_x = max(int(b['pos'][0]) for b in self._blocks)
        max_y = max(int(b['pos'][1]) for b in self._blocks)
        max_z = max(int(b['pos'][2]) for b in self._blocks)
        sx = max_x + 1
        sy = max_y + 1
        sz = max_z + 1

        root = Compound({
            'size': List[Int]([Int(sx), Int(sy), Int(sz)]),
            'palette': List[Compound](self._palette),
            'blocks': List[Compound](self._blocks),
            'entities': List[Compound]([]),
            'DataVersion': Int(int(data_version)),
        })
        return nbtlib.File(root)


def parse_legend(path: Optional[str]) -> Dict[Tuple[int, int, int, int], Dict[str, object]]:
    """Return mapping from RGBA tuple to block spec dict.
    Block spec dict has keys: name (str), optional properties (dict[str,str]).
    """
    default_legend: Dict[Tuple[int, int, int, int], Dict[str, object]] = {
        (255, 0, 0, 255): {"name": "minecraft:redstone_wire"},
        (0, 255, 0, 255): {"name": "minecraft:repeater", "properties": {"facing": "east", "delay": "1", "locked": "false", "powered": "false"}},
        (0, 0, 255, 255): {"name": "minecraft:redstone_torch"},
        (255, 255, 0, 255): {"name": "minecraft:comparator", "properties": {"facing": "east", "mode": "compare", "powered": "false"}},
        (0, 0, 0, 255): {"name": "minecraft:stone"},
    }
    if not path:
        return default_legend
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    legend: Dict[Tuple[int, int, int, int], Dict[str, object]] = {}
    for hex_color, block in raw.items():
        c = hex_color.lstrip('#')
        if len(c) == 6:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            a = 255
        elif len(c) == 8:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            a = int(c[6:8], 16)
        else:
            raise ValueError(f"Invalid color key: {hex_color}")
        legend[(r, g, b, a)] = block
    return legend


def place_image_as_layer(builder: StructureBuilder, img: Image.Image, legend: Dict[Tuple[int, int, int, int], Dict[str, object]], y: int, skip_transparent: bool = True) -> None:
    rgba = img.convert('RGBA')
    width, height = rgba.size
    pixels = rgba.load()
    for z in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, z]
            if skip_transparent and a == 0:
                continue
            spec = legend.get((r, g, b, a))
            if not spec:
                # Unrecognized color => skip (treat as air)
                continue
            name = spec.get('name')
            properties = spec.get('properties') or {}
            builder.add_block(x, y, z, name, properties)  # x across, z forward


def write_datapack(datapack_dir: str, namespace: str, structure_path: str, pack_name: str) -> None:
    os.makedirs(datapack_dir, exist_ok=True)
    data_dir = os.path.join(datapack_dir, 'data', namespace)
    functions_dir = os.path.join(data_dir, 'functions')
    structures_dir = os.path.join(data_dir, 'structures')
    os.makedirs(functions_dir, exist_ok=True)
    os.makedirs(structures_dir, exist_ok=True)

    # pack.mcmeta
    mcmeta_path = os.path.join(datapack_dir, 'pack.mcmeta')
    mcmeta = {
        "pack": {
            "pack_format": 48,  # 1.21.x; adjust as needed
            "description": pack_name,
        }
    }
    with open(mcmeta_path, 'w', encoding='utf-8') as f:
        json.dump(mcmeta, f, indent=2)

    # Move/copy structure into data/<ns>/structures/<file>.nbt
    structure_filename = os.path.basename(structure_path)
    target_structure_path = os.path.join(structures_dir, structure_filename)
    with open(structure_path, 'rb') as src, open(target_structure_path, 'wb') as dst:
        dst.write(src.read())

    # Provide a function to place the structure at the executor
    fn_main_path = os.path.join(functions_dir, 'place.mcfunction')
    resource_name = f"{namespace}:{os.path.splitext(structure_filename)[0]}"
    with open(fn_main_path, 'w', encoding='utf-8') as f:
        f.write(f"place structure {resource_name} ~ ~ ~\n")


def main() -> None:
    parser = argparse.ArgumentParser(description='Convert a PNG into a Minecraft redstone structure and optional datapack.')
    parser.add_argument('image', help='Input PNG file path')
    parser.add_argument('-o', '--output', default='output.nbt', help='Output .nbt filename')
    parser.add_argument('--y', type=int, default=1, help='Y level for placement (default: 1)')
    parser.add_argument('--legend', help='JSON legend mapping hex colors to block specs')
    parser.add_argument('--data-version', type=int, default=DEFAULT_DATA_VERSION, help=f'DataVersion integer (default: {DEFAULT_DATA_VERSION})')
    parser.add_argument('--datapack', help='Output datapack directory (if provided, writes a pack with a place function)')
    parser.add_argument('--namespace', default='pngcircuit', help='Datapack namespace (default: pngcircuit)')
    parser.add_argument('--pack-name', default='PNG to Redstone', help='Datapack display name')
    args = parser.parse_args()

    img = Image.open(args.image)
    legend = parse_legend(args.legend)

    builder = StructureBuilder()
    place_image_as_layer(builder, img, legend, y=args.y)
    nbt_file = builder.build(data_version=args.data_version)
    nbt_file.save(args.output, gzipped=True)
    print(f"Wrote structure: {args.output}")

    if args.datapack:
        write_datapack(args.datapack, args.namespace, args.output, args.pack_name)
        print(f"Wrote datapack to: {args.datapack}. Run: /function {args.namespace}:place")


if __name__ == '__main__':
    main()


