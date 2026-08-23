"""Natural language -> mechanical-search DSL compiler.

An LLM (Claude) translates a user's question into a query DSL JSON object.
The mined ontology is both the compiler's vocabulary (embedded in the system
prompt) and its gate (cardguru.validate rejects out-of-vocabulary output, and
validation errors are fed back for a bounded number of retries).

The DSL is recursive, so structured-output schemas can't express it — we parse
JSON from the response text and rely on the validator, which is the stronger
check anyway.

Requires the `anthropic` package and credentials (ANTHROPIC_API_KEY or an
`ant auth login` profile).
"""
from __future__ import annotations

import json
import re

from .validate import Ontology, validate

MODEL = "claude-opus-5"

DSL_SPEC = """\
Queries are JSON objects, one operator per object:
  {"all": [Q, ...]}   every subquery matches
  {"any": [Q, ...]}   at least one matches
  {"not": Q}          negation
  {"node": NodeSpec}  some node in the card's ability graph matches
  {"chain": {"from": NodeSpec, "to": NodeSpec | [NodeSpec, ...], "via": [edgeType, ...]?}}
       a node matching `from` reaches node(s) matching `to` along ability-chain
       edges. A LIST of `to` specs means ALL must be reachable from the SAME
       `from` node — use this to say "one ability does both X and Y".
  {"keyword": "Name"} card has that keyword
  {"card": {"types"|"name"|"manaCost"|"oracle"|"pt": VP}} card-level attributes
  {"hook": "sac_outlet"} a validated semantic facet (closed list below). Prefer a
       hook over hand-rolling its structure when one covers the question.
  {"role": "card_draw"} a deckbuilding role (closed list below). Suffix
       ":engine" or ":one_shot" to demand repeatability, e.g. "card_draw:engine"
       for a recurring draw engine as opposed to a one-shot draw spell.

NodeSpec fields (AND-ed): kind ("A" spell/activated line, "T" trigger,
"S" static, "R" replacement, "K" keyword, "SVar" sub-ability), api (effect
name), apiKind ("SP" spell / "AB" activated / "DB" sub-ability), mode
(trigger/static mode), keyword, params ({ParamName: VP}).

VP (value predicate): "exact" | {"contains": s} | {"icontains": s} |
{"regex": r} | {"any": [VP, ...]} | true (param exists).

Conventions from the Forge card-script data this runs over:
- Triggers: T nodes with mode. ETB self-trigger: mode "ChangesZone" with
  params ValidCard containing "Card.Self" and Destination "Battlefield".
  Dies: same with Origin "Battlefield", Destination "Graveyard".
  Combat damage to a player: mode "DamageDone", params CombatDamage "True",
  ValidTarget containing "Player". Landfall: mode "ChangesZone" with
  ValidCard containing "Land", Destination "Battlefield".
  "An opponent draws": mode "Drawn" with ValidCard matching Opp(Ctrl|Own).
- Activated-ability costs are the "Cost" param on kind "A" apiKind "AB" nodes:
  sacrifice costs look like Sac<1/Creature>, discard like Discard<1/Card>,
  self-sacrifice Sac<1/CARDNAME>. Use {"contains"/"regex"} on Cost.
- Replacement effects: kind "R" with params Event (e.g. "Moved",
  "CreateToken", "AddCounter", "DamageDone") chaining via ReplaceWith.
- Fetching cards: api "ChangeZone" with params Origin/Destination zone names
  ("Library", "Battlefield", "Graveyard", "Exile", "Hand") and ChangeType
  selectors (type words like "Land", "Forest", "Creature").
- Effects: api names like Token, DealDamage, Draw, GainLife, LoseLife,
  PutCounter, Destroy, Mana, AddTurn, CopySpellAbility, Pump, Dig, Mill.
- Idioms: fog effects have their own api "Fog". Mass zone-changes
  (ChangeZoneAll) select what moves with ChangeType (not ValidCards — that
  is the DestroyAll family's param). Counterspells use TargetType$ Spell
  with ValidTgts naming what KIND of spell: unrestricted counters are
  ValidTgts "Card"; restricted ones are ValidTgts "Creature" etc.
- "Each opponent"/"each player" effects usually use the *All api variants
  (DamageAll with ValidPlayers, DestroyAll, TapAll) rather than the targeted
  api with a Defined param — query both with {"any": ...} when unsure.
- Doubling/replacement of counters mirrors tokens: R Event "AddCounter"
  chains to api "ReplaceCounter" (MultiplyCounter is a different, rarer API).
- Prefer chain over all-of-two-nodes when the question implies one ability
  does both things. Prefer exact api/mode strings from the vocabulary below;
  use params only when needed for precision.
"""

