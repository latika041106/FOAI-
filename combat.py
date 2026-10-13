"""
combat.py
---------
Handles the mechanics of an attack: how much damage is dealt, and
building a readable combat-log message. Keeping this separate from
Player/Enemy means those classes don't need to know about each other.
"""


def resolve_attack(attacker, attacker_name, defender, defender_name):
    """
    attacker/defender: Player or Enemy instances (both have .attack_power,
                        .take_damage(), .health)
    Returns a log message string describing what happened.
    """
    damage = attacker.attack_power
    defender.take_damage(damage)

    message = f"{attacker_name} attacks {defender_name} for {damage} damage!"

    if not defender.is_alive():
        message += f" {defender_name} has been defeated!"

    return message


def resolve_heal(entity, name):
    """Heal an entity (used by the enemy's 'heal' rule) and log it."""
    before = entity.health
    entity.heal(entity.heal_amount)
    healed = entity.health - before
    return f"{name} drinks a potion and recovers {healed} HP!"
