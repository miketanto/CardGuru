"""Phase 4g (v7 plan §2): every v7 gate in one runnable, exit 1 on any
failure — the v7 counterpart of entattn_check.py.

Runs, in order, and prints one CHECK line each:
  WIRE      wire_validate.py on rl/fixtures/v7 (valid pass, broken refused)
  PARSE     v7_obs.py on the fixtures (valid parse, broken refused)
  PROBES    rl/probes self-tests (faithfulness, leak)
  PYTEST    tests/test_wire_v7.py test_v7_obs.py test_v7_net.py test_v7_encoder.py
            test_v7_heads.py test_v7_value.py test_v7_belief.py test_v7_policy.py
  V6        rl/entattn_check.py unchanged vs rl/artifacts/v7/baseline.md (same
            check lines: 23 checks, the known R0-NOBIAS state)

    python3 rl/v7_check.py            (WSL; needs pytest, scikit-learn, torch)
"""
import glob
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
PY = sys.executable
TESTS = ["test_wire_v7.py", "test_v7_obs.py", "test_v7_net.py", "test_v7_encoder.py",
         "test_v7_heads.py", "test_v7_value.py", "test_v7_belief.py", "test_v7_policy.py",
         "test_v7_server.py"]


def run(cmd, timeout=1800):
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def main():
    t0 = time.time()
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(f"CHECK|{name:9s}|{'PASS' if ok else 'FAIL'}|{detail}", flush=True)

    rc, out = run([PY, os.path.join(HERE, "wire_validate.py")] + sorted(glob.glob(os.path.join(HERE, "fixtures", "v7", "valid_*.jsonl"))))
    check("WIRE-OK", rc == 0, f"valid fixtures: {out.count('ok   ')} ok")
    rc, out = run([PY, os.path.join(HERE, "wire_validate.py")] + sorted(glob.glob(os.path.join(HERE, "fixtures", "v7", "broken_*.jsonl"))))
    n_fail = out.count("FAIL ")
    check("WIRE-BAD", n_fail == len(glob.glob(os.path.join(HERE, "fixtures", "v7", "broken_*.jsonl"))), f"broken fixtures refused: {n_fail}")
    rc, out = run([PY, os.path.join(HERE, "v7_obs.py")] + sorted(glob.glob(os.path.join(HERE, "fixtures", "v7", "*.jsonl"))))
    check("PARSE", rc == 0, f"v7_obs on fixtures: {out.count('ok  ')} ok, {out.count('BAD ')} bad")
    rc, out = run([PY, os.path.join(HERE, "probes", "faithfulness.py")])
    check("PROBE-F", rc == 0, re.search(r"SELFTEST\|.*", out).group(0) if "SELFTEST" in out else out[-200:])
    rc, out = run([PY, os.path.join(HERE, "probes", "leak.py")])
    check("PROBE-L", rc == 0, re.search(r"SELFTEST\|.*", out).group(0) if "SELFTEST" in out else out[-200:])
    for t in TESTS:
        rc, out = run([PY, "-m", "pytest", os.path.join(REPO, "tests", t), "-q", "-x"], timeout=3600)
        m = re.search(r"(\d+) passed", out)
        check(t.replace("test_", "").replace(".py", "").upper()[:9], rc == 0, m.group(0) if m else out[-300:].replace("\n", " "))
    rc, out = run([PY, os.path.join(HERE, "entattn_check.py")], timeout=1800)
    m = re.search(r"ENTATTN\|checks=(\d+)\|failures=(\d+)", out)
    base = open(os.path.join(HERE, "artifacts", "v7", "baseline.md"), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, "artifacts", "v7", "baseline.md")) else ""
    bm = re.search(r"checks=(\d+)\|failures=(\d+)", base)
    same = bool(m and bm and m.group(1) == bm.group(1) and m.group(2) == bm.group(2))
    check("V6-SAME", same, f"entattn_check {m.group(0) if m else 'no summary'} vs baseline {bm.group(0) if bm else 'none'}")
    n_fail = sum(1 for r in results if not r)
    print(f"V7CHECK|checks={len(results)}|failures={n_fail}|{time.time() - t0:.0f}s")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
