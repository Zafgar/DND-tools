"""
Generic serialization/deserialization for all dataclass models.
Replaces ~500 lines of manual _export_X / _import_X boilerplate.

Usage:
    from data.serialization import serialize, deserialize

    # Export a CreatureStats to dict (JSON-ready)
    data = serialize(hero)

    # Import from dict back to CreatureStats
    hero = deserialize(CreatureStats, data)
"""
import dataclasses
from typing import get_type_hints, get_origin, get_args, List, Dict, Optional
from data.models import (
    CreatureStats, AbilityScores, Action, SpellInfo, Feature,
    RacialTrait, SummonTemplate, Item,
)

# All known dataclass types for nested deserialization
_DATACLASS_TYPES = {
    cls.__name__: cls for cls in [
        CreatureStats, AbilityScores, Action, SpellInfo, Feature,
        RacialTrait, SummonTemplate, Item,
    ]
}


def serialize(obj) -> dict:
    """Serialize any dataclass to a JSON-compatible dict.

    Handles nested dataclasses, lists of dataclasses, and primitive types.
    Skips fields that match the default value to keep JSON compact.
    """
    if not dataclasses.is_dataclass(obj):
        raise TypeError(f"Expected a dataclass instance, got {type(obj)}")

    result = {}
    defaults = _get_defaults(type(obj))

    for f in dataclasses.fields(obj):
        value = getattr(obj, f.name)
        default = defaults.get(f.name)

        # Serialize the value
        serialized = _serialize_value(value)

        # Skip fields matching default (keeps JSON smaller)
        if serialized == default:
            continue

        result[f.name] = serialized

    return result


def serialize_full(obj) -> dict:
    """Serialize all fields including defaults. Used when full data is needed."""
    if not dataclasses.is_dataclass(obj):
        raise TypeError(f"Expected a dataclass instance, got {type(obj)}")

    result = {}
    for f in dataclasses.fields(obj):
        value = getattr(obj, f.name)
        result[f.name] = _serialize_value(value)
    return result


def deserialize(cls, data: dict):
    """Deserialize a dict into a dataclass instance.

    Handles nested dataclasses, lists of dataclasses, and provides
    defaults for missing fields (backward-compatible with older saves).
    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")

    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"Expected a dataclass type, got {cls}")

    hints = get_type_hints(cls)
    kwargs = {}

    for f in dataclasses.fields(cls):
        if f.name not in data:
            # Use field default
            continue

        raw_value = data[f.name]
        field_type = hints.get(f.name, type(None))
        kwargs[f.name] = _deserialize_value(field_type, raw_value)

    return cls(**kwargs)


def _serialize_value(value):
    """Recursively serialize a single value."""
    if dataclasses.is_dataclass(value):
        return serialize_full(value)
    elif isinstance(value, list):
        return [_serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    else:
        # Primitive: int, float, str, bool, None
        return value


def _deserialize_value(field_type, raw_value):
    """Recursively deserialize a value based on its type hint."""
    origin = get_origin(field_type)
    args = get_args(field_type)

    # Handle Optional[X] -> extract X
    if origin is type(None):
        return raw_value

    # Check if it's a dataclass type directly
    if dataclasses.is_dataclass(field_type) and isinstance(raw_value, dict):
        return deserialize(field_type, raw_value)

    # Handle List[X]
    if origin is list and args and isinstance(raw_value, list):
        inner_type = args[0]
        if dataclasses.is_dataclass(inner_type):
            return [deserialize(inner_type, v) if isinstance(v, dict) else v for v in raw_value]
        return raw_value

    # Handle Dict[K, V]
    if origin is dict and isinstance(raw_value, dict):
        return raw_value

    # Handle Optional[X] (Union[X, None])
    import typing
    if hasattr(typing, 'UnionType'):
        # Python 3.10+ X | None
        pass
    if origin is type(None) or (hasattr(origin, '__origin__') and origin.__origin__ is type(None)):
        return raw_value

    # Try to match by name if it's a string-named dataclass in a list
    if isinstance(raw_value, dict):
        # Could be a nested dataclass - check known types
        for dc_name, dc_cls in _DATACLASS_TYPES.items():
            if dataclasses.is_dataclass(field_type) and field_type is dc_cls:
                return deserialize(dc_cls, raw_value)

    return raw_value


def _get_defaults(cls) -> dict:
    """Get default values for all fields as serialized values."""
    defaults = {}
    for f in dataclasses.fields(cls):
        if f.default is not dataclasses.MISSING:
            defaults[f.name] = _serialize_value(f.default)
        elif f.default_factory is not dataclasses.MISSING:
            defaults[f.name] = _serialize_value(f.default_factory())
    return defaults
