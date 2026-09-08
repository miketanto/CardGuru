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

import hashlib
import json
import os
import re
import sys

from .validate import Ontology, validate

# Default is the cheapest current model, chosen deliberately for cost while the
# compiler is being smoke-tested. Override with --model or CARDGURU_MODEL.
#   haiku-4.5  $1 / $5   per Mtok   (5x cheaper than opus-5 on both sides)
#   sonnet-5   $3 / $15  per Mtok
#   opus-5     $5 / $25  per Mtok
MODEL = os.environ.get("CARDGURU_MODEL", "claude-haiku-4-5")

# $ per input / output token, for the spend line printed after each call.
PRICING = {
    "claude-haiku-4-5": (1.00e-6, 5.00e-6),
    "claude-sonnet-5": (3.00e-6, 15.00e-6),
    "claude-opus-5": (5.00e-6, 25.00e-6),
}

# The queries are small JSON objects; 2000 was headroom we never use.
MAX_TOKENS = 1024

# Prompt caching is a no-op here and that is not a bug: the system prompt is
# ~2.7k tokens and Haiku 4.5's minimum cacheable prefix is 4096, so the marker
# below silently never creates an entry (cache_creation_input_tokens stays 0).
# It starts working if the model changes to sonnet/opus (1024 / 512 minimum).
# The real cost lever at this size is the on-disk cache in compile_question.
CACHE_DIR = os.environ.get("CARDGURU_COMPILE_CACHE", "data/compile_cache")

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
  {"hook": "name"}    semantic facet (makes_tokens, sac_outlet, gains_life, ...)
  {"role": "name"}    deckbuilding role (card_draw, ramp, targeted_removal,
                      sweepers); suffix ":engine" or ":one_shot" to require
                      repeatability, e.g. "card_draw:engine"

NodeSpec fields (AND-ed): kind ("A" spell/activated line, "T" trigger,
"S" static, "R" replacement, "K" keyword, "SVar" sub-ability, "SVarValue"
raw value), api (effect name), apiKind ("SP" spell / "AB" activated / "DB"
sub-ability), mode (trigger/static mode), keyword, count (Count$ expression
on SVarCount), value (raw string on SVarValue), params ({ParamName: VP}).

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
- CARD FIELDS ARE FORGE'S RAW FIELDS. Get these wrong and you silently return
  zero cards, because one empty clause inside {"all": [...]} zeroes everything.
  * "types" is ONLY the type line: "Instant", "Creature Human Wizard",
    "Legendary Enchantment". It NEVER contains colors. {"card": {"types":
    {"contains": "Blue"}}} matches 0 cards. Do not write it.
  * COLOR lives in "manaCost", as letters: "U U", "1 U", "W", "2 W U".
    White-or-blue is {"card": {"manaCost": {"regex": "[WU]"}}}.
    Colorless/no cost is manaCost "no cost" or absent.
  * MANA VALUE IS NOT NUMERICALLY COMPARABLE. There is no cmc/mv field and no
    < or <= operator — manaCost is a plain string. Approximate a cheap spell
    with a regex bounding generic and pips, e.g. 3-or-less is
    {"card": {"manaCost": {"regex": "^(([0-3]( |$))|)([WUBRG] ?){0,3}$"}}}.
    Say in your query that this is an approximation if asked to be exact.
- A STATIC IS NOT A CHAIN. Prohibitions, taxes, anthems and other continuous
  effects are a single node describing what the card DOES while it is on the
  battlefield. There is no trigger feeding them, so do not wrap one in a
  {"chain": {"from": {"kind": "T"}, ...}} — that asks for the rare case where a
  trigger creates the static, and drops the ordinary cards you wanted.
  "Creatures that stop opponents casting spells" is
    {"all": [{"card": {"types": {"contains": "Creature"}}},
             {"node": {"mode": "CantBeCast"}}]}
  not a chain. Prohibition modes: CantBeCast, CantBeActivated, CantAttack,
  CantPlayLand, CantTarget.
