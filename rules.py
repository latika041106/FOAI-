"""
rules.py
--------
This file is the heart of our SYMBOLIC AI (rule-based reasoning).

Two simple building blocks:

1. Rule       -> one IF-THEN rule ("IF condition THEN action, BECAUSE reason")
2. RuleEngine -> holds a priority-ordered list of Rules and picks the
                 FIRST one whose condition is true.

This is a classic "forward chaining with priority ordering" symbolic AI
technique. There is no learning, no neural network, no probability --
every enemy decision can be traced back to a plain-English rule that a
human wrote. That's what makes it "Explainable AI".
"""


class Rule:
    """
    A single IF-THEN rule.

    name:      short machine-readable id, e.g. "attack_if_adjacent"
    condition: function(facts: dict) -> bool          -- the "IF"
    action:    function(facts: dict) -> dict           -- the "THEN"
    reason:    human-readable explanation shown to the player
    """

    def __init__(self, name, condition, action, reason):
        self.name = name
        self.condition = condition
        self.action = action
        self.reason = reason

    def matches(self, facts):
        """Return True if this rule's IF-condition holds for the given facts."""
        return self.condition(facts)

    def fire(self, facts):
        """Run this rule's THEN-action and attach explainability info."""
        result = self.action(facts)
        result["rule_name"] = self.name
        result["reason"] = self.reason
        return result


class RuleEngine:
    """
    Holds an ordered list of Rules and evaluates them top-to-bottom.
    The order matters a lot: putting "attack" before "heal" means the
    enemy will always prefer attacking over healing when both could apply.
    """

    def __init__(self):
        self.rules = []

    def add_rule(self, rule):
        """Add a rule to the end of the priority list."""
        self.rules.append(rule)

    def decide(self, facts):
        """
        Walk through rules in priority order.
        Return the action dict produced by the FIRST matching rule.
        """
        for rule in self.rules:
            if rule.matches(facts):
                return rule.fire(facts)

        # Safety net: this should rarely trigger because we always
        # include a catch-all rule, but it's good practice to have one.
        return {
            "action": "idle",
            "rule_name": "default_idle",
            "reason": "No rule matched, so the enemy waits cautiously.",
        }
