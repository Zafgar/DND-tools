"""Simple internationalization (i18n) module for DnD Tools.

Usage:
    from i18n import t
    label = t("combat.round")  # Returns "ROUND" or "KIERROS" based on current language
"""
from __future__ import annotations

_current_language: str = "en"

# Translation dictionaries
_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "combat.round": "ROUND",
        "combat.turn": "Turn",
        "combat.started": "COMBAT STARTED",
        "combat.initiative_order": "Initiative order",
        "combat.surprise": "is surprised!",
        "combat.next_turn": "Next Turn",
        "combat.ai_turn": "AI Turn",
        "combat.deployment": "DEPLOYMENT PHASE",
        "ui.menu": "Menu",
        "ui.save": "Save",
        "ui.load": "Load",
        "ui.settings": "Settings",
        "ui.help": "Help",
        "ui.back": "Back",
        "ui.close": "Close",
        "ui.cancel": "Cancel",
        "ui.confirm": "Confirm",
        "ui.new_encounter": "New Encounter",
        "ui.hero_creator": "Hero Creator",
        "ui.campaign": "Campaign",
        "ui.combat_roster": "Combat Roster",
        "encounter.easy": "EASY",
        "encounter.fair": "FAIR",
        "encounter.hard": "HARD",
        "encounter.deadly": "DEADLY",
        "condition.prone": "Prone",
        "condition.stunned": "Stunned",
        "condition.poisoned": "Poisoned",
        "condition.blinded": "Blinded",
        "condition.charmed": "Charmed",
        "condition.frightened": "Frightened",
        "condition.invisible": "Invisible",
        "condition.restrained": "Restrained",
    },
    "fi": {
        "combat.round": "KIERROS",
        "combat.turn": "Vuoro",
        "combat.started": "TAISTELU ALKAA",
        "combat.initiative_order": "Aloitejärjestys",
        "combat.surprise": "on yllättynyt!",
        "combat.next_turn": "Seuraava vuoro",
        "combat.ai_turn": "Tekoälyvuoro",
        "combat.deployment": "SIJOITTELUVAIHE",
        "ui.menu": "Valikko",
        "ui.save": "Tallenna",
        "ui.load": "Lataa",
        "ui.settings": "Asetukset",
        "ui.help": "Ohje",
        "ui.back": "Takaisin",
        "ui.close": "Sulje",
        "ui.cancel": "Peruuta",
        "ui.confirm": "Vahvista",
        "ui.new_encounter": "Uusi kohtaaminen",
        "ui.hero_creator": "Hahmon luonti",
        "ui.campaign": "Kampanja",
        "ui.combat_roster": "Taistelulista",
        "encounter.easy": "HELPPO",
        "encounter.fair": "REILU",
        "encounter.hard": "VAIKEA",
        "encounter.deadly": "TAPPAVA",
        "condition.prone": "Maassa",
        "condition.stunned": "Tyrmistynyt",
        "condition.poisoned": "Myrkytetty",
        "condition.blinded": "Sokaistu",
        "condition.charmed": "Lumottu",
        "condition.frightened": "Peloissaan",
        "condition.invisible": "Näkymätön",
        "condition.restrained": "Sidottu",
    },
}


def set_language(lang: str) -> None:
    """Set the active language. Supported: 'en', 'fi'."""
    global _current_language
    if lang in _TRANSLATIONS:
        _current_language = lang


def get_language() -> str:
    """Get the current language code."""
    return _current_language


def t(key: str) -> str:
    """Translate a key to the current language. Falls back to English, then to the key itself."""
    lang_dict = _TRANSLATIONS.get(_current_language, {})
    if key in lang_dict:
        return lang_dict[key]
    # Fallback to English
    en_dict = _TRANSLATIONS.get("en", {})
    return en_dict.get(key, key)


def available_languages() -> list[str]:
    """Return list of supported language codes."""
    return list(_TRANSLATIONS.keys())
