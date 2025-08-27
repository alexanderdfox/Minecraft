
# build_circuit_mc.py
# --------------------------------------------------------------
# Minecraft Java Edition (Spigot/Paper + RaspberryJuice plugin)
# Python 3 script to draw a stylized version of your transformer/
# rectifier/capacitor circuit using redstone. Uses the mcpi API.
#
# WHAT IT PLACES (legend):
# - Redstone wire = interconnects (green carpet underlay for visibility)
# - Repeaters (facing) = diodes
# - Colored wool blocks mark components:
#     * ORANGE wool = "transformer" bodies (1:1, 1:100, 100:1)
#     * BLUE wool   = "capacitor" pillar
#     * LIGHT_GRAY  = neutral/bus rails
# - Signs are added with labels (ratios, 60 Hz note).
#
# Tweak the sizes/orientations below. Stand where you want the
# center-bottom of the drawing to appear and run the script.
#
# Requirements:
#   pip install mcpi
#   Spigot/Paper server with RaspberryJuice plugin installed
#   Start the server, load a world, then run this file with Python.
# --------------------------------------------------------------

from mcpi.minecraft import Minecraft
from mcpi import block
import time

mc = Minecraft.create()  # defaults to localhost:4711

# Helper utilities
def setb(x, y, z, b, data=0):
    mc.setBlock(x, y, z, b.id if hasattr(b, "id") else b, data)

def fill(x1, y1, z1, x2, y2, z2, b, data=0):
    xs, xe = sorted((x1, x2))
    ys, ye = sorted((y1, y2))
    zs, ze = sorted((z1, z2))
    for x in range(xs, xe+1):
        for y in range(ys, ye+1):
            for z in range(zs, ze+1):
                setb(x, y, z, b, data)

def line(x1, y1, z1, x2, y2, z2, b, data=0):
    # Bresenham-like simple line for axis-aligned or 45-degree steps
    x, y, z = x1, y1, z1
    dx = 1 if x2 >= x1 else -1
    dy = 1 if y2 >= y1 else -1
    dz = 1 if z2 >= z1 else -1
    while True:
        setb(x, y, z, b, data)
        if (x, y, z) == (x2, y2, z2): break
        if x != x2: x += dx
        if y != y2: y += dy if y1 != y2 else 0
        if z != z2: z += dz

# Redstone helpers
REDSTONE_WIRE = block.REDSTONE_WIRE
REPEATER = 356  # repeater block id (works with RaspberryJuice)
LAMP = block.REDSTONE_LAMP_OFF

# Decorative/legend blocks
ORANGE = block.WOOL.id, 1
BLUE = block.WOOL.id, 11
LIGHT_GRAY = block.WOOL.id, 8
GREEN_CARPET = 171, 13

def set_wool(x, y, z, color_id):
    setb(x, y, z, block.WOOL, color_id)

def carpet(x, y, z, color_id):
    setb(x, y, z, GREEN_CARPET[0], GREEN_CARPET[1])

def repeater(x, y, z, direction=0, delay_ticks=1):
    # direction: 0 south, 1 west, 2 north, 3 east (RaspberryJuice data bits)
    data = (direction & 0x3) | ((max(1, min(delay_ticks, 4)) - 1) << 2)
    setb(x, y, z, REPEATER, data)

def wire_path(points, y):
    for (x, z) in points:
        carpet(x, y-1, z, GREEN_CARPET[1])
        setb(x, y, z, REDSTONE_WIRE)

def label(x, y, z, text):
    # 63=sign post. data=0 orientation N; RJ ignores text per-line API—use chat
    setb(x, y, z, block.SIGN_POST)
    for line in text.split('\n'):
        mc.postToChat(line)

# Build origin relative to player
px, py, pz = mc.player.getTilePos()
Y = py + 0
X0 = px
Z0 = pz

mc.postToChat("Placing circuit… Stand still for a few seconds.")
time.sleep(1)

# Ground rails
for dz in range(0, 35):
    set_wool(X0-16, Y, Z0+dz, LIGHT_GRAY[1])
    set_wool(X0+16, Y, Z0+dz, LIGHT_GRAY[1])

# Bottom AC source "coil"
coil_w = 10
coil_z = 5
coil_y = Y
for x in range(X0-coil_w//2, X0+coil_w//2+1):
    setb(x, coil_y, Z0, block.IRON_BLOCK)
    setb(x, coil_y+1, Z0, block.IRON_BARS)

label(X0, coil_y+2, Z0-1, "60 Hz AC Source")

# Center 1:1 transformer body
fill(X0-2, Y+1, Z0+8, X0+2, Y+3, Z0+10, block.WOOL, ORANGE[1])
label(X0, Y+4, Z0+9, "1:1")

# Left and right "1:100" / "100:1" top blocks
fill(X0-12, Y+7, Z0+20, X0-8, Y+9, Z0+22, block.WOOL, ORANGE[1])
label(X0-10, Y+10, Z0+21, "1:100")
fill(X0+8, Y+7, Z0+20, X0+12, Y+9, Z0+22, block.WOOL, ORANGE[1])
label(X0+10, Y+10, Z0+21, "100:1")

# Capacitor column in the middle
for y in range(Y+6, Y+12):
    set_wool(X0, y, Z0+18, BLUE[1])
label(X0, Y+12, Z0+18, "Capacitor")

# Wire buses (stylized per your drawing)
wire_path([(X0-10+dx, Z0+12) for dx in range(0, 21)], Y+1)   # horizontal mid bus
wire_path([(X0-14, Z0+dz) for dz in range(6, 24)], Y+1)     # left vertical
wire_path([(X0+14, Z0+dz) for dz in range(6, 24)], Y+1)     # right vertical

# Diode bridges as 4 repeaters each (arrow-like)
# Left bridge
repeater(X0-12, Y+1, Z0+10, direction=3, delay_ticks=1)
repeater(X0-10, Y+1, Z0+10, direction=3, delay_ticks=1)
repeater(X0-12, Y+1, Z0+14, direction=1, delay_ticks=1)
repeater(X0-10, Y+1, Z0+14, direction=1, delay_ticks=1)

# Right bridge
repeater(X0+10, Y+1, Z0+10, direction=1, delay_ticks=1)
repeater(X0+12, Y+1, Z0+10, direction=1, delay_ticks=1)
repeater(X0+10, Y+1, Z0+14, direction=3, delay_ticks=1)
repeater(X0+12, Y+1, Z0+14, direction=3, delay_ticks=1)

# Connect bridges to mid bus
wire_path([(X0-11, Z0+11), (X0-11, Z0+12), (X0-11, Z0+13)], Y+1)
wire_path([(X0+11, Z0+11), (X0+11, Z0+12), (X0+11, Z0+13)], Y+1)

# Vertical feed toward capacitor
wire_path([(X0, Z0+13), (X0, Z0+14), (X0, Z0+15), (X0, Z0+16), (X0, Z0+17)], Y+1)

# Signs for reference nodes
label(X0-16, Y+1, Z0+12, "Bus L")
label(X0+16, Y+1, Z0+12, "Bus R")
label(X0, Y+1, Z0+13, "DC node → capacitor")

mc.postToChat("Done. If parts look offset, rotate your player and tweak directions in code.")
