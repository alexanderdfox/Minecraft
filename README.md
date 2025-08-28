## Minecraft Redstone Structure Tools

This repository contains several Python scripts to generate Minecraft Structure NBT files and a PNG→redstone converter with optional datapack export.

Prerequisites:
- Python 3.9+
- Install deps: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

---

### camera.py
Generates a complex redstone circuit inspired by a differential amplifier.

Usage:
```bash
python3 camera.py -o camera.nbt --data-version 3700
```
Flags:
- `-o, --output`: Output `.nbt` filename (default: `camera.nbt`)
- `--no-gzip`: Save uncompressed NBT (gzip by default)
- `--data-version`: DataVersion integer (default: 3700)

Output: `camera.nbt`

---

### flip-flop.py
Generates a compact T flip-flop using droppers/hopper with comparator output.

Usage:
```bash
python3 flip-flop.py -o flip_flop.nbt --data-version 3700
```
Flags:
- `-o, --output`: Output `.nbt` filename (default: `flip_flop.nbt`)
- `--gzip`: Gzip-compress the NBT (off by default)
- `--data-version`: DataVersion integer (default: 3700)

Output: `flip_flop.nbt`

---

### fox.py
Minimal example of building a structure NBT from a manual block map.

Behavior:
- Writes a tiny example structure `circuit_structure.nbt` containing blue wool.

Usage:
```bash
python3 fox.py
```

Output: `circuit_structure.nbt`

---

### hammer.py
Creates a small example structure with a simple redstone setup.

Usage:
```bash
python3 hammer.py
```

Output: `do_nothing_hammer.nbt`

---

### png_to_redstone.py
Converts a PNG image into a Minecraft redstone structure (`.nbt`). Optionally creates a datapack to place the structure via a function.

Basic conversion:
```bash
python3 png_to_redstone.py path/to/circuit.png -o circuit.nbt
```

With custom color→block legend:
```bash
python3 png_to_redstone.py path/to/circuit.png --legend legend.json -o circuit.nbt
```

Also output a datapack (plugin-like) to place the structure at the executor:
```bash
python3 png_to_redstone.py path/to/circuit.png -o circuit.nbt \
  --datapack ./pack --namespace mypack --pack-name "PNG Circuits"
```
Then install the datapack and run in-game:
```
/function mypack:place
```

Flags:
- `-o, --output`: Output `.nbt` filename (default: `output.nbt`)
- `--y`: Y-level for placement in the structure (default: 1)
- `--legend`: Path to JSON legend mapping colors to block specs
- `--data-version`: DataVersion integer (default: 3700)
- `--datapack`: Output datapack directory (creates pack.mcmeta, function, and embeds the structure)
- `--namespace`: Datapack namespace (default: `pngcircuit`)
- `--pack-name`: Datapack display name (default: `PNG to Redstone`)

Legend JSON format:
```json
{
  "#ff0000": { "name": "minecraft:redstone_wire" },
  "#00ff00": { "name": "minecraft:repeater", "properties": { "facing": "east", "delay": "1", "locked": "false", "powered": "false" } },
  "#0000ff": { "name": "minecraft:redstone_torch" },
  "#ffff00": { "name": "minecraft:comparator", "properties": { "facing": "east", "mode": "compare", "powered": "false" } },
  "#000000": { "name": "minecraft:stone" }
}
```

Notes:
- Unmapped colors and fully transparent pixels are treated as air (skipped).
- The X axis maps to image width; Z maps to image height; Y is constant unless extended.
- Use a Structure Block or the generated datapack function to place the structure.

---

### Importing structures in Minecraft (Java Edition)
1. Copy `.nbt` files into your world folder under: `saves/<WORLD>/generated/<namespace>/structures/` when used via datapack; or load directly via a Structure Block by placing the file in `saves/<WORLD>/structures/` (or use the datapack output which handles layout).
2. Use a Structure Block in LOAD mode and enter the structure name (for datapack: `<namespace>:<file>`; for direct: the base filename without extension).
3. Click LOAD to preview, then LOAD again to place.