- SYMMETRIC EFFECTS STILL AFFECT OPPONENTS. The prohibited player is the
  "Caster" param (NOT ValidPlayer), but only one-sided cards set it. Meddling
  Mage, Sanctum Prelate and Archon of Emeria stop everyone, so they have no
  Caster — and adding {"Caster": {"contains": "Opponent"}} to a question about
  "opponents" drops exactly the cards a player means. Leave Caster off unless
  the question explicitly asks for one-sided / asymmetric / "only opponents"
  effects. The same applies to any Valid*/Activator player filter.
- DON'T PIN kind UNLESS YOU NEED IT. A mode can live on a plain static (kind
  "S") or on an Effect a spell creates, so adding {"kind": "S"} to a mode
  query silently drops the latter — 11 of the 65 CantBeCast creatures. Match
  on mode/api alone unless the question really is about the ability's form.
- FUNCTIONAL CATEGORIES: use {"hook": "..."} instead of guessing at the
  mechanisms. A word like "disruption", "removal", or "ramp" describes what a
  card ACHIEVES, and Forge expresses each of those several structurally
  unrelated ways — enumerating them by hand silently misses cards. "Counters or
  disrupts opponents' spells" is {"hook": "disrupts_spells"}, which covers
  countering, exiling a spell off the stack, Airbend, and opponent-facing cost
  taxes; writing {"node": {"api": "Counter"}} alone misses Aven Interrupter and
  Aang, Swift Savior. Check the hook list before hand-rolling an {"any": [...]}
  over several APIs.
- Prefer FEWER card-level clauses. A mechanical question is answered by the
  graph; attribute filters only narrow it. If unsure whether an attribute
  clause is expressible, leave it out rather than emitting one that matches
  nothing — a slightly-too-broad answer beats an empty one.
- Doubling/replacement of counters mirrors tokens: R Event "AddCounter"
  chains to api "ReplaceCounter" (MultiplyCounter is a different, rarer API).
- DOUBLING vs ADDING MORE is NOT a structural difference — Doubling Season and
  Hardened Scales have identical graph shape. The arithmetic operator lives in
  a kind "SVarValue" node's `value`: "ReplaceCount$CounterNum/Twice" doubles,
  "ReplaceCount$CounterNum/Plus.1" adds one. Same for damage multipliers
  (Furnace of Rath "/Twice" vs Torbran "/Plus.2"). To ask for doublers, add
  {"node": {"kind": "SVarValue", "value": {"contains": "/Twice"}}}. Never fall
  back to a card.oracle text regex for this — that is what the structural
  index exists to avoid.
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


def _shape_block(path: str = None) -> str:
    """Mined param-shape clusters, if `cardguru shapes` has been run.

    This is the derived replacement for hand-written 'convention' prose: it
    tells the compiler that one mode name can encode several distinct
    meanings, and which param selects each. Absent the artifact the prompt is
    unchanged, so nothing hard-depends on it.
    """
    from .shapes import digest, load

    shapes = load(path or os.environ.get("CARDGURU_SHAPES", "data/shapes.json"))
    if not shapes:
        return ""
    return (
        "PARAM SHAPES — a mode name is NOT one concept. Each line is a mode "
        "followed by the discriminating param combinations that actually occur "
        "and how many nodes carry each. Pick the shape matching the question: "
        "querying the bare mode conflates all of them.\n"
        + digest(shapes) + "\n\n")


def _family_block(path: str = None) -> str:
    """Mined disjunctive families, if `cardguru families` has been run.

    `_shape_block` above tells the compiler one mode name can mean several
    things. This tells it the reverse: one thing can be several names, and
    naming only the one you thought of is how a query silently answers a
    narrower question than it was asked.

    Set CARDGURU_FAMILIES=off to compile without it — that is the control arm
    of the A/B, and it has to be a switch rather than a deleted file because
    the file is also what `cardguru families` writes.
    """
    from .families import digest, load

    path = path or os.environ.get("CARDGURU_FAMILIES", "data/families.json")
    if path == "off":
        return ""
    fams = load(path)
    if not fams:
        return ""
    return (
        "DISJUNCTIVE FAMILIES — mined groups of api/mode names the data uses "
        "for ONE player-facing concept, labelled by the word Forge writes for "
        "them. When a question is about the word on the left, match the WHOLE "
        "group with {\"api\": {\"any\": [...]}} (or {\"mode\": {\"any\": "
        "[...]}}); naming one member drops the others and silently answers a "
        "narrower question. Members are alternatives, not steps of one "
        "ability, so a disjunction is always the right shape for them.\n"
        + digest(fams) + "\n\n")


