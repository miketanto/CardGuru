"""Render a puzzle's board state as the model turn's prompt.

The encoder is the seam between game state and language. Two modes, which
are the first two benchmark arms:

  bare       what a human sees looking at the board: life totals, permanents
             with printed stats and tapped state, the hand with mana costs
             and oracle text. No advice, no arithmetic done for the model.

  annotated  bare + the computed layer (clock, connect-verdicts, windows) —
             PokeChamp's "turns to KO" trick. Arrives in P2; requesting it
             before then is an error rather than a silent fallback to bare,
             so no run can mislabel its arm.

Card facts come from the card store. A card the store cannot resolve renders
with its name and a `[stats unknown]` marker instead of failing the run:
the agent is graded by the engine, not by the prompt's completeness, and a
degraded prompt is itself informative (the engine knows cards the tier
pools should never include).
"""
from __future__ import annotations

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

    def render(self, spec: dict, mode: str = "bare") -> str:
        if mode not in MODES:
            raise ValueError(f"unknown mode '{mode}'")
        if mode == "annotated":
            raise NotImplementedError("annotated rendering lands in P2; "
                                      "run arm (a)/(b) prompts as 'bare'")
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
        return "\n".join(out)
