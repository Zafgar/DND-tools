"""Aurelian kruunu — the grand city map, and the tools that build it.

Every other premade map is a room: twenty squares by fifteen, one fight,
one idea. This one is a city district, sixty by forty-four squares —
three hundred feet by two hundred and twenty — and it is built rather
than typed, because thirteen hundred hand-written tile literals is not
something anyone can edit afterwards.

The design rule that shapes everything is **a dragon has to be able to
walk down the street**. A Huge creature covers 3x3 squares and a
Gargantuan one 4x4, so:

  * the two grand avenues are six squares wide (30 ft),
  * every district street is at least four (20 ft),
  * the city gate and the castle gate are five squares across,
  * and no through-route is ever pinched narrower than four.

``test_grand_city.py`` measures all of that on the built map rather than
trusting the numbers here, and walks a Gargantuan from the south gate to
the castle to prove the routes actually connect.

Districts, laid out around the crossing of the two avenues:

    NW  the castle — curtain wall, battlements, corner towers, keep
    NE  the temple quarter, noble houses and a walled garden
    SW  the artisans' quarter — forges, wells, hay, cramped yards
    SE  the market square and the canal wharf
"""
from __future__ import annotations

# Grid extent. Everything below is written against these two numbers.
CITY_W = 60
CITY_H = 44

# The two grand avenues, in grid coordinates (inclusive ranges).
AVENUE_NS = (26, 31)      # x range of the north-south avenue
AVENUE_EW = (18, 23)      # y range of the east-west avenue


# --------------------------------------------------------------------- #
# Tile helpers
#
# Each returns a list of terrain dicts. They are deliberately dumb: the
# builder composes them and a single de-duplication pass at the end
# decides who wins when two features overlap.
# --------------------------------------------------------------------- #
def _t(kind, x, y):
    return {"terrain_type": kind, "grid_x": int(x), "grid_y": int(y)}


def _fill(kind, x0, y0, x1, y1):
    """Solid block, inclusive of both corners."""
    return [_t(kind, x, y)
            for y in range(int(y0), int(y1) + 1)
            for x in range(int(x0), int(x1) + 1)]


def _outline(kind, x0, y0, x1, y1):
    """Hollow rectangle — the four edges only."""
    out = []
    for x in range(int(x0), int(x1) + 1):
        out.append(_t(kind, x, y0))
        out.append(_t(kind, x, y1))
    for y in range(int(y0) + 1, int(y1)):
        out.append(_t(kind, x0, y))
        out.append(_t(kind, x1, y))
    return out


def _row(kind, x0, x1, y, step=1):
    return [_t(kind, x, y) for x in range(int(x0), int(x1) + 1, step)]


def _col(kind, x, y0, y1, step=1):
    return [_t(kind, x, y) for y in range(int(y0), int(y1) + 1, step)]


def _building(x0, y0, x1, y1, door_side="s", door_at=None):
    """A solid town house with one door.

    Houses are solid ``house`` tiles rather than hollow rooms: at this
    scale the interiors would be a hundred tiles nobody fights in, and
    a solid block reads instantly as "building" on the map. The door
    marks the entrance for flavour and for anything that cares about
    where a street meets a wall.
    """
    tiles = _fill("house", x0, y0, x1, y1)
    if door_side == "s":
        dx = door_at if door_at is not None else (x0 + x1) // 2
        tiles.append(_t("door", dx, y1))
    elif door_side == "n":
        dx = door_at if door_at is not None else (x0 + x1) // 2
        tiles.append(_t("door", dx, y0))
    elif door_side == "w":
        dy = door_at if door_at is not None else (y0 + y1) // 2
        tiles.append(_t("door", x0, dy))
    else:
        dy = door_at if door_at is not None else (y0 + y1) // 2
        tiles.append(_t("door", x1, dy))
    return tiles