EXAMPLES = [
    ("creatures with a combat-damage-to-a-player trigger that creates a token",
     {"chain": {"from": {"kind": "T", "mode": {"any": ["DamageDone", "DamageDoneOnce"]},
                         "params": {"CombatDamage": "True", "ValidTarget": {"contains": "Player"}}},
                "to": {"api": "Token"}}}),
    ("cards that exile cards from the library and let you play them (impulse draw)",
     {"chain": {"from": {"kind": {"any": ["A", "T", "S", "R"]}},
                "to": [{"api": {"any": ["Dig", "DigUntil", "Mill"]},
                        "params": {"DestinationZone": {"contains": "Exile"}}},
                       {"mode": "Continuous", "params": {"MayPlay": "True"}}]}}),
    ("activated abilities that sacrifice a creature to add mana",
     {"node": {"apiKind": "AB", "api": {"any": ["Mana", "ManaReflected"]},
               "params": {"Cost": {"regex": "Sac<[^>]*Creature"}}}}),
    ("replacement effects that double token creation",
     {"chain": {"from": {"kind": "R", "params": {"Event": "CreateToken"}},
                "to": {"api": "ReplaceToken"}}}),
    ("spells or ETB triggers that search a land onto the battlefield",
     {"chain": {"from": {"kind": {"any": ["A", "T"]}},
                "to": {"api": "ChangeZone",
                       "params": {"Origin": "Library", "Destination": "Battlefield",
                                  "ChangeType": {"regex": "Land|Plains|Island|Swamp|Mountain|Forest"}}}}}),
    ("cards that give you an extra turn",
     {"node": {"api": "AddTurn"}}),
]


def build_system_prompt(onto_data: dict, top_n: int = 80,
                        param_keys_n: int | None = None) -> str:
    """Build the compiler's system prompt from the mined ontology.

    `param_keys_n` truncates the parameter vocabulary; None emits all of it.
    It defaults to None because truncation was measured to be actively harmful:
    frequency-ranking put `ValidPlayer` (rank 25) in the prompt and left
    `ValidPlayers` (rank 159) out, so every compilation of "damage to each
    opponent" used the wrong key on `DamageAll` — a query that validates clean,
    returns hits from its sibling branch, finds the witness, and silently
    matches nothing on the branch that mattered.

    Emitting the full list measured 0/5 -> 5/5 on that token choice, cut the
    dead-branch rate from 5.4% to 1.0%, and raised paraphrase consistency on the
    idiom-alternation stratum from 0.456 to 0.599.
    See eval/consistency/C3-ablation.md.
    """
    def top(d, n):
        return ", ".join(list(d) if n is None else list(d)[:n])
    vocab = (
        f"Effect APIs (by frequency): {top(onto_data['api'], top_n)}\n"
        f"Trigger modes: {top(onto_data['trigger_modes'], 60)}\n"
        f"Static modes: {top(onto_data['static_modes'], 40)}\n"
        f"Replacement events: {top(onto_data['replacement_events'], 34)}\n"
        f"Keywords: {top(onto_data['keywords'], 80)}\n"
        f"Common params: {top(onto_data['param_keys'], param_keys_n)}\n"
    )
    # Closed-label operators. These are the ONLY legal hook/role arguments, so
    # they are always listed in full — truncating them would make the operators
    # unusable rather than merely harder to use.
    try:
        from .recommend import HOOKS
        from .deck import ROLES
        vocab += (f"Hooks (for {{\"hook\": ...}}): {', '.join(sorted(HOOKS))}\n"
                  f"Roles (for {{\"role\": ...}}, optional :engine / :one_shot "
                  f"suffix): {', '.join(sorted(ROLES))}\n")
    except ImportError:  # pragma: no cover - concept libraries always present
        pass
    shots = "\n".join(
        f"Q: {q}\nA: {json.dumps(dsl)}" for q, dsl in EXAMPLES)
    return (
        "You compile natural-language Magic: The Gathering card-search "
        "questions into a mechanical-search query DSL that runs over per-card "
        "ability graphs parsed from Forge card scripts.\n\n"
        f"{DSL_SPEC}\n"
        "VOCABULARY (closed — exact-match api/mode/keyword/param values MUST "
        "come from these lists):\n" + vocab + "\n"
        "Examples:\n" + shots + "\n\n"
        "Respond with ONLY the query JSON object, no prose, no code fences."
    )


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text.strip())
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in response")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON in response")


class CompileResult:
    def __init__(self, query, attempts, errors):
        self.query = query          # validated query, or None
        self.attempts = attempts    # list of (raw_text, error_list)
        self.errors = errors        # last error list ([] on success)

    @property
    def ok(self):
        return self.query is not None


def compile_question(question: str, ontology_path: str, client=None,
                     model: str = MODEL, max_retries: int = 2) -> CompileResult:
    """Compile NL -> validated DSL query. `client` defaults to a real
    anthropic.Anthropic(); inject a stub for tests."""
    with open(ontology_path, encoding="utf-8") as f:
        onto_data = json.load(f)
    onto = Ontology(onto_data)
    system = build_system_prompt(onto_data)

    if client is None:
        import anthropic
        client = anthropic.Anthropic()

    messages = [{"role": "user", "content": question}]
    attempts = []
    errors: list[str] = []
    for _ in range(1 + max_retries):
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=[{"type": "text", "text": system,
                     "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        )
        if response.stop_reason == "refusal":
            attempts.append(("<refusal>", ["model refused"]))
            return CompileResult(None, attempts, ["model refused"])
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            query = extract_json(text)
            errors = validate(query, onto)
        except (ValueError, json.JSONDecodeError) as e:
            query, errors = None, [f"unparseable response: {e}"]
        attempts.append((text, errors))
        if not errors:
            return CompileResult(query, attempts, [])
        messages += [
            {"role": "assistant", "content": text},
            {"role": "user", "content":
                "That query failed validation:\n- " + "\n- ".join(errors) +
                "\nEmit a corrected query as JSON only. Every exact api/mode/"
                "keyword/param token must come from the vocabulary list."},
        ]
    return CompileResult(None, attempts, errors)
