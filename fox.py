import nbtlib
from nbtlib import Compound, List, String, Int, ByteArray

def create_structure(blocks, width, height, length, filename):
    # blocks = {(x, y, z): (block_id, block_data), ...}
    size = width * height * length
    block_ids = [0] * size
    block_data = [0] * size

    def index(x, y, z):
        return y * length * width + z * width + x

    for (x, y, z), (bid, bdata) in blocks.items():
        i = index(x, y, z)
        block_ids[i] = bid
        block_data[i] = bdata

    # Structure NBT format
    structure = Compound({
        'size': List[Int]([width, height, length]),
        'palette': List[Compound]([Compound({'Name': String('minecraft:air')})]),
        'blocks': List[Compound]([]),
        'entities': List[Compound]([])
    })

    # Populate blocks list
    for (x, y, z), (bid, bdata) in blocks.items():
        block_entry = Compound({
            'state': Int(bid),   # simple numeric ID; can later be converted to names if needed
            'pos': List[Int]([x, y, z])
        })
        structure['blocks'].append(block_entry)

    nbtlib.File(structure).save(filename)
    print(f"Saved {filename} as structure NBT")

# Example: tiny capacitor structure (a 3-block vertical column of blue wool)
blocks = {
    (1,0,1): (35, 11),  # Blue wool (ID 35, data 11)
    (1,1,1): (35, 11),
    (1,2,1): (35, 11),
}

create_structure(blocks, width=3, height=5, length=3, filename='circuit_structure.nbt')