# --------------------------------------------------------------------- #
# Districts
# --------------------------------------------------------------------- #
def _city_walls():
    """Curtain wall around the whole district, towers, and two gates."""
    t = []
    t += _row("wall", 0, CITY_W - 1, 0)
    t += _row("wall", 0, CITY_W - 1, CITY_H - 1)
    t += _col("wall", 0, 0, CITY_H - 1)
    t += _col("wall", CITY_W - 1, 0, CITY_H - 1)

    # Corner and mid-wall towers
    for (tx, ty) in ((0, 0), (CITY_W - 2, 0), (0, CITY_H - 2),
                     (CITY_W - 2, CITY_H - 2), (0, 20), (CITY_W - 2, 20),
                     (14, 0), (44, 0), (14, CITY_H - 2), (44, CITY_H - 2)):
        t += _fill("tower", tx, ty, tx + 1, ty + 1)

    # South gate, five squares wide, opening onto the north-south avenue
    gx0, gx1 = AVENUE_NS[0] + 1, AVENUE_NS[1]
    for x in range(gx0, gx1 + 1):
        t.append(_t("gate", x, CITY_H - 1))
    # North postern, same width, so the avenue runs clean through
    for x in range(gx0, gx1 + 1):
        t.append(_t("gate", x, 0))
    # East watergate where the canal leaves the city
    for y in range(33, 37):
        t.append(_t("gate", CITY_W - 1, y))
    return t


def _side_streets():
    """The lesser roads.

    Without these the ground between the building blocks renders as
    bare floor, and a city district reads as buildings floating in a
    void. Laid down before the districts so anything solid wins.
    """
    t = []
    # Ring road just inside the curtain wall
    t += _fill("cobblestone", 1, 1, CITY_W - 2, 1)
    t += _fill("cobblestone", 1, CITY_H - 2, CITY_W - 2, CITY_H - 2)
    t += _fill("cobblestone", 1, 1, 1, CITY_H - 2)
    t += _fill("cobblestone", CITY_W - 2, 1, CITY_W - 2, CITY_H - 2)
    # Alleys between the artisan workshop blocks
    for ax in (9, 17):
        t += _fill("cobblestone", ax, 24, ax + 1, 42)
    t += _fill("cobblestone", 2, 41, 24, 42)
    t += _fill("cobblestone", 2, 24, 24, 24)
    # Streets around the castle and the temple quarter
    t += _fill("cobblestone", 23, 1, 25, CITY_H - 2)
    t += _fill("cobblestone", 32, 1, 32, CITY_H - 2)
    t += _fill("cobblestone", 1, 17, CITY_W - 2, 17)
    t += _fill("cobblestone", 47, 1, 48, 17)
    t += _fill("cobblestone", 33, 17, 57, 17)
    # Wharf approach
    t += _fill("cobblestone", 47, 24, 50, 42)
    return t


def _avenues():
    """The two grand avenues, paved, with lamps and signposts."""
    t = []
    t += _fill("cobblestone", AVENUE_NS[0], 1, AVENUE_NS[1], CITY_H - 2)
    t += _fill("cobblestone", 1, AVENUE_EW[0], CITY_W - 2, AVENUE_EW[1])
    # Lamps down both sides of each avenue, well clear of the roadway
    for y in range(4, CITY_H - 3, 6):
        if AVENUE_EW[0] - 1 <= y <= AVENUE_EW[1] + 1:
            continue
        t.append(_t("lamppost", AVENUE_NS[0] - 1, y))
        t.append(_t("lamppost", AVENUE_NS[1] + 1, y))
    for x in range(4, CITY_W - 3, 7):
        if AVENUE_NS[0] - 1 <= x <= AVENUE_NS[1] + 1:
            continue
        # Never in front of the castle gate: a single lamp square there
        # is enough to stop a Huge creature lining up on a five-wide
        # gate, which makes the whole castle unenterable for the boss.
        if not 9 <= x <= 15:
            t.append(_t("lamppost", x, AVENUE_EW[0] - 1))
        t.append(_t("lamppost", x, AVENUE_EW[1] + 1))
    # Crossroads sign in the middle of the junction
    t.append(_t("signpost", AVENUE_NS[0], AVENUE_EW[0]))
    t.append(_t("statue", AVENUE_NS[1], AVENUE_EW[1]))
    return t


