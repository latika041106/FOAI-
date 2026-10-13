"""
app.py
------
The Flask web server. This file is intentionally "dumb" about AI --
it just manages the board/game-state and calls into ai_engine.py,
combat.py, player.py, and enemy.py to do the real work.

Routes:
  GET  /                -> serves the game page
  POST /api/new_game    -> resets and returns a fresh game state
  GET  /api/state        -> returns the current game state
  POST /api/action       -> player moves or attacks, then the enemy
                             takes its Symbolic AI turn, returns the
                             updated state + a log of what happened
"""

from flask import Flask, render_template, request, jsonify

from player import Player
from enemy import Enemy
from combat import resolve_attack
from ai_engine import enemy_take_turn, manhattan_distance, GRID_SIZE

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory game state. For a small learning project a single global game
# is simplest. (For multiple simultaneous players you'd key this by session
# id, but that's outside the scope of this beginner project.)
# ---------------------------------------------------------------------------
game = {}


def new_game_state():
    """Build a brand new board + player + enemy + items."""
    player = Player(x=0, y=0)
    enemy = Enemy(x=4, y=0)

    # Fixed layout, kept simple and readable for a beginner project.
    items = {
        (2, 2): "health_pack",
        (0, 3): "health_pack",
        (4, 2): "key",
    }
    exit_pos = (4, 4)

    return {
        "player": player,
        "enemy": enemy,
        "items": items,
        "exit_pos": exit_pos,
        "log": ["A new dungeon has been generated. Find the key and reach the exit!"],
        "game_over": False,
        "won": False,
    }


game.update(new_game_state())


def add_log(message):
    game["log"].append(message)
    # keep the log from growing forever
    game["log"] = game["log"][-30:]


def serialize_state():
    """Turn the whole game state into plain JSON-friendly data."""
    return {
        "grid_size": GRID_SIZE,
        "player": game["player"].to_dict(),
        "enemy": game["enemy"].to_dict(),
        "items": {f"{x},{y}": kind for (x, y), kind in game["items"].items()},
        "exit_pos": list(game["exit_pos"]),
        "log": game["log"],
        "game_over": game["game_over"],
        "won": game["won"],
    }


def pick_up_items(player):
    """Check the player's current tile for a collectible and apply it."""
    pos = (player.x, player.y)
    item = game["items"].get(pos)
    if item == "health_pack":
        player.heal(30)
        add_log("Player picks up a health pack and recovers 30 HP!")
        del game["items"][pos]
    elif item == "key":
        player.has_key = True
        add_log("Player found the key! The exit is now reachable.")
        del game["items"][pos]


def check_win_condition(player):
    if player.has_key and (player.x, player.y) == game["exit_pos"]:
        game["game_over"] = True
        game["won"] = True
        add_log("Player reaches the exit with the key. VICTORY!")


def check_lose_condition(player):
    if not player.is_alive():
        game["game_over"] = True
        game["won"] = False
        add_log("Player has been defeated. GAME OVER.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(serialize_state())


@app.route("/api/new_game", methods=["POST"])
def new_game():
    game.update(new_game_state())
    return jsonify(serialize_state())


@app.route("/api/action", methods=["POST"])
def player_action():
    if game["game_over"]:
        return jsonify(serialize_state())

    data = request.get_json(force=True) or {}
    action = data.get("action")
    direction = data.get("direction")

    player = game["player"]
    enemy = game["enemy"]

    deltas = {
        "up": (0, -1),
        "down": (0, 1),
        "left": (-1, 0),
        "right": (1, 0),
    }

    if action == "move":
        if direction not in deltas:
            return jsonify({"error": "invalid direction"}), 400

        dx, dy = deltas[direction]
        nx, ny = player.x + dx, player.y + dy

        if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
            add_log("Player can't move off the edge of the dungeon.")
        elif enemy.is_alive() and (nx, ny) == enemy.position():
            add_log("Player bumps into the enemy! (Attack instead to fight.)")
        else:
            player.move_to(nx, ny)
            add_log(f"Player moves {direction} to ({nx}, {ny}).")
            pick_up_items(player)

    elif action == "attack":
        dist = manhattan_distance(player.position(), enemy.position())
        if not enemy.is_alive():
            add_log("There is no enemy here to attack.")
        elif dist != 1:
            add_log("Enemy is not adjacent, move closer to attack.")
        else:
            msg = resolve_attack(player, "Player", enemy, "Enemy")
            add_log(msg)

    elif action == "use_potion":
        if player.potions > 0:
            player.potions -= 1
            player.heal(30)
            add_log("Player drinks a potion and recovers 30 HP!")
        else:
            add_log("Player has no potions left.")

    else:
        return jsonify({"error": "invalid action"}), 400

    check_win_condition(player)
    check_lose_condition(player)

    # -------- Enemy's Symbolic AI turn --------
    ai_result = None
    if not game["game_over"] and enemy.is_alive():
        ai_result = enemy_take_turn(player, enemy)
        add_log(f"[AI] {ai_result['log']} (Rule: {ai_result['rule_name']} — {ai_result['reason']})")
        check_lose_condition(player)

    response = serialize_state()
    response["ai_decision"] = ai_result
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
