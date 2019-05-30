from dataclasses import dataclass
from typing import Dict, List

import discord


@dataclass
class CharacterState:
    """Tracks a characters position, current language, stats, etc."""

    # What's your name?
    name: str
    # Should they be shown in rolls?
    active: bool
    # What're your ability scores? Keyed by all-lowercase STR, CON, DEX, WIS, INT
    ability_scores: Dict[str, int]
    # Proficiencies: As a list, of what keywords should give the bonus. use lowercase
    proficiencies: List[str]
    # The proficiency mod of the character
    proficiency_mod: int

    def validate(self) -> str:
        """Ensures things are fine. Return an error message if not"""
        warnings = ""
        # First validate all ability scores are present.
        for score in ["str", "con", "dex", "wis", "int"]:
            if score not in self.ability_scores:
                warnings += "Missing ability score {0} in character {1.name}\n".format(score, self)

        return warnings


# Default ability scores
DEFAULT_SCORES = {
    "str": 10,
    "con": 10,
    "dex": 10,
    "wis": 10,
    "int": 10
}


def score_to_mod(score: int) -> int:
    """Returns ability score converted to a modifier"""
    return (score - 10) // 2


@dataclass
class Message:
    """Keeps track of the relevant bits of a message"""
    # What was spoken/done?
    sentence: str
    # With what action verb?
    verb: str
    # Who by
    speaker: CharacterState
    # Wherein
    origin_channel: discord.TextChannel
    # In what language?
    # At what volume?
    # With what composure/emotion?


def get_character_by_name(name):
    # TODO: make this actually read files
    return CharacterState("Placeholder", True, dict(DEFAULT_SCORES), ["athletics"], 2)
