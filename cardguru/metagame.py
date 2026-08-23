"""Meta Lab meta-deck mode: sideboard planning against a real metagame.

plan/product.md lists this surface as blocked on "meta decklists from
MTGGoldfish/Melee — network-gated". It is no longer blocked: MetaSurf exports a
metagame snapshot (archetype shares + a centroid-representative decklist per
archetype, classified by its rules engine) and this module consumes it.

What it computes, per candidate answer card in your colors:

- which (archetype, key threat) pairs it actually answers, with the reason —
  every verdict comes from `find_answers`, so "Lightning Bolt does not answer a
  5-toughness threat" is a computed fact, not a heuristic;
- **weighted coverage**: the share of the metagame whose key threats it answers,
  summing `meta_share` over archetypes where it works;
- a greedy N-slot sideboard whose marginal gain is measured in metagame share
  rather than card count.

Deliberately NOT modelled (state them, don't hide them): matchup win rates —
a card that answers a threat is not the same as a card that wins the matchup;
mana costs and curve fit; how many copies to run; and sideboarding plans (what
comes out). This ranks *mechanical answer coverage* and nothing more.
"""
from __future__ import annotations

import json


def load_snapshot(path: str) -> dict:
    """Read a MetaSurf metagame export. Validated loudly: a snapshot missing
    shares or decklists would silently produce a meaningless ranking."""
    with open(path, encoding="utf-8") as fh:
        snap = json.load(fh)
    if not isinstance(snap, dict) or "archetypes" not in snap:
        raise ValueError(f"{path}: not a metagame snapshot (no 'archetypes' key)")
    for entry in snap["archetypes"]:
        for field in ("archetype", "meta_share", "representative"):
            if field not in entry:
                raise ValueError(f"{path}: archetype entry missing {field!r}")
        if not entry["representative"].get("mainboard"):
            raise ValueError(f"{path}: {entry['archetype']} has an empty mainboard")
    return snap


def _decklist(entry: dict) -> list[tuple[str, int]]:
    return [(name, int(count)) for name, count in entry["representative"]["mainboard"]]


def analyze_meta(idx, by_name: dict, snapshot: dict, colors: set[str] | None,
                 token_scripts: dict | None = None, top_threats: int = 5,
                 progress=None, played_only: bool = True) -> dict:
    """Run the answer engine against every archetype in the snapshot.

    Returns per-archetype detail plus `answers`: card -> the weighted coverage
    record used for ranking.

    `played_only` restricts candidates to cards the snapshot records as actually
    played in the format+window. This matters more than it looks: mechanically,
    every bounce spell ever printed answers every creature, so without the prior
    the ranking is a tie between hundreds of unplayable commons. The play-rate
    table is a format-legality and viability filter first, a quality signal
    second. It is circular by construction (popular cards stay popular), which
    is exactly why it re-ranks and never proposes — the mechanical layer decides
    what *works*, this decides what is *real*.
    """
    from .threats import analyze_opponent

    play_rates = snapshot.get("play_rates") or {}
    if played_only and not play_rates:
        raise ValueError(
            "snapshot has no play_rates: re-export with a MetaSurf build that "
            "includes the prior, or pass played_only=False and read the ranking "
            "as mechanical-only"
        )

    per_archetype = []
    # card -> {archetype -> {"share", "threats": {threat: reason}}}
    hits: dict[str, dict[str, dict]] = {}

    for entry in snapshot["archetypes"]:
        name, share = entry["archetype"], float(entry["meta_share"])
        if progress:
            progress(name, share)
        res = analyze_opponent(idx, by_name, None, _decklist(entry), colors,
                               token_scripts=token_scripts,
                               top_threats=top_threats)
        threats = []
        for surgical in res["surgical"]:
            threat = surgical["threat"]
            threats.append({"threat": threat,
                            "centrality": surgical["centrality"],
                            "answers": len(surgical["all_answers"])})
            # all_answers, NOT answers: the latter is a 5-card display list
            # pre-sorted by cheapness, which would silently bias every ranking
            # below toward one-mana filler.
            for card, answer in surgical["all_answers"].items():
                if played_only and card not in play_rates:
                    continue
                rec = hits.setdefault(card, {}).setdefault(
                    name, {"share": share, "threats": {}, "classes": set()})
                rec["threats"].setdefault(threat, answer["reason"])
                rec["classes"].add(answer["class"])
        per_archetype.append({
            "archetype": name,
            "meta_share": share,
            "decks": entry.get("decks"),
            "gameplan": res.get("gameplan"),
            "key_threats": [t for t, _s in res["key_threats"]],
            "threat_detail": threats,
            "coverage_answers": res.get("coverage_answers", []),
        })

    answers = {}
    for card, by_arch in hits.items():
        weighted = sum(rec["share"] for rec in by_arch.values())
        rate = play_rates.get(card) or {}
        classes = sorted({c for rec in by_arch.values() for c in rec["classes"]})
        answers[card] = {
            "classes": classes,
            # A counter answers every threat in the abstract but only while it
            # is on the stack; on-board answers deal with a resolved permanent.
            # Coverage saturates on catch-alls, so this flag is what keeps the
            # ranking readable rather than a 12-way tie.
            "stack_only": classes == ["counter_spell"],
            "card": card,
            "weighted_coverage": weighted,
            "archetypes": sorted(by_arch),
            "n_archetypes": len(by_arch),
            "play_decks": rate.get("decks", 0),
            "play_share": rate.get("deck_share", 0.0),
            "side_copies": rate.get("side_copies", 0),
            "detail": {a: rec["threats"] for a, rec in sorted(by_arch.items())},
        }

    return {
        "format": snapshot.get("format"),
        "window": snapshot.get("window"),
        "covered_share": sum(a["meta_share"] for a in per_archetype),
        "archetypes": per_archetype,
        "answers": answers,
    }


