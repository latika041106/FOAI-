"""
player.py
---------
Defines the Player class: position, health, inventory (key + potions),
and simple helper methods. Plain OOP, no AI here -- the player is
controlled by the human.
"""


class Player:
    def __init__(self, x, y, health=100, attack_power=25):
        self.x = x
        self.y = y
        self.max_health = health
        self.health = health
        self.attack_power = attack_power
        self.has_key = False
        self.potions = 1  # player starts with one healing potion

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def move_to(self, x, y):
        self.x = x
        self.y = y

    def position(self):
        return (self.x, self.y)

    def to_dict(self):
        """Serialize to a plain dict so Flask can turn it into JSON."""
        return {
            "x": self.x,
            "y": self.y,
            "health": self.health,
            "max_health": self.max_health,
            "attack_power": self.attack_power,
            "has_key": self.has_key,
            "potions": self.potions,
        }
