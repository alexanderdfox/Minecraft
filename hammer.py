import nbtlib
from nbtlib import tag

def dict_to_nbt_compound(d):
	return nbtlib.Compound({k: nbtlib.String(v) for k, v in d.items()})

def create_nbt_structure(filename):
	size = [16, 10, 16]
	offset = [0, 0, 0]

	blocks = [
		(2, 1, 2, "minecraft:redstone_lamp", {}),
		(2, 1, 1, "minecraft:redstone_wire", {}),
		(2, 1, 0, "minecraft:redstone_torch", {}),
		(1, 1, 1, "minecraft:comparator", {"facing": "south"}),
		(3, 1, 1, "minecraft:comparator", {"facing": "south"}),
		(2, 1, 3, "minecraft:redstone_wire", {}),
		(2, 1, 4, "minecraft:repeater", {"facing": "north"}),
		(2, 2, 2, "minecraft:stone", {}),
		(2, 3, 2, "minecraft:stone", {}),
		(1, 4, 2, "minecraft:stone", {}),
		(3, 4, 2, "minecraft:stone", {}),
	]

	palette = []
	palette_dict = {}
	blocks_nbt = []

	def state_to_string(states):
		return ",".join(f"{k}={v}" for k, v in states.items()) if states else ""

	for (x, y, z, name, states) in blocks:
		blockstate = name
		state_str = state_to_string(states)
		if state_str:
			blockstate += f"[{state_str}]"

		if blockstate not in palette_dict:
			palette_dict[blockstate] = len(palette)
			palette.append(nbtlib.Compound({
				"Name": nbtlib.String(name),
				"Properties": dict_to_nbt_compound(states) if states else nbtlib.Compound()
			}))

		block_index = palette_dict[blockstate]

		blocks_nbt.append(nbtlib.Compound({
			"pos": nbtlib.List([tag.Int(x), tag.Int(y), tag.Int(z)]),
			"state": tag.Int(block_index)
		}))

	structure_nbt = nbtlib.Compound({
		"DataVersion": tag.Int(3120),  # Minecraft 1.19.3
		"size": nbtlib.List([tag.Int(c) for c in size]),
		"palette": nbtlib.List(palette),
		"blocks": nbtlib.List(blocks_nbt),
		"entities": nbtlib.List([])
	})

	nbtlib.File(structure_nbt, gzipped=True).save(filename)
	print(f"✅ Minecraft structure saved to {filename}")

if __name__ == "__main__":
	create_nbt_structure("do_nothing_hammer.nbt")
