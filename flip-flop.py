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
import gzip
import io
import struct
from dataclasses import dataclass
from typing import Dict, List as TypingList, Optional, Tuple


# Reasonable default for modern Java editions; structure blocks will upgrade on load.
# If you know your target version, override with --data-version.
DEFAULT_DATA_VERSION = 3700


@dataclass(frozen=True)
class BlockStateKey:
    name: str
    properties: Tuple[Tuple[str, str], ...]


# --- Minimal NBT writer (subset: Int, String, List, Compound) ---

TAG_End = 0
TAG_Byte = 1
TAG_Short = 2
TAG_Int = 3
TAG_Long = 4
TAG_Float = 5
TAG_Double = 6
TAG_Byte_Array = 7
TAG_String = 8
TAG_List = 9
TAG_Compound = 10
TAG_Int_Array = 11
TAG_Long_Array = 12


class IntTag(int):
    pass


class StringTag(str):
    pass


class ListTag(list):
    def __init__(self, element_tag_id: int, values: TypingList):
        super().__init__(values)
        self.element_tag_id = element_tag_id


class CompoundTag(dict):
    pass


def _write_short(buf: io.BufferedIOBase, value: int) -> None:
    buf.write(struct.pack('>h', int(value)))


def _write_int(buf: io.BufferedIOBase, value: int) -> None:
    buf.write(struct.pack('>i', int(value)))


def _write_string_payload(buf: io.BufferedIOBase, s: str) -> None:
    data = s.encode('utf-8')
    _write_short(buf, len(data))
    buf.write(data)


def _write_named_tag(buf: io.BufferedIOBase, tag_id: int, name: str, value) -> None:
    buf.write(struct.pack('>B', tag_id))
    _write_string_payload(buf, name)
    _write_payload(buf, tag_id, value)


def _write_payload(buf: io.BufferedIOBase, tag_id: int, value) -> None:
    if tag_id == TAG_Int:
        _write_int(buf, int(value))
    elif tag_id == TAG_String:
        _write_string_payload(buf, str(value))
    elif tag_id == TAG_List:
        assert isinstance(value, ListTag), 'List payload must be ListTag'
        buf.write(struct.pack('>B', value.element_tag_id))
        _write_int(buf, len(value))
        for item in value:
            _write_payload(buf, value.element_tag_id, item)
    elif tag_id == TAG_Compound:
        assert isinstance(value, (CompoundTag, dict)), 'Compound payload must be CompoundTag/dict'
        items = value.items() if isinstance(value, dict) else value.items()
        for k, v in items:
            t_id = _infer_tag_id(v)
            _write_named_tag(buf, t_id, k, v)
        buf.write(struct.pack('>B', TAG_End))
    else:
        raise ValueError(f'Unsupported tag id: {tag_id}')


def _infer_tag_id(value) -> int:
    if isinstance(value, IntTag):
        return TAG_Int
    if isinstance(value, StringTag):
        return TAG_String
    if isinstance(value, ListTag):
        return TAG_List
    if isinstance(value, CompoundTag) or isinstance(value, dict):
        return TAG_Compound
    if isinstance(value, int):
        return TAG_Int
    if isinstance(value, str):
        return TAG_String
    raise ValueError(f'Cannot infer tag for value type: {type(value)}')


def write_nbt_file(root: CompoundTag, path: str, gzip_compress: bool = False) -> None:
    raw = io.BytesIO()
    # Root is a named Compound with an empty name by convention
    _write_named_tag(raw, TAG_Compound, '', root)
    data = raw.getvalue()
    if gzip_compress:
        with gzip.open(path, 'wb') as f:
            f.write(data)
    else:
        with open(path, 'wb') as f:
            f.write(data)


class StructureBuilder:
    def __init__(self) -> None:
        self._palette: TypingList[CompoundTag] = []
        self._palette_index: Dict[BlockStateKey, int] = {}
        self._blocks: TypingList[CompoundTag] = []
        self._min_x = 10**9
        self._min_y = 10**9
        self._min_z = 10**9
        self._max_x = -10**9
        self._max_y = -10**9
        self._max_z = -10**9

    def add_block(self, x: int, y: int, z: int, name: str, properties: Optional[Dict[str, str]] = None, nbt: Optional[CompoundTag] = None) -> None:
        key = BlockStateKey(name=name, properties=tuple(sorted((properties or {}).items())))
        if key not in self._palette_index:
            palette_entry = CompoundTag({
                'Name': StringTag(name),
            })
            if properties:
                palette_entry['Properties'] = CompoundTag({k: StringTag(v) for k, v in properties.items()})
            self._palette_index[key] = len(self._palette)
            self._palette.append(palette_entry)

        state_index = IntTag(self._palette_index[key])
        block_entry = CompoundTag({
            'pos': ListTag(TAG_Int, [IntTag(x), IntTag(y), IntTag(z)]),
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
            blk['pos'] = ListTag(TAG_Int, [IntTag(px + dx), IntTag(py + dy), IntTag(pz + dz)])
        self._max_x += dx
        self._max_y += dy
        self._max_z += dz
        self._min_x = 0
        self._min_y = 0
        self._min_z = 0

    def build(self, data_version: int) -> CompoundTag:
        self.translate_to_origin()
        sx, sy, sz = self.size()
        root = CompoundTag({
            'size': ListTag(TAG_Int, [IntTag(sx), IntTag(sy), IntTag(sz)]),
            'palette': ListTag(TAG_Compound, self._palette),
            'blocks': ListTag(TAG_Compound, self._blocks),
            'entities': ListTag(TAG_Compound, []),
            'DataVersion': IntTag(int(data_version)),
        })
        return root


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

    root = builder.build(data_version=args.data_version)
    write_nbt_file(root, args.output, gzip_compress=bool(args.gzip))
    print(f'Wrote structure: {args.output} (gzip={bool(args.gzip)})')


if __name__ == '__main__':
    main()

