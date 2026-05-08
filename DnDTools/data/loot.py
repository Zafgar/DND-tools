"""Loot helpers — credit campaign-side party gold + inventory after
combat. Pure logic, no pygame.

Intended call site: at the end of a battle, the DM resolves loot
drops via ``award_loot(campaign, gold=, items=)``. The helper
distributes gold either to ``Campaign.party_gold`` (default) or
splits it evenly among active PCs, and appends item names to the
shared inventory.

Also exposes ``loot_from_defeated_entities`` that walks a list of
combat ``Entity`` objects and aggregates their carried items / gold
into a single :class:`LootBundle` ready for award.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from data.campaign import Campaign, PartyMember


@dataclass
class LootBundle:
    """Aggregated loot ready to credit to the party."""
    gold: float = 0.0
    items: List[str] = field(default_factory=list)
    source_names: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return self.gold <= 0 and not self.items

    def merge(self, other: "LootBundle") -> "LootBundle":
        return LootBundle(
            gold=self.gold + other.gold,
            items=self.items + other.items,
            source_names=self.source_names + other.source_names,
        )


@dataclass
class AwardReport:
    gold_credited: float = 0.0
    items_added: int = 0
    per_pc_gold: List[tuple] = field(default_factory=list)
    distribution: str = "shared"  # 'shared' | 'split' | 'first'

    def summary(self) -> str:
        bits = []
        if self.gold_credited:
            mode = {"shared": "yhteiseen kassaan",
                     "split": "jaettu PC:ille",
                     "first": "yhdelle PC:lle"}.get(self.distribution,
                                                       "")
            bits.append(f"{self.gold_credited:.1f} gp {mode}")
        if self.items_added:
            bits.append(f"{self.items_added} esinettä lisätty")
        return " · ".join(bits) if bits else "ei loottia"


# --------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------- #
def loot_from_defeated_entities(entities: Iterable) -> LootBundle:
    """Walk ``entities`` (defeated combat Entity instances) and sum
    their ``stats.items`` lists + any ``loot_gold`` attribute. Skips
    summons and lair markers because their loot is the conjurer's,
    not the party's."""
    bundle = LootBundle()
    for ent in entities:
        if getattr(ent, "is_summon", False) or getattr(
                ent, "is_lair", False):
            continue
        if getattr(ent, "is_player", False):
            continue
        if getattr(ent, "hp", 0) > 0:
            continue   # Still alive — not loot yet
        items = getattr(getattr(ent, "stats", None), "items", []) or []
        for item in items:
            bundle.items.append(str(item))
        gold = float(getattr(getattr(ent, "stats", None),
                                "loot_gold", 0.0) or 0.0)
        bundle.gold += gold
        name = getattr(ent, "name", "") or "?"
        if name and name not in bundle.source_names:
            bundle.source_names.append(name)
    return bundle


# --------------------------------------------------------------------- #
# Awarding
# --------------------------------------------------------------------- #
def _active_party(campaign: Campaign) -> List[PartyMember]:
    return [m for m in (campaign.party or []) if getattr(m, "active", True)]


def award_loot(campaign: Campaign, *,
                 gold: float = 0.0,
                 items: Optional[Iterable[str]] = None,
                 distribution: str = "shared") -> AwardReport:
    """Credit ``gold`` and ``items`` to ``campaign``.

    ``distribution`` controls gold-only:
        "shared"  — adds to Campaign.party_gold (default)
        "split"   — divides evenly across active PCs (any remainder
                     goes to the shared purse)
        "first"   — credits the first active PC

    Items always go to the shared ``Campaign.party_inventory`` so
    the DM can hand them out manually.
    """
    rep = AwardReport(distribution=distribution)
    if gold and gold > 0:
        if distribution == "split":
            actives = _active_party(campaign)
            n = len(actives)
            if n > 0:
                share = gold / n
                for m in actives:
                    m.gold = float(m.gold or 0.0) + share
                    rep.per_pc_gold.append(
                        (m.hero_data.get("name", ""), share)
                    )
            else:
                # Empty party → fall back to shared
                campaign.party_gold = float(campaign.party_gold) + gold
        elif distribution == "first":
            actives = _active_party(campaign)
            if actives:
                m = actives[0]
                m.gold = float(m.gold or 0.0) + gold
                rep.per_pc_gold.append(
                    (m.hero_data.get("name", ""), gold)
                )
            else:
                campaign.party_gold = float(campaign.party_gold) + gold
        else:
            campaign.party_gold = float(campaign.party_gold) + gold
        rep.gold_credited = gold

    if items:
        for it in items:
            campaign.party_inventory.append(str(it))
            rep.items_added += 1
    return rep


def award_bundle(campaign: Campaign, bundle: LootBundle, *,
                   distribution: str = "shared") -> AwardReport:
    """Convenience: award an aggregated :class:`LootBundle`."""
    return award_loot(campaign,
                        gold=bundle.gold,
                        items=bundle.items,
                        distribution=distribution)


# --------------------------------------------------------------------- #
# Per-PC inventory transfer
# --------------------------------------------------------------------- #
def hand_item_to_pc(campaign: Campaign, hero_name: str,
                       item_name: str) -> bool:
    """Move ``item_name`` from the shared party_inventory to the named
    PC's custom_items list. Returns True on success."""
    if item_name not in campaign.party_inventory:
        return False
    key = (hero_name or "").strip().lower()
    target = None
    for m in (campaign.party or []):
        nm = (m.hero_data or {}).get("name", "") or ""
        if nm.lower() == key:
            target = m
            break
    if target is None:
        return False
    campaign.party_inventory.remove(item_name)
    if target.custom_items is None:
        target.custom_items = []
    target.custom_items.append(item_name)
    return True
