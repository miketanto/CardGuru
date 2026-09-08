"""Run the compile loop with an in-session agent as the model turn.

`research/agent-compiler-poc.md` and `research/agent-compiler-round2.md` both
evaluated this pipeline using in-session agents instead of API calls. This
module makes that a repeatable mode of the eval harness rather than a manual
exercise, and it does so *without reimplementing the loop*.

The trick is that everything in `compile_question` except the model turn is
deterministic: the system prompt, the JSON extraction, the validator, the
execution checker, the retry bookkeeping. So a run is driven by replay:

    round 1   ReplayClient([])          -> raises OutOfAnswers, carrying the
                                          exact request the API would have got
              (an agent answers it)
    round 2   ReplayClient([answer1])   -> replays turn 1 for free, reaches the
                                          same state, and either finishes or
                                          raises again with the next request
    ...

Each round replays all prior turns at zero cost, so the loop that runs is the
production loop — same code path, same feedback text — with the model swapped
out. Nothing here is a parallel implementation that can drift.

State lives in one directory per run:

    <run>/system_prompt.md      the system prompt, written once (~8k tokens)
    <run>/state.json            {question_id: [answer_text, ...]}
    <run>/pending/<id>.md       a task file per question awaiting an answer
    <run>/answers/<id>.txt      where the agent writes the query JSON
"""
from __future__ import annotations

import json
import os
import types

PENDING = "pending"
ANSWERS = "answers"
STATE = "state.json"
SYSTEM = "system_prompt.md"


class OutOfAnswers(Exception):
    """The loop wants another model turn and the replay has none left.

    Carries the request verbatim, which is what gets handed to the agent.
    """

    def __init__(self, request: dict):
        super().__init__("replay exhausted; another model turn is needed")
        self.request = request


class ReplayClient:
    """Anthropic-client shape that serves canned texts, then raises.

    Deliberately not a mock: it satisfies the same contract `compile_question`
    uses against the real SDK, so the loop cannot tell the difference.
    """

    def __init__(self, answers: list[str]):
        self._answers = list(answers)
        self.requests: list[dict] = []
        self.messages = types.SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.requests.append(dict(kwargs, messages=list(kwargs["messages"])))
        if not self._answers:
            raise OutOfAnswers(self.requests[-1])
        block = types.SimpleNamespace(type="text", text=self._answers.pop(0))
        # usage=None makes _report_cost a no-op: there is no spend to report.
        return types.SimpleNamespace(content=[block], stop_reason="end_turn",
                                     usage=None)


class RunDir:
    """The on-disk state of one agent-driven eval run."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.join(path, PENDING), exist_ok=True)
        os.makedirs(os.path.join(path, ANSWERS), exist_ok=True)

    # -- state ------------------------------------------------------------
    def load_state(self) -> dict[str, list[str]]:
        p = os.path.join(self.path, STATE)
        if not os.path.exists(p):
            return {}
        with open(p, encoding="utf-8") as f:
            return json.load(f)

    def save_state(self, state: dict[str, list[str]]):
        tmp = os.path.join(self.path, ".state.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1)
        os.replace(tmp, os.path.join(self.path, STATE))

    def write_system_prompt(self, text: str):
        p = os.path.join(self.path, SYSTEM)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)

    # -- answers ----------------------------------------------------------
    def collect_answers(self, state: dict[str, list[str]]) -> int:
        """Fold any answer files into the state and clear the round.

        An answer file is raw model output — the agent may wrap it in fences or
        prose, exactly as a model would; `extract_json` handles that downstream,
        so nothing is cleaned up here. Cleaning it would make the replay kinder
        to the agent than the API is to the model.
        """
        adir = os.path.join(self.path, ANSWERS)
        n = 0
        for fn in sorted(os.listdir(adir)):
            qid, ext = os.path.splitext(fn)
            if ext not in (".txt", ".json"):
                continue
            with open(os.path.join(adir, fn), encoding="utf-8") as f:
                state.setdefault(qid, []).append(f.read())
            os.remove(os.path.join(adir, fn))
            pending = os.path.join(self.path, PENDING, f"{qid}.md")
            if os.path.exists(pending):
                os.remove(pending)
            n += 1
        return n

    def clear_pending(self):
        pdir = os.path.join(self.path, PENDING)
        for fn in os.listdir(pdir):
            os.remove(os.path.join(pdir, fn))

    def write_task(self, qid: str, question: str, request: dict, turn: int):
        """One self-contained task file for the agent."""
        msgs = request["messages"]
        lines = [
            f"# Compile task: `{qid}`  (turn {turn})", "",
            "You are the model turn of CardGuru's NL -> DSL compiler. Read the "
            f"system prompt in `../{SYSTEM}` — it is the compiler's full "
            "specification and closed vocabulary — then answer the conversation "
            "below exactly as that system prompt instructs.", "",
            f"**Write your answer to `../{ANSWERS}/{qid}.txt`** and nothing "
            "else. The answer is the query JSON object, no prose. Do not run "
            "searches, read the dataset, or look at the benchmark goldens: you "
            "are standing in for a single model call, and anything extra makes "
            "this run incomparable to the API runs.", "",
            "---", "", "## Conversation so far", "",
        ]
        for m in msgs:
            role = "USER" if m["role"] == "user" else "ASSISTANT (you, earlier)"
            lines += [f"### {role}", "", "```", m["content"], "```", ""]
        lines += [
            "---", "",
            "Reply to the last USER turn. If it reports that a previous query "
            "returned nothing, the per-clause hit counts tell you which single "
            "clause is empty — fix that clause and leave the others alone.", "",
        ]
        with open(os.path.join(self.path, PENDING, f"{qid}.md"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def pending_ids(self) -> list[str]:
        return sorted(os.path.splitext(f)[0]
                      for f in os.listdir(os.path.join(self.path, PENDING)))


def step(question: str, qid: str, answers: list[str], ontology_path: str,
         checker=None, max_retries: int = 2):
    """Replay one question's loop. Returns (result, request).

    Exactly one of the two is None: a `result` means the compile finished, a
    `request` means the next model turn is needed.
    """
    from .nl_compiler import compile_question

    client = ReplayClient(answers)
    try:
        res = compile_question(question, ontology_path, client=client,
                               model="agent", max_retries=max_retries,
                               use_cache=False, checker=checker,
                               variant="agent")
        return res, None
    except OutOfAnswers as e:
        return None, e.request
