"""Provisional tier-1 scenario runner: combat arithmetic, no rules engine.

This exists so puzzle grading has an instrument before an XMage checkout is
configured. It executes exactly the slice of the scenario vocabulary that
tier-1 lethal puzzles use — direct-damage spells at a player, attacks into a
defender with no legal blocks — with the SAME damage model the generator
uses to prove a win exists. Everything outside that slice is a loud error,
never a guess: an unsupported action here fails the run exactly the way an
unscripted decision fails strict-choose XMage.

Simplifications, stated once and carried in every outcome as
`"engine": "local-combat"` so a provisional grade can never be mistaken for
an engine-verified one:

  - Mana is color-blind: a cast taps `cmc` untapped lands. Generated puzzles
    use mono-color boards precisely so this cannot change a verdict.
  - Battlefield creatures may attack (no summoning sickness), matching the
    XMage test-base convention for setup-placed permanents.
  - The defender must have NO untapped creatures. Blocks are decisions, and
    this runner adjudicates no decisions; a puzzle that allows blocks is
    outside its slice and errors.
  - Damage spells are recognized only as "deals N damage" with a player
    target; N comes from the card's oracle text in the card store, not from
    a hand-kept table.

`run_scenarios(specs)` takes scenario DICTS (not paths — nothing here needs
the JVM's file handoff) and returns outcome dicts shaped like the driver's:
id, status, engine, state {life, battlefield [{name, tapped, power,
toughness}], graveyard, hand_count}.
"""
from __future__ import annotations

import re

_DEALS = re.compile(r"deals (\d+) damage to (any target|target player|"
                    r"target creature or player)", re.IGNORECASE)

LAND_TYPES = ("Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes")


class LocalRunner:
    def __init__(self, store):
        """`store` is a CardStore (cardstore.CardStore.open(...))."""
        if store is None:
            raise RuntimeError("local runner needs the card store "
                               "(build it with: python -m cardguru cardstore)")
        self.store = store

    # -- card facts ---------------------------------------------------------
    def _row(self, name: str):
        row = self.store.resolve(name)
        if row is None:
            raise _Unsupported(f"unknown card '{name}'")
        return row

    def _pt(self, name: str) -> tuple[int, int]:
        row = self._row(name)
        try:
            return int(row["power"]), int(row["toughness"])
        except (TypeError, ValueError):
            raise _Unsupported(f"non-numeric power/toughness on '{name}'")

    def burn_damage(self, name: str) -> int:
        m = _DEALS.search(self._row(name)["oracle_text"] or "")
        if not m:
            raise _Unsupported(f"'{name}' is not a recognized damage spell")
        return int(m.group(1))

    def cmc(self, name: str) -> int:
        return int(self._row(name)["cmc"] or 0)

    def is_creature(self, name: str) -> bool:
        return "Creature" in (self._row(name)["type_line"] or "")

    def is_land(self, name: str) -> bool:
        return "Land" in (self._row(name)["type_line"] or "")

    # -- execution ----------------------------------------------------------
    def run_scenarios(self, specs: list[dict]) -> list[dict]:
        return [self._run_one(spec) for spec in specs]

    def _run_one(self, spec: dict) -> dict:
        try:
            return self._execute(spec)
        except _Unsupported as e:
            return {"id": spec.get("id"), "status": "error",
                    "error": f"local-combat runner: {e}",
                    "engine": "local-combat", "state": None}

    def _execute(self, spec: dict) -> dict:
        boards = {p: _Board(spec["players"].get(p, {}), self)
                  for p in ("A", "B")}
        if boards["B"].untapped_creatures():
            raise _Unsupported("defender has untapped creatures; blocks are "
                               "decisions this runner cannot adjudicate")
        attackers: list[str] = []
        for act in spec.get("actions", []):
            do = act.get("do")
            if do == "wait_stack":
                continue
            if do == "attack":
                name = act.get("attacker")
                if not boards["A"].has_untapped(name):
                    raise _Unsupported(f"no untapped '{name}' to attack with")
                boards["A"].tap(name)
                attackers.append(name)
            elif do == "cast":
                self._cast(act, boards)
            else:
                raise _Unsupported(f"action '{do}' outside the tier-1 slice")
        for name in attackers:
            power, _ = self._pt(name)
            boards["B"].life -= power
        return {"id": spec.get("id"), "status": "executed", "error": None,
                "engine": "local-combat",
                "state": {p: boards[p].dump() for p in ("A", "B")}}

    def _cast(self, act: dict, boards: dict):
        name, player = act.get("card"), act.get("player")
        if player != "A":
            raise _Unsupported("only player A acts in a puzzle line")
        board = boards[player]
        if name not in board.hand:
            raise _Unsupported(f"'{name}' is not in hand")
        dmg = self.burn_damage(name)
        target = act.get("target_player")
        if target not in ("A", "B"):
            raise _Unsupported(f"cast '{name}' needs target_player A|B")
        cost = self.cmc(name)
        if board.untapped_lands() < cost:
            raise _Unsupported(f"cannot pay {{{cost}}} for '{name}': only "
                               f"{board.untapped_lands()} untapped lands")
        board.tap_lands(cost)
        board.hand.remove(name)
        board.graveyard.append(name)
        boards[target].life -= dmg


class _Unsupported(Exception):
    pass


class _Board:
    def __init__(self, block: dict, runner: LocalRunner):
        self.runner = runner
        self.life = block.get("life", 20)
        self.hand = list(block.get("hand", []))
        self.graveyard = list(block.get("graveyard", []))
        self.perms: list[dict] = []
        for entry in block.get("battlefield", []):
            for _ in range(entry.get("count", 1)):
                self.perms.append({"name": entry["card"],
                                   "tapped": bool(entry.get("tapped", False))})

    def _is(self, kind, perm) -> bool:
        return getattr(self.runner, kind)(perm["name"])

    def untapped_creatures(self):
        return [p for p in self.perms
                if self._is("is_creature", p) and not p["tapped"]]

    def untapped_lands(self) -> int:
        return sum(1 for p in self.perms
                   if self._is("is_land", p) and not p["tapped"])

    def has_untapped(self, name) -> bool:
        return any(p["name"] == name and not p["tapped"] for p in self.perms)

    def tap(self, name):
        for p in self.perms:
            if p["name"] == name and not p["tapped"]:
                p["tapped"] = True
                return

    def tap_lands(self, n: int):
        for p in self.perms:
            if n and self._is("is_land", p) and not p["tapped"]:
                p["tapped"] = True
                n -= 1

    def dump(self) -> dict:
        out = []
        for p in self.perms:
            entry = {"name": p["name"], "tapped": p["tapped"]}
            if self.runner.is_creature(p["name"]):
                power, tough = self.runner._pt(p["name"])
                entry["power"], entry["toughness"] = power, tough
            out.append(entry)
        return {"life": self.life, "battlefield": out,
                "graveyard": list(self.graveyard),
                "hand_count": len(self.hand)}