def _hook_names() -> str:
    """The hook facets are only usable if the compiler knows they exist."""
    from .recommend import HOOKS
    return ", ".join(sorted(HOOKS))


def _role_names() -> str:
    from .deck import ROLES
    return ", ".join(sorted(ROLES))


def build_system_prompt(onto_data: dict, top_n: int = 80) -> str:
    def top(d, n):
        return ", ".join(list(d)[:n])
    vocab = (
        f"Effect APIs (by frequency): {top(onto_data['api'], top_n)}\n"
        f"Trigger modes: {top(onto_data['trigger_modes'], 60)}\n"
        f"Static modes: {top(onto_data['static_modes'], 40)}\n"
        f"Replacement events: {top(onto_data['replacement_events'], 34)}\n"
        f"Keywords: {top(onto_data['keywords'], 80)}\n"
        f"Common params: {top(onto_data['param_keys'], 100)}\n"
        f"{_shape_block()}"
        f"{_family_block()}"
        f"Semantic hooks (use with {{\"hook\": ...}}): {_hook_names()}\n"
        f"Deckbuilding roles (use with {{\"role\": ...}}, "
        f"optional :engine / :one_shot suffix): {_role_names()}\n"
    )
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
    def __init__(self, query, attempts, errors, hits=-1, checks=None,
                 exhausted=False):
        self.query = query          # validated query, or None
        self.attempts = attempts    # list of (raw_text, error_list)
        self.errors = errors        # last error list ([] on success)
        self.hits = hits            # result count of `query`, -1 if not executed
        self.checks = checks or []  # execution-signal kinds, in order
        # True when the retry budget ran out and `query` is the best candidate
        # rather than one the checker accepted.
        self.exhausted = exhausted

    @property
    def ok(self):
        return self.query is not None

    @property
    def repaired(self):
        """The execution loop rejected at least one earlier candidate."""
        return any(k != "ok" for k in self.checks)


def _cache_key(question: str, model: str, system: str, variant: str = "") -> str:
    """Key on everything that changes the answer, so a prompt or ontology edit
    invalidates the entry instead of serving a stale query.

    `variant` covers what is *not* in the system prompt: the execution-feedback
    configuration lives in the message turns, so without it an A/B of the repair
    loop would silently serve the other arm's cached answers.
    """
    h = hashlib.sha256()
    for part in (model, question.strip().lower(), system, variant):
        h.update(part.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:32]


def _cache_read(key: str):
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)["query"]
    except (OSError, ValueError, KeyError):
        return None       # a corrupt entry costs one API call, not a crash


