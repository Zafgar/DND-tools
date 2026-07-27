"""Data models for the Tactical AI: ActionStep and TurnPlan."""
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.entities import Entity
    from data.models import Action, SpellInfo, CreatureStats


@dataclass
class ActionStep:
    """One step inside a full turn plan."""
    step_type: str             # "attack","spell","bonus_attack","bonus_spell","move","wait","legendary","summon"
    description: str = ""
    attacker: Optional["Entity"] = None
    target: Optional["Entity"] = None
    targets: List["Entity"] = field(default_factory=list)
    action_name: str = ""
    action: Optional["Action"] = None
    spell: Optional["SpellInfo"] = None
    slot_used: int = 0
    attack_roll: int = 0
    attack_roll_str: str = ""
    nat_roll: int = 0
    is_crit: bool = False
    is_hit: bool = False
    damage: int = 0
    damage_type: str = ""
    save_dc: int = 0
    save_ability: str = ""
    applies_condition: str = ""
    condition_dc: int = 0
    new_x: float = 0.0
    new_y: float = 0.0
    movement_ft: float = 0.0
    old_x: float = 0.0
    old_y: float = 0.0
    aoe_center: tuple = field(default_factory=tuple)
    # Class mechanic extras
    bonus_damage: int = 0            # Extra damage from Sneak Attack, Smite, etc.
    bonus_damage_desc: str = ""      # "Sneak Attack 5d6", "Divine Smite 2d8", etc.
    rage_bonus: int = 0              # Rage damage bonus applied
    # Summon spawn info
    summon_name: str = ""
    summon_x: float = 0.0
    summon_y: float = 0.0
    summon_hp: int = 0
    summon_ac: int = 10
    summon_owner: Optional["Entity"] = None
    summon_duration: int = 10
    summon_spell: str = ""
    summon_immediate_attack: bool = False  # If True, attacks immediately after spawn
    counter_checked: bool = False
    is_magical: bool = False
    transform_stats: Optional["CreatureStats"] = None


@dataclass
class TurnOption:
    """One action the AI considered for this turn, kept for the DM.

    The tactical AI already builds and scores every option a creature
    has before choosing the best one — and then threw the rest away.
    Keeping them lets the DM see the whole board the way the AI sees
    it, and take the third-best line on purpose because a player just
    did something that ought to draw the monster's attention.

    ``steps`` is the same list ``_decide_action`` would have returned
    had this option won, so choosing one runs through the normal
    confirm-and-roll flow with nothing special about it.
    """
    kind: str                                   # "multiattack", "aoe_spell", ...
    score: float = 0.0
    label: str = ""                             # short name for the button
    reason: str = ""                            # one line: why the AI rates it here
    steps: List[ActionStep] = field(default_factory=list)
    rank: int = 0                               # 1 = the AI's own pick
    is_best: bool = False


@dataclass
class TurnPlan:
    entity: Optional["Entity"] = None
    steps: List[ActionStep] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
    # Every main action the AI weighed, best first. Empty when the turn
    # never reached the action phase (incapacitated, nothing in range).
    options: List[TurnOption] = field(default_factory=list)
    # Where the chosen action sits inside ``steps``. Swapping in a
    # different option replaces exactly this slice and leaves the
    # movement and bonus-action steps around it alone.
    action_slice: tuple = (0, 0)
    # Spell slots as they stood before the options were built, so an
    # option the DM picks later is charged from the same baseline.
    slots_before: dict = field(default_factory=dict)
    # Which option is currently in ``steps`` (1-based rank, 0 = none).
    chosen_rank: int = 0
