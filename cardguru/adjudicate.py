"""Batch-run scenario JSON files through the XMage driver.

Copies scenarios into a temp dir, invokes the CardGuruScenarioRunner test in
the configured XMage checkout (env CARDGURU_MAGE_REPO or --mage-repo), and
collects the outcome JSONs. One maven/JVM invocation per batch.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

DRIVER_REL = "Mage.Tests/src/test/java/org/mage/test/serverside/CardGuruScenarioRunner.java"

PHASES = {"UPKEEP", "DRAW", "PRECOMBAT_MAIN", "BEGIN_COMBAT", "DECLARE_ATTACKERS",
          "DECLARE_BLOCKERS", "COMBAT_DAMAGE", "POSTCOMBAT_MAIN", "END_TURN"}
ACTIONS = {"cast", "play_land", "activate", "attack", "block", "wait_stack",
           "choice", "target", "mode"}
CHECKS = {"permanent_count", "exile_count", "graveyard_count", "hand_count", "battlefield_count",
          "life", "tapped", "power_toughness"}


def validate_scenario(spec: dict) -> list[str]:
    """Cheap client-side validation so obvious mistakes fail before the JVM."""
    errors = []
    if "players" not in spec or not isinstance(spec["players"], dict):
        errors.append("missing players")
    for key in spec.get("players", {}):
        if key not in ("A", "B"):
            errors.append(f"unknown player '{key}' (only A/B supported)")
    required = {"cast": ("player", "card"), "play_land": ("player", "card"),
                "activate": ("player", "ability"),
                "attack": ("player", "attacker", "turn"),
                "block": ("player", "blocker", "attacker", "turn"),
                "choice": ("player", "value"), "target": ("player", "value"),
                "mode": ("player", "value")}
    for i, a in enumerate(spec.get("actions", [])):
        if a.get("do") not in ACTIONS:
            errors.append(f"actions[{i}]: unknown do '{a.get('do')}'")
            continue
        if a["do"] in ("cast", "play_land", "activate", "wait_stack") \
                and a.get("phase") not in PHASES:
            errors.append(f"actions[{i}]: bad phase '{a.get('phase')}'")
        for field in required.get(a["do"], ()):
            if a.get(field) in (None, ""):
                errors.append(f"actions[{i}]: {a['do']} missing '{field}'")
    stop = spec.get("stop")
    if not stop or stop.get("phase") not in PHASES or "turn" not in stop:
        errors.append("missing/invalid stop {turn, phase}")
    for i, x in enumerate(spec.get("expect", [])):
        if x.get("check") not in CHECKS:
            errors.append(f"expect[{i}]: unknown check '{x.get('check')}'")
    return errors


def ensure_driver(mage_repo: str) -> None:
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "driver", "CardGuruScenarioRunner.java")
    dst = os.path.join(mage_repo, DRIVER_REL)
    if not os.path.exists(dst) or \
            open(src, encoding="utf-8").read() != open(dst, encoding="utf-8").read():
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)


def run_scenarios(paths: list[str], mage_repo: str | None = None,
                  timeout: int = 1800) -> list[dict]:
    mage_repo = mage_repo or os.environ.get("CARDGURU_MAGE_REPO")
    if not mage_repo or not os.path.isdir(mage_repo):
        raise RuntimeError("XMage checkout not found: set CARDGURU_MAGE_REPO or --mage-repo")

    specs = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            spec = json.load(f)
        errs = validate_scenario(spec)
        if errs:
            raise ValueError(f"{p}: " + "; ".join(errs))
        specs.append((p, spec))

    ensure_driver(mage_repo)
    with tempfile.TemporaryDirectory(prefix="cardguru-scn-") as tmp:
        indir = os.path.join(tmp, "in")
        outdir = os.path.join(tmp, "out")
        os.makedirs(indir)
        for p, _ in specs:
            shutil.copyfile(p, os.path.join(indir, os.path.basename(p)))
        proc = subprocess.run(
            ["mvn", "-q", "-pl", "Mage.Tests", "test",
             "-Dtest=CardGuruScenarioRunner", "-DfailIfNoTests=false",
             f"-Dcardguru.scenarios.dir={indir}", f"-Dcardguru.out.dir={outdir}"],
            cwd=mage_repo, capture_output=True, text=True, timeout=timeout)
        results = []
        for p, _ in specs:
            outfile = os.path.join(
                outdir, os.path.basename(p).replace(".json", ".out.json"))
            if os.path.exists(outfile):
                with open(outfile, encoding="utf-8") as f:
                    results.append(json.load(f))
            else:
                results.append({
                    "id": os.path.basename(p), "status": "error",
                    "error": "driver produced no outcome "
                             f"(maven rc={proc.returncode}); tail: "
                             + proc.stdout[-800:]})
        return results


class MageServer:
    """Persistent XMage scenario server: pay the JVM warmup once.

    Wraps the driver's spool-directory server mode. `run_scenarios` takes
    scenario DICTS and returns outcomes in order, at the marginal per-
    scenario cost only (~0.1-12s) instead of ~40s of maven+DB warmup per
    batch. The protocol is file-based (tmp-write then atomic rename both
    ways), so nothing about the driver's execution path changes — server
    grading is batch grading with the warmup amortized.

    Use as a context manager, or call close(); an atexit hook covers the
    forgetful path so no orphan JVMs outlive the Python process.
    """

    def __init__(self, mage_repo: str | None = None, warmup_timeout: int = 300):
        import atexit
        import time as _time

        self.mage_repo = mage_repo or os.environ.get("CARDGURU_MAGE_REPO")
        if not self.mage_repo or not os.path.isdir(self.mage_repo):
            raise RuntimeError("XMage checkout not found: set "
                               "CARDGURU_MAGE_REPO or pass mage_repo")
        ensure_driver(self.mage_repo)
        self.spool = tempfile.mkdtemp(prefix="cardguru-srv-")
        self._seq = 0
        self.proc = subprocess.Popen(
            ["mvn", "-q", "-pl", "Mage.Tests", "test",
             "-Dtest=CardGuruScenarioRunner", "-DfailIfNoTests=false",
             f"-Dcardguru.server.spool={self.spool}"],
            cwd=self.mage_repo, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        ready = os.path.join(self.spool, "READY")
        deadline = _time.time() + warmup_timeout
        while not os.path.exists(ready):
            if self.proc.poll() is not None:
                raise RuntimeError("mage server exited during warmup "
                                   f"(rc={self.proc.returncode})")
            if _time.time() > deadline:
                self.close()
                raise RuntimeError("mage server warmup timed out")
            _time.sleep(0.5)
        atexit.register(self.close)

    def run_scenarios(self, specs: list[dict],
                      per_scenario_timeout: float = 30.0) -> list[dict]:
        import time as _time

        indir = os.path.join(self.spool, "in")
        outdir = os.path.join(self.spool, "out")
        names = []
        for spec in specs:
            self._seq += 1
            name = f"s{self._seq:06d}"
            tmp = os.path.join(indir, name + ".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(spec, f)
            os.replace(tmp, os.path.join(indir, name + ".json"))
            names.append(name)
        deadline = _time.time() + 30 + per_scenario_timeout * len(specs)
        outcomes = []
        for name in names:
            path = os.path.join(outdir, name + ".out.json")
            while not os.path.exists(path):
                if self.proc.poll() is not None:
                    raise RuntimeError("mage server died mid-batch")
                if _time.time() > deadline:
                    raise RuntimeError(f"mage server timed out waiting for "
                                       f"{name} ({len(specs)} scenarios)")
                _time.sleep(0.05)
            with open(path, encoding="utf-8") as f:
                outcomes.append(json.load(f))
            os.remove(path)
        return outcomes

    def close(self):
        if getattr(self, "proc", None) is None:
            return
        try:
            with open(os.path.join(self.spool, "SHUTDOWN"), "w"):
                pass
            self.proc.wait(timeout=15)
        except Exception:
            self.proc.kill()
        self.proc = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


_SERVER: "MageServer | None" = None


def shared_server(mage_repo: str | None = None) -> MageServer:
    """Process-wide server singleton for repeated grading calls."""
    global _SERVER
    if _SERVER is None or _SERVER.proc is None:
        _SERVER = MageServer(mage_repo)
    return _SERVER