def _cache_write(key: str, question: str, model: str, query: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp = os.path.join(CACHE_DIR, f".{key}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"question": question, "model": model, "query": query}, f, indent=1)
    os.replace(tmp, os.path.join(CACHE_DIR, f"{key}.json"))   # atomic


def _report_cost(response, model: str):
    """Print what the call cost. Spend you can't see is spend you can't control."""
    u = getattr(response, "usage", None)
    if u is None:
        return
    inp = getattr(u, "input_tokens", 0) or 0
    out = getattr(u, "output_tokens", 0) or 0
    cached = getattr(u, "cache_read_input_tokens", 0) or 0
    # Cache WRITES are billed at ~1.25x and land in their own field. Omitting
    # them made a cache-writing call look nearly free (in=14) when it had just
    # paid for ~8k tokens.
    written = getattr(u, "cache_creation_input_tokens", 0) or 0
    in_rate, out_rate = PRICING.get(model, (0.0, 0.0))
    cost = ((inp * in_rate) + (written * in_rate * 1.25)
            + (cached * in_rate * 0.1) + (out * out_rate))
    print(f"  [{model}] in={inp} out={out} "
          f"cache(w={written} r={cached})  ~${cost:.5f}", file=sys.stderr)
    return cost


def compile_question(question: str, ontology_path: str, client=None,
                     model: str = MODEL, max_retries: int = 2,
                     use_cache: bool = True, checker=None,
                     variant: str | None = None) -> CompileResult:
    """Compile NL -> validated DSL query. `client` defaults to a real
    anthropic.Anthropic(); inject a stub for tests.

    `checker` adds EXECUTION feedback to the retry loop. Without it the loop
    only ever sees `validate()` errors — syntax and vocabulary — so a query that
    parses, validates, and returns zero cards is indistinguishable from a
    correct one. A checker (see `cardguru.repair.ExecutionChecker`) is called
    with each validated query and returns an object with `.ok`, `.hits`,
    `.kind` and `.feedback`; a non-ok result is fed back as the next user turn
    exactly like a validation error.

    Two guards keep the loop from arguing with itself:
      * an advisory ("narrow") complaint is raised at most once per compile;
      * re-emitting the identical query after an advisory counts as the model
        standing by it, and is accepted.

    Successful compilations are cached on disk keyed by (model, question,
    system prompt, variant), so re-asking a question costs nothing. Results
    that only survived because the retry budget ran out are NOT cached — a
    later prompt fix should get a fresh attempt rather than inherit a bad
    answer. Pass use_cache=False to force a live call.
    """
    with open(ontology_path, encoding="utf-8") as f:
        onto_data = json.load(f)
    onto = Ontology(onto_data)
    system = build_system_prompt(onto_data)

    if variant is None:
        variant = f"exec:{getattr(checker, 'signals', 'on')}" if checker else "off"
    key = _cache_key(question, model, system, variant)
    if use_cache:
        cached_query = _cache_read(key)
        if cached_query is not None:
            print(f"  [cache hit] no API call", file=sys.stderr)
            return CompileResult(cached_query, [("<cached>", [])], [])

    if client is None:
        import anthropic
        client = anthropic.Anthropic()

    messages = [{"role": "user", "content": question}]
    attempts = []
    errors: list[str] = []
    checks: list[str] = []
    candidates: list[tuple[dict, int]] = []   # every validated query, with hits
    narrow_used = False
    last_query = None

    for _ in range(1 + max_retries):
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": system,
                     "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        )
        _report_cost(response, model)
        if response.stop_reason == "refusal":
            attempts.append(("<refusal>", ["model refused"]))
            return CompileResult(None, attempts, ["model refused"])
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            query = extract_json(text)
            errors = validate(query, onto)
        except (ValueError, json.JSONDecodeError) as e:
            query, errors = None, [f"unparseable response: {e}"]

        if errors:
            attempts.append((text, errors))
            messages += [
                {"role": "assistant", "content": text},
                {"role": "user", "content":
                    "That query failed validation:\n- " + "\n- ".join(errors) +
                    "\nEmit a corrected query as JSON only. Every exact api/mode/"
                    "keyword/param token must come from the vocabulary list."},
            ]
            continue

        if checker is None:
            attempts.append((text, []))
            if use_cache:
                _cache_write(key, question, model, query)
            return CompileResult(query, attempts, [])

        check = checker(query)
        checks.append(check.kind)
        candidates.append((query, check.hits))
        standing_by = check.kind == "narrow" and (narrow_used or query == last_query)
        if check.ok or standing_by:
            attempts.append((text, []))
            if use_cache:
                _cache_write(key, question, model, query)
            return CompileResult(query, attempts, [], hits=check.hits,
                                 checks=checks)

        attempts.append((text, [f"execution/{check.kind}: {check.hits} hits"]))
        narrow_used = narrow_used or check.kind == "narrow"
        last_query = query
        messages += [
            {"role": "assistant", "content": text},
            {"role": "user", "content": check.feedback},
        ]

    if candidates:
        # Budget exhausted with every candidate complained about. Prefer the
        # most recent one that at least returns something over one that returns
        # nothing; an empty answer is never the better of the two. This is a
        # tie-break, not ranking — sample-and-rerank is a separate change.
        nonzero = [q for q, h in candidates if h > 0]
        best = nonzero[-1] if nonzero else candidates[-1][0]
        hits = next((h for q, h in reversed(candidates) if q is best), -1)
        return CompileResult(best, attempts, [], hits=hits, checks=checks,
                             exhausted=True)
    return CompileResult(None, attempts, errors, checks=checks)
