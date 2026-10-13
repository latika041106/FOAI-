"""
enemy.py
--------
Defines the Enemy class. The enemy carries its own stats plus a
`state` label ("idle", "chasing", "attacking", "healing", "retreating")
that the UI uses to show what the AI is currently doing.

The actual decision-making logic lives in ai_engine.py -- this file
only stores data and simple helpers, keeping our OOP responsibilities
clean and separated.
"""


class Enemy:
    def __init__(self, x, y, health=80, attack_power=15):
        self.x = x
        self.y = y
        self.max_health = health
        self.health = health
        self.attack_power = attack_power
        self.potions = 2  # enemy can self-heal twice before running dry
        self.heal_amount = 20
        self.state = "idle"          # current behaviour label, for the UI
        self.last_reason = "Waiting for the player to approach."

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
        self.potions -= 1

    def move_to(self, x, y):
        self.x = x
        self.y = y

    def position(self):
        return (self.x, self.y)

    def health_percent(self):
        return self.health / self.max_health

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "health": self.health,
            "max_health": self.max_health,
            "attack_power": self.attack_power,
            "potions": self.potions,
            "alive": self.is_alive(),
            "state": self.state,
            "last_reason": self.last_reason,
        }