def rank_answers(analysis: dict, limit: int = 25,
                 on_board_only: bool = False) -> list[dict]:
    """Best single cards by share of the metagame they answer.

    KNOWN LIMITATION, stated rather than hidden: this metric **saturates**. A
    counterspell mechanically answers every threat in the field, so every
    catch-all ties at the maximum and the ordering below the tie is carried
    entirely by play rate, not by mechanics. `on_board_only` drops answers that
    work only on the stack, which is the difference between "I can stop this"
    and "I can deal with this once it has resolved" — usually the question a
    sideboard slot is actually answering.
    """
    rows = analysis["answers"].values()
    if on_board_only:
        rows = [a for a in rows if not a.get("stack_only")]
    return sorted(
        rows,
        key=lambda a: (
            -a["weighted_coverage"],
            -a.get("play_share", 0.0),   # break mechanical ties by real play
            -a["n_archetypes"],
            a["card"],
        ),
    )[:limit]


def greedy_sideboard(analysis: dict, slots: int = 15,
                     on_board_only: bool = False) -> list[dict]:
    """Greedy max-coverage selection over (archetype, threat) pairs.

    Each pair is worth its archetype's meta share divided by the number of key
    threats that archetype has, so answering one of five key threats is worth
    a fifth of that matchup rather than all of it. Greedy is not optimal for
    max-coverage, but it is the standard 1-1/e approximation and — unlike an
    exact solve — the pick order is itself the useful output: each slot's
    marginal gain is visible.
    """
    weight: dict[tuple[str, str], float] = {}
    for arch in analysis["archetypes"]:
        threats = arch["key_threats"]
        if not threats:
            continue
        per = arch["meta_share"] / len(threats)
        for threat in threats:
            weight[(arch["archetype"], threat)] = per

    covers: dict[str, set[tuple[str, str]]] = {}
    for card, rec in analysis["answers"].items():
        if on_board_only and rec.get("stack_only"):
            continue
        pairs = {
            (arch, threat)
            for arch, threats in rec["detail"].items()
            for threat in threats
        }
        covers[card] = {p for p in pairs if p in weight}

    chosen: list[dict] = []
    remaining = set(weight)
    for _ in range(slots):
        best_card, best_gain, best_pairs, best_play = None, 0.0, set(), -1.0
        for card in sorted(covers):
            pairs = covers[card] & remaining
            gain = sum(weight[p] for p in pairs)
            play = analysis["answers"][card].get("play_share", 0.0)
            # equal mechanical gain -> prefer the card the format actually plays
            if gain > best_gain or (gain == best_gain and gain > 0 and play > best_play):
                best_card, best_gain, best_pairs, best_play = card, gain, pairs, play
        if not best_card or best_gain <= 0:
            break
        remaining -= best_pairs
        chosen.append({
            "card": best_card,
            "marginal_gain": best_gain,
            "covers": sorted(best_pairs),
        })
    total = sum(weight.values())
    cumulative = 0.0
    for pick in chosen:
        cumulative += pick["marginal_gain"]
        pick["cumulative_coverage"] = cumulative / total if total else 0.0
    return chosen