def _castle():
    """North-west: curtain wall, wall walk, corner towers, keep, yard."""
    t = []
    x0, y0, x1, y1 = 2, 2, 22, 16

    # Curtain wall, with the wall walk only along the north and west
    # runs. Ringing the whole yard with battlement put a 20 ft high
    # walkway across the inside of the gate, so anything entering the
    # castle climbed a wall and then fell off it into the courtyard.
    t += _outline("wall", x0, y0, x1, y1)
    t += _row("battlement", x0 + 1, x1 - 1, y0 + 1)
    t += _col("battlement", x0 + 1, y0 + 1, y1 - 1)
    for (tx, ty) in ((x0 - 1, y0 - 1), (x1 - 1, y0 - 1),
                     (x0 - 1, y1 - 1), (x1 - 1, y1 - 1)):
        t += _fill("tower", tx, ty, tx + 1, ty + 1)

    # Flagged courtyard. Laid before the keep and the clutter so those
    # overwrite it; without it the castle interior is the only bare
    # ground in a city where every street is paved, and it reads as a
    # hole in the map rather than as a yard.
    t += _fill("cobblestone", x0 + 2, y0 + 2, x1 - 2, y1 - 1)

    # Castle gate, five wide, facing the east-west avenue
    for x in range(10, 15):
        t.append(_t("gate", x, y1))
        t.append(_t("cobblestone", x, y1 - 1))

    # Approach from the gate to the keep door, wide enough for a dragon
    t += _fill("cobblestone", 10, y1 - 1, 14, 12)

    # The keep: a real building you can enter
    kx0, ky0, kx1, ky1 = 8, 4, 17, 11
    t += _outline("wall", kx0, ky0, kx1, ky1)
    for x in range(11, 14):
        t.append(_t("door", x, ky1))
    t.append(_t("throne", 12, ky0 + 2))
    t.append(_t("throne", 13, ky0 + 2))
    t += _row("pillar", kx0 + 2, kx1 - 2, ky0 + 4, step=3)
    t += _row("brazier", kx0 + 2, kx1 - 2, ky1 - 1, step=6)
    t.append(_t("table", 10, 8))
    t.append(_t("table", 15, 8))

    # Yard furniture. All of it hugs the walls: the courtyard has to
    # stay open enough for a Huge creature to turn around in, which
    # means nothing solid in the middle of it.
    t.append(_t("well", 5, 14))
    t.append(_t("cart", 20, 14))
    t.append(_t("crate", 20, 13))
    t.append(_t("barrel", 4, 5))
    t.append(_t("barrel", 4, 6))
    t += _fill("crops", 19, 4, 21, 7)
    t += _row("fence", 19, 21, 8)
    return t


def _temple_quarter():
    """North-east: temple, noble houses, a walled garden."""
    t = []
    # Temple — enterable, on a raised platform
    tx0, ty0, tx1, ty1 = 35, 3, 46, 12
    t += _fill("platform_5", tx0, ty0, tx1, ty1)
    t += _outline("wall", tx0, ty0, tx1, ty1)
    for x in range(40, 43):
        t.append(_t("door", x, ty1))
    t.append(_t("altar", 40, ty0 + 2))
    t.append(_t("altar", 41, ty0 + 2))
    t += _col("pillar", tx0 + 2, ty0 + 3, ty1 - 2, step=3)
    t += _col("pillar", tx1 - 2, ty0 + 3, ty1 - 2, step=3)
    t += _row("brazier", tx0 + 3, tx1 - 3, ty1 - 1, step=6)

    # Temple forecourt, wide enough to fight in
    t += _fill("cobblestone", 35, 13, 46, 16)
    t.append(_t("fountain", 40, 15))
    t.append(_t("fountain", 41, 15))

    # Noble houses along the east wall
    t += _building(49, 3, 54, 7, "s")
    t += _building(49, 10, 54, 14, "s")
    t += _building(49, 16, 52, 16, "n")

    # Walled garden between temple and wall
    t += _fill("hedge", 33, 3, 33, 16)
    t += _row("hedge", 47, 48, 3)
    t += _fill("tree", 55, 4, 56, 5)
    t += _fill("tree", 55, 12, 56, 13)
    t += _fill("crops", 56, 7, 57, 10)
    return t


def _artisan_quarter():
    """South-west: cramped yards, forges, wells, hay and washing lines."""
    t = []
    # Two rows of workshops with a SIX-wide lane between them. Five was
    # not enough: scatter three wells and a forge down a five-wide lane
    # and the clear channel drops below three squares, which walls the
    # whole quarter off from anything Huge.
    for bx in (3, 11, 19):
        t += _building(bx, 25, bx + 5, 29, "s")
        t += _building(bx, 36, bx + 5, 40, "n")
    # The lane itself
    t += _fill("cobblestone", 2, 30, 24, 35)

    # Yard clutter — pinned to the two edge rows of the lane so the
    # four middle rows stay clear from end to end.
    t.append(_t("well", 8, 30))
    t.append(_t("well", 17, 35))
    t.append(_t("forge", 3, 30))
    t.append(_t("forge", 4, 30))
    t.append(_t("cart", 13, 35))
    t.append(_t("haystack", 22, 30))
    t.append(_t("haystack", 22, 35))
    t.append(_t("barrel", 10, 35))
    t.append(_t("crate", 11, 35))
    t.append(_t("barricade", 2, 35))

    # Backyards against the south wall
    t += _fill("crops", 3, 42, 10, 42)
    t += _row("fence", 12, 24, 42)
    t.append(_t("haystack", 15, 41))
    t.append(_t("cart", 20, 41))

    # Alley north of the workshops
    t += _fill("cobblestone", 2, 24, 24, 24)
    return t


