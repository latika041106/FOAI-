"""
ai_engine.py
------------
This is where Symbolic AI meets the actual game.

Flow every enemy turn:
  1. build_facts()   -> look at the current game state and describe it
                         as a dictionary of simple facts
  2. RuleEngine       -> picks the first rule whose IF-condition matches
                         those facts (see rules.py)
  3. execute_action() -> actually performs the chosen action on the
                         board (move / attack / heal / retreat / idle)

This mirrors classic "Expert System" design: Facts + Rules -> Decision.
"""

from rules import Rule, RuleEngine
from combat import resolve_attack, resolve_heal


GRID_SIZE = 5


def manhattan_distance(pos1, pos2):
    """Standard grid distance: sum of horizontal + vertical steps."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def build_facts(player, enemy):
    """
    Translate the raw game objects into a simple 'facts' dictionary.
    Symbolic AI reasons over FACTS, not raw objects -- this separation
    is what makes the rules easy to read and easy to explain.
    """
    dist = manhattan_distance(player.position(), enemy.position())
    return {
        "distance": dist,
        "is_adjacent": dist == 1,
        "enemy_health": enemy.health,
        "enemy_health_percent": enemy.health_percent(),
        "enemy_potions": enemy.potions,
        "player_position": player.position(),
        "enemy_position": enemy.position(),
    }


def build_enemy_rule_engine():
    """
    Build the enemy's rule book, IN PRIORITY ORDER.
    Earlier rules "win" over later ones if both conditions are true.

    Priority logic (matches the brief exactly):
      1. Adjacent to player?              -> Attack
      2. Low health AND has a potion?     -> Heal
      3. Low health AND NO potion left?   -> Retreat
      4. Player far away?                 -> Move closer
      5. Otherwise                        -> Idle
    """
    engine = RuleEngine()

    engine.add_rule(Rule(
        name="attack_if_adjacent",
        condition=lambda f: f["is_adjacent"],
        action=lambda f: {"action": "attack"},
        reason="Player is right next to me, I strike while I can!",
    ))

    engine.add_rule(Rule(
        name="heal_if_low_and_has_potion",
        condition=lambda f: f["enemy_health_percent"] <= 0.3 and f["enemy_potions"] > 0,
        action=lambda f: {"action": "heal"},
        reason="My health is critically low and I still have a potion, healing now.",
    ))

    engine.add_rule(Rule(
        name="retreat_if_low_and_no_potion",
        condition=lambda f: f["enemy_health_percent"] <= 0.3 and f["enemy_potions"] <= 0,
        action=lambda f: {"action": "retreat"},
        reason="My health is critical and I'm out of potions, I must fall back!",
    ))

    engine.add_rule(Rule(
        name="move_closer_if_far",
        condition=lambda f: f["distance"] > 1,
        action=lambda f: {"action": "move_closer"},
        reason="Player is too far away, closing the distance.",
    ))

    engine.add_rule(Rule(
        name="idle_default",
        condition=lambda f: True,   # catch-all, always matches
        action=lambda f: {"action": "idle"},
        reason="Nothing urgent to do right now, staying alert.",
    ))

    return engine


def _step_towards(from_pos, to_pos):
    """
    Compute one grid step (dx, dy) that reduces the distance from
    from_pos towards to_pos. Moves along whichever axis has the
    bigger gap first (simple, readable "greedy" pathing -- still
    symbolic/deterministic, not learned).
    """
    fx, fy = from_pos
    tx, ty = to_pos
    dx = tx - fx
    dy = ty - fy

    if abs(dx) >= abs(dy) and dx != 0:
        return (1 if dx > 0 else -1, 0)
    elif dy != 0:
        return (0, 1 if dy > 0 else -1)
    return (0, 0)


def _step_away(from_pos, danger_pos):
    """Same idea as _step_towards but in reverse, for retreating."""
    dx, dy = _step_towards(from_pos, danger_pos)
    return (-dx, -dy)


def _in_bounds(x, y):
    return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE


def execute_action(decision, player, enemy):
    """
    Actually perform the action the rule engine decided on.
    Returns a human-readable log message describing what happened.
    """
    action = decision["action"]

    if action == "attack":
        enemy.state = "attacking"
        return resolve_attack(enemy, "Enemy", player, "Player")

    if action == "heal":
        enemy.state = "healing"
        return resolve_heal(enemy, "Enemy")

    if action == "retreat":
        enemy.state = "retreating"
        dx, dy = _step_away(enemy.position(), player.position())
        nx, ny = enemy.x + dx, enemy.y + dy
        if _in_bounds(nx, ny) and (nx, ny) != player.position():
            enemy.move_to(nx, ny)
            return f"Enemy retreats to ({nx}, {ny})."
        return "Enemy wants to retreat but is cornered!"

    if action == "move_closer":
        enemy.state = "chasing"
        dx, dy = _step_towards(enemy.position(), player.position())
        nx, ny = enemy.x + dx, enemy.y + dy
        if _in_bounds(nx, ny) and (nx, ny) != player.position():
            enemy.move_to(nx, ny)
            return f"Enemy moves closer to ({nx}, {ny})."
        return "Enemy tries to advance but the path is blocked."

    # idle
    enemy.state = "idle"
    return "Enemy stands still, watching the player."


def enemy_take_turn(player, enemy):
    """
    Public entry point called once per turn by app.py.
    Runs the full Facts -> Rules -> Action -> Execution pipeline
    and returns a dict with everything the frontend needs to display
    the AI's explainable decision.
    """
    if not enemy.is_alive():
        return {
            "action": "none",
            "rule_name": "enemy_defeated",
            "reason": "The enemy has been defeated and can no longer act.",
            "log": "Enemy is defeated.",
        }

    engine = build_enemy_rule_engine()
    facts = build_facts(player, enemy)
    decision = engine.decide(facts)
    log_message = execute_action(decision, player, enemy)

    enemy.last_reason = decision["reason"]

    return {
        "action": decision["action"],
        "rule_name": decision["rule_name"],
        "reason": decision["reason"],
        "log": log_message,
        "facts": facts,
    }
