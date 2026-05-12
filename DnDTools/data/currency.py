"""D&D 5e currency — cp / sp / ep / gp / pp with conversion helpers.

PHB p.143 conversion table:
  1 platinum (pp) = 10 gold (gp)
  1 gold        = 2 electrum (ep) = 10 silver (sp) = 100 copper (cp)

Pure logic, no pygame.
"""
from __future__ import annotations

from dataclasses import dataclass


# Coin → copper-piece value
_COIN_VALUES = {
    "cp": 1,
    "sp": 10,
    "ep": 50,
    "gp": 100,
    "pp": 1000,
}

# Display order (lowest → highest); used for normalised breakdown
_COIN_ORDER = ("pp", "gp", "ep", "sp", "cp")


@dataclass
class Coins:
    """A pile of coins. All five denominations supported."""
    cp: int = 0
    sp: int = 0
    ep: int = 0
    gp: int = 0
    pp: int = 0

    # ------------------------------------------------------------------ #
    # Conversion
    # ------------------------------------------------------------------ #
    def total_cp(self) -> int:
        """Total wealth expressed in copper pieces."""
        return (self.cp
                + self.sp * _COIN_VALUES["sp"]
                + self.ep * _COIN_VALUES["ep"]
                + self.gp * _COIN_VALUES["gp"]
                + self.pp * _COIN_VALUES["pp"])

    def total_gp(self) -> float:
        """Total wealth expressed as gold (fractional for cp/sp)."""
        return self.total_cp() / _COIN_VALUES["gp"]

    @classmethod
    def from_cp(cls, copper: int) -> "Coins":
        """Build a normalised :class:`Coins` from a copper total."""
        copper = max(0, int(copper))
        out = cls()
        for coin in _COIN_ORDER:
            v = _COIN_VALUES[coin]
            n, copper = divmod(copper, v)
            setattr(out, coin, n)
        return out

    @classmethod
    def from_gp(cls, gold: float) -> "Coins":
        return cls.from_cp(int(round(float(gold) * _COIN_VALUES["gp"])))

    # ------------------------------------------------------------------ #
    # Arithmetic
    # ------------------------------------------------------------------ #
    def __add__(self, other: "Coins") -> "Coins":
        return Coins.from_cp(self.total_cp() + other.total_cp())

    def __sub__(self, other: "Coins") -> "Coins":
        return Coins.from_cp(self.total_cp() - other.total_cp())

    def __mul__(self, scalar: int) -> "Coins":
        return Coins.from_cp(int(self.total_cp() * scalar))

    def __ge__(self, other) -> bool:
        if isinstance(other, Coins):
            return self.total_cp() >= other.total_cp()
        return self.total_cp() >= int(other)

    # ------------------------------------------------------------------ #
    # Mutators
    # ------------------------------------------------------------------ #
    def normalise(self) -> "Coins":
        """Re-pack coins so smaller denominations roll into larger
        ones (e.g. 25 sp → 2 gp + 5 sp)."""
        norm = Coins.from_cp(self.total_cp())
        for coin in _COIN_ORDER:
            setattr(self, coin, getattr(norm, coin))
        return self

    def can_afford(self, price_gp: float) -> bool:
        return self.total_gp() >= price_gp

    def pay(self, price_gp: float) -> bool:
        """Spend ``price_gp`` worth of coins. Smallest coins first
        (player drops cp before gp). Returns False if can't afford."""
        if not self.can_afford(price_gp):
            return False
        target_cp = self.total_cp() - int(round(price_gp * _COIN_VALUES["gp"]))
        new = Coins.from_cp(max(0, target_cp))
        for coin in _COIN_ORDER:
            setattr(self, coin, getattr(new, coin))
        return True

    # ------------------------------------------------------------------ #
    # Render
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {coin: getattr(self, coin) for coin in _COIN_ORDER
                if getattr(self, coin) > 0} or {"cp": 0}

    def short(self) -> str:
        """Compact "12pp 4gp 50sp" rendering."""
        parts = []
        for coin in _COIN_ORDER:
            n = getattr(self, coin)
            if n > 0:
                parts.append(f"{n}{coin}")
        return " ".join(parts) or "0gp"


# --------------------------------------------------------------------- #
# Free-function helpers (handy for parsing user input)
# --------------------------------------------------------------------- #
def coins_from_string(text: str) -> Coins:
    """Parse "12pp 4gp 50sp" or just "100" (treated as gp)."""
    text = (text or "").strip().lower()
    if not text:
        return Coins()
    out = Coins()
    bits = text.split()
    if len(bits) == 1 and bits[0].replace(".", "", 1).isdigit():
        return Coins.from_gp(float(bits[0]))
    for b in bits:
        for coin in _COIN_ORDER:
            if b.endswith(coin):
                try:
                    n = int(b[: -len(coin)])
                except ValueError:
                    n = 0
                if n > 0:
                    setattr(out, coin, getattr(out, coin) + n)
                break
    return out


def total_cp_of(coins_iter) -> int:
    """Sum every Coins instance in ``coins_iter`` to a single cp total."""
    return sum(c.total_cp() for c in coins_iter)