def _market_and_wharf():
    """South-east: the market square, then the canal and its wharf."""
    t = []
    # Market square, paved, with a fountain at its heart
    t += _fill("cobblestone", 33, 24, 50, 36)
    t += _fill("fountain", 40, 29, 41, 30)

    # Stalls in two rows, in pairs with FOUR-wide aisles between them.
    # Spaced every four the gaps came out two squares wide, which is a
    # market a Medium shopper can walk through and a dragon cannot.
    for x in (34, 40, 46):
        t.append(_t("market_stall", x, 25))
        t.append(_t("market_stall", x + 1, 25))
        t.append(_t("market_stall", x, 35))
        t.append(_t("market_stall", x + 1, 35))
    for y in (27, 28, 32, 33):
        t.append(_t("market_stall", 34, y))
        t.append(_t("market_stall", 48, y))
    t.append(_t("cart", 36, 31))
    t.append(_t("cart", 45, 28))
    t.append(_t("crate", 37, 31))
    t.append(_t("barrel", 44, 32))
    t.append(_t("signpost", 40, 24))

    # The canal: three squares of water down the east side, into the
    # watergate, with a plank wharf and two bridges over it.
    t += _fill("water", 53, 24, 55, 42)
    t += _fill("dock", 51, 24, 52, 42)
    t += _fill("bridge", 53, 26, 55, 27)
    t += _fill("bridge", 53, 38, 55, 39)
    t.append(_t("shipwreck", 54, 33))
    t.append(_t("barrel", 51, 30))
    t.append(_t("crate", 52, 31))
    t.append(_t("crate", 51, 40))

    # Slum houses south of the market
    t += _building(33, 38, 38, 41, "n")
    t += _building(41, 38, 46, 41, "n")
    return t


# --------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------- #
# When two features land on the same square, the later one usually wins
# — but a door must never be overwritten by the wall it sits in, and a
# gate must never be paved over. These win regardless of order.
_PRIORITY = {"door": 3, "gate": 3, "bridge": 2, "dock": 2}


def _merge(tiles):
    """One tile per square, with doors and gates protected."""
    best = {}
    for tile in tiles:
        if tile["grid_x"] < 0 or tile["grid_y"] < 0:
            continue          # the no-op marker from _castle
        key = (tile["grid_x"], tile["grid_y"])
        prev = best.get(key)
        if prev is None:
            best[key] = tile
            continue
        if _PRIORITY.get(prev["terrain_type"], 0) > \
           _PRIORITY.get(tile["terrain_type"], 0):
            continue
        best[key] = tile
    return [best[k] for k in sorted(best)]


def build_grand_city() -> dict:
    """The whole district, assembled and de-duplicated."""
    tiles = []
    tiles += _side_streets()     # paving first; everything solid wins
    tiles += _castle()
    tiles += _temple_quarter()
    tiles += _artisan_quarter()
    tiles += _market_and_wharf()
    tiles += _avenues()          # avenues are cut through the districts
    tiles += _city_walls()       # the wall wins over everything it meets
    terrain = [t for t in _merge(tiles)
               if t["terrain_type"] != "flagstone_yard_marker"]

    return {
        "floor_style": "flagstone",
        "name": "Aurelian kruunu — Suurkaupunki",
        "description": (
            "A whole city district: castle, temple, market, canal wharf "
            "and artisans' quarter, 300 by 220 feet. The avenues are "
            "thirty feet across so a dragon can come down the street."),
        "terrain": terrain,
        # Every one of these fits a Huge creature — checked by
        # test_grand_city, not by eye. A spawn a dragon cannot stand on
        # is the single most common way a big map breaks.
        "spawn_zones": {
            # Defenders form up on the avenue inside the south gate.
            "players": [(26, 40), (29, 40), (26, 38), (29, 38),
                        (27, 36), (30, 36)],
            # Attackers hold the avenue crossing and the market, far
            # enough away that the first round is a march up the street.
            "enemies": [(27, 20), (30, 20), (36, 20), (44, 31),
                        (12, 32), (20, 20)],
        },
    }


def install(premade_maps: dict) -> dict:
    """Register the city in the premade map table."""
    premade_maps["grand_city"] = build_grand_city()
    return premade_maps
