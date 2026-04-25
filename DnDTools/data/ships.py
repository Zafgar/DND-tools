"""Ships, sea routes, and fares.

PHB / DMG-flavoured but tuned to be testable and friendly to the DM:
each ship has a daily speed in miles, a per-mile passenger fare in gp,
a max passenger and cargo capacity, and a crew requirement. Sea routes
on the world map are AnnotationPath objects with ``path_type="sea_route"``;
``can_traverse_sea_route(traveller)`` validates whether a given party can
take that path on its own (it can't unless it's actually a ship).

Pure logic; no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# --------------------------------------------------------------------- #
# Ship catalog
# --------------------------------------------------------------------- #
@dataclass(frozen=True)
class ShipType:
    key: str
    name: str
    miles_per_day: int      # base cruising speed (good wind)
    passenger_capacity: int
    cargo_tons: int
    crew_required: int
    base_fare_gp_per_mile: float    # per passenger
    cargo_fare_gp_per_ton_mile: float
    description: str = ""

    @property
    def daily_charter_gp(self) -> float:
        """Approximate daily charter price = passenger fare * cap * speed."""
        return self.base_fare_gp_per_mile * self.passenger_capacity \
                 * self.miles_per_day


SHIP_TYPES: Dict[str, ShipType] = {
    "rowboat": ShipType(
        key="rowboat", name="Rowboat",
        miles_per_day=12, passenger_capacity=4, cargo_tons=0,
        crew_required=1, base_fare_gp_per_mile=0.05,
        cargo_fare_gp_per_ton_mile=0.0,
        description="Tiny river/coastal craft. Two oars, no sail.",
    ),
    "keelboat": ShipType(
        key="keelboat", name="Keelboat",
        miles_per_day=24, passenger_capacity=8, cargo_tons=1,
        crew_required=4, base_fare_gp_per_mile=0.1,
        cargo_fare_gp_per_ton_mile=0.05,
        description="River and coastal trader, single mast.",
    ),
    "longship": ShipType(
        key="longship", name="Longship",
        miles_per_day=72, passenger_capacity=40, cargo_tons=10,
        crew_required=40, base_fare_gp_per_mile=0.15,
        cargo_fare_gp_per_ton_mile=0.05,
        description="Coastal raider, oars + square sail.",
    ),
    "sailing_ship": ShipType(
        key="sailing_ship", name="Sailing Ship",
        miles_per_day=48, passenger_capacity=20, cargo_tons=100,
        crew_required=20, base_fare_gp_per_mile=0.2,
        cargo_fare_gp_per_ton_mile=0.05,
        description="Standard merchant brig — most common trade hull.",
    ),
    "warship": ShipType(
        key="warship", name="Warship",
        miles_per_day=60, passenger_capacity=60, cargo_tons=50,
        crew_required=80, base_fare_gp_per_mile=0.5,
        cargo_fare_gp_per_ton_mile=0.1,
        description="Naval galleon — escorts, troop transport.",
    ),
    "galley": ShipType(
        key="galley", name="Galley",
        miles_per_day=96, passenger_capacity=80, cargo_tons=150,
        crew_required=80, base_fare_gp_per_mile=0.4,
        cargo_fare_gp_per_ton_mile=0.08,
        description="Big oar-and-sail trader, very fast in calms.",
    ),
    "airship": ShipType(
        key="airship", name="Airship",
        miles_per_day=192, passenger_capacity=20, cargo_tons=10,
        crew_required=10, base_fare_gp_per_mile=2.0,
        cargo_fare_gp_per_ton_mile=0.5,
        description="Magical airship, ignores terrain (spelljammer-lite).",
    ),
}


def list_ship_types() -> List[ShipType]:
    return [SHIP_TYPES[k] for k in SHIP_TYPES]


def get_ship(key: str) -> ShipType:
    if key not in SHIP_TYPES:
        raise KeyError(f"Unknown ship type {key!r}; "
                       f"known: {list(SHIP_TYPES)}")
    return SHIP_TYPES[key]


# --------------------------------------------------------------------- #
# Fare math
# --------------------------------------------------------------------- #
def passenger_fare_gp(ship: ShipType, miles: float, passengers: int) -> float:
    """Total gp for ``passengers`` riders over ``miles`` aboard ``ship``."""
    if miles <= 0 or passengers <= 0:
        return 0.0
    if passengers > ship.passenger_capacity:
        # Over capacity: caller has to charter multiple ships; the
        # extra riders simply can't board.
        passengers = ship.passenger_capacity
    return float(passengers) * ship.base_fare_gp_per_mile * float(miles)


def cargo_fare_gp(ship: ShipType, miles: float, cargo_tons: float) -> float:
    if miles <= 0 or cargo_tons <= 0:
        return 0.0
    if cargo_tons > ship.cargo_tons:
        cargo_tons = ship.cargo_tons
    return float(cargo_tons) * ship.cargo_fare_gp_per_ton_mile * float(miles)


def voyage_days(ship: ShipType, miles: float) -> float:
    if miles <= 0:
        return 0.0
    return float(miles) / float(ship.miles_per_day)


def voyage_estimate(ship: ShipType, miles: float, passengers: int = 1,
                      cargo_tons: float = 0) -> dict:
    """Compact dict summarising a single chartered voyage."""
    pas_fare = passenger_fare_gp(ship, miles, passengers)
    car_fare = cargo_fare_gp(ship, miles, cargo_tons)
    return {
        "ship": ship.key,
        "ship_name": ship.name,
        "miles": float(miles),
        "days": voyage_days(ship, miles),
        "passengers": int(passengers),
        "passenger_fare_gp": pas_fare,
        "cargo_tons": float(cargo_tons),
        "cargo_fare_gp": car_fare,
        "total_gp": pas_fare + car_fare,
        "exceeded_passengers": passengers > ship.passenger_capacity,
        "exceeded_cargo": cargo_tons > ship.cargo_tons,
    }


def cheapest_ship(miles: float, passengers: int,
                    cargo_tons: float = 0) -> Optional[dict]:
    """Best-value ship for the trip — minimises total fare among ships
    that can fit the passengers and cargo. Returns the
    voyage_estimate dict or None if no ship fits."""
    candidates = []
    for s in SHIP_TYPES.values():
        if s.passenger_capacity < passengers:
            continue
        if s.cargo_tons < cargo_tons:
            continue
        candidates.append(voyage_estimate(s, miles, passengers, cargo_tons))
    if not candidates:
        return None
    return min(candidates, key=lambda v: v["total_gp"])


def fastest_ship(miles: float, passengers: int = 1,
                   cargo_tons: float = 0) -> Optional[dict]:
    """Fastest ship that still fits passengers + cargo."""
    candidates = []
    for s in SHIP_TYPES.values():
        if s.passenger_capacity < passengers:
            continue
        if s.cargo_tons < cargo_tons:
            continue
        candidates.append(voyage_estimate(s, miles, passengers, cargo_tons))
    if not candidates:
        return None
    return min(candidates, key=lambda v: v["days"])


# --------------------------------------------------------------------- #
# Sea-route validation
# --------------------------------------------------------------------- #
def is_sea_route(path) -> bool:
    return getattr(path, "path_type", "") == "sea_route"


def is_air_route(path) -> bool:
    return getattr(path, "path_type", "") == "air_route"


def can_traverse(path, traveller) -> bool:
    """Return True iff ``traveller`` (a MapObject) can move along
    ``path`` on its own. Sea routes require a vehicle of type
    ``ship``/``airship``/``caravan`` whose actor is a ship; air routes
    require either an airship vehicle or a creature with fly speed
    (handled via passenger or actor metadata in upstream code)."""
    from data.map_engine import VEHICLE_TYPES
    if is_sea_route(path):
        # Only ship-class vehicles can sail (airships also count)
        return traveller.object_type in ("ship", "airship")
    if is_air_route(path):
        # Airship or any flying actor (caller decides via actor lookup)
        return traveller.object_type == "airship"
    # Land routes: anyone moves on them
    return True
