"""Render a puzzle's board state as the model turn's prompt.

The encoder is the seam between game state and language. Two modes, which
are the first two benchmark arms:

  bare       what a human sees looking at the board: life totals, permanents
             with printed stats and tapped state, the hand with mana costs
             and oracle text. No advice, no arithmetic done for the model.

  annotated  bare + the computed layer — PokeChamp's "turns to KO" trick.
             Facts only, never advice: full-attack damage and the shortfall
             against the opponent's life, untapped-land arithmetic, and a
             per-spell verdict (damage, what it may legally target, whether
             it is castable now). Verdicts come from the SAME oracle-text
             machinery the graders use, so the annotation layer can never
             disagree with the instrument that scores the answer. The
             annotations state what is true; which line to take stays
             entirely the model's problem.

Card facts come from the card store. A card the store cannot resolve renders
with its name and a `[stats unknown]` marker instead of failing the run:
the agent is graded by the engine, not by the prompt's completeness, and a
degraded prompt is itself informative (the engine knows cards the tier
pools should never include).
"""
from __future__ import annotations

from .localrunner import _DEALS          # "deals N damage to any target/…"
from .puzzlegen import _CREATURE_ONLY    # "deals N damage to target creature"

MODES = ("bare", "annotated")


class Encoder:
    def __init__(self, store):
        self.store = store

    def _card_line(self, name: str, tapped: bool | None = None,
                   with_text: bool = False) -> str:
        row = self.store.resolve(name) if self.store else None
        bits = [name]
        if row is None:
            bits.append("[stats unknown]")
        else:
            if row["mana_cost"]:
                bits.append(row["mana_cost"])
            if row["power"] is not None and row["toughness"] is not None:
                bits.append(f"{row['power']}/{row['toughness']}")
            type_line = row["type_line"] or ""
            if type_line:
                bits.append(f"— {type_line}")
        if tapped:
            bits.append("(TAPPED)")
        line = "  - " + " ".join(bits)
        if with_text and row is not None and row["oracle_text"]:
            text = " ".join(row["oracle_text"].split())
            line += f"\n      text: {text}"
        return line

    def _zone(self, title: str, entries: list, tapped_aware: bool,
              with_text: bool) -> list[str]:
        if not entries:
            return [f"{title}: (empty)"]
        lines = [f"{title}:"]
        for e in entries:
            if isinstance(e, dict):
                name, count = e["card"], e.get("count", 1)
                tapped = e.get("tapped", False) if tapped_aware else None
            else:
                name, count, tapped = e, 1, None
            for _ in range(count):
                lines.append(self._card_line(name, tapped=tapped,
                                             with_text=with_text))
        return lines

    # -- the computed layer --------------------------------------------------

    def _is(self, kind: str, name: str) -> bool:
        row = self.store.resolve(name) if self.store else None
        return bool(row and kind in (row["type_line"] or ""))

    def _spell_fact(self, name: str, lands: int) -> str:
        row = self.store.resolve(name) if self.store else None
        if row is None:
            return f"- {name}: unknown to the card store"
        text = row["oracle_text"] or ""
        cmc = int(row["cmc"] or 0)
        castable = ("castable now" if cmc <= lands
                    else f"NOT castable: costs {cmc}, {lands} untapped lands")
        m = _DEALS.search(text)
        if m:
            return (f"- {name} ({row['mana_cost']}): {m.group(1)} damage, "
                    f"may target a player; {castable}")
        m = _CREATURE_ONLY.search(text)
        if m and "any target" not in text.lower():
            return (f"- {name} ({row['mana_cost']}): {m.group(1)} damage, "
                    f"targets creatures ONLY — cannot be aimed at a player; "
                    f"{castable}")
        return f"- {name} ({row['mana_cost']}): {castable}"

    def _annotations(self, spec: dict) -> list[str]:
        a, b = spec["players"].get("A", {}), spec["players"].get("B", {})

        def perms(block, want, untapped_only=False):
            out = []
            for e in block.get("battlefield", []):
                if not self._is(want, e["card"]):
                    continue
                if untapped_only and e.get("tapped"):
                    continue
                out += [e["card"]] * e.get("count", 1)
            return out

        attackers = perms(a, "Creature", untapped_only=True)
        total = 0
        for name in attackers:
            row = self.store.resolve(name)
            try:
                total += int(row["power"])
            except (TypeError, ValueError):
                pass
        lands = len(perms(a, "Land", untapped_only=True))
        blockers = perms(b, "Creature", untapped_only=True)
        life = b.get("life", 20)
        out = ["", "COMPUTED (facts derived by the engine tooling — "
                   "not advice):",
               f"- your full attack: {total} combat damage"
               + (" (opponent has no untapped creatures; nothing can block)"
                  if not blockers else
                  f" (opponent has {len(blockers)} untapped creature(s))"),
               f"- opponent at {life}: a full attack alone leaves them at "
               f"{life - total}",
               f"- your untapped lands: {lands}"]
        hand = a.get("hand", [])
        out += [self._spell_fact(name, lands) for name in hand]
        if hand:
            costs = []
            for name in hand:
                row = self.store.resolve(name)
                costs.append(int(row["cmc"] or 0) if row else 0)
            if sum(costs) > lands:
                out.append(f"- total costs {sum(costs)} > {lands} untapped "
                           "lands: you cannot cast everything")
        return out

    def render(self, spec: dict, mode: str = "bare") -> str:
        if mode not in MODES:
            raise ValueError(f"unknown mode '{mode}'")
        players = spec["players"]
        a, b = players.get("A", {}), players.get("B", {})
        out = [
            f"It is turn {spec['turn']}. You are player A, in your "
            "precombat main phase with priority. Player B is the opponent.",
            "",
            f"YOU (player A) — life {a.get('life', 20)}",
        ]
        out += self._zone("your battlefield", a.get("battlefield", []),
                          tapped_aware=True, with_text=True)
        out += self._zone("your hand", a.get("hand", []),
                          tapped_aware=False, with_text=True)
        out += ["", f"OPPONENT (player B) — life {b.get('life', 20)}"]
        out += self._zone("their battlefield", b.get("battlefield", []),
                          tapped_aware=True, with_text=True)
        if b.get("hand"):
            out += self._zone("their hand (known)", b["hand"],
                              tapped_aware=False, with_text=False)
        if mode == "annotated":
            out += self._annotations(spec)
        return "\n".join(out)
