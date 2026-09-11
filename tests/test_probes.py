"""Phase 0d gate (v7 plan §2): the probe harness self-tests — planted fields
recovered at 1.0, a dropped field refused, a planted leak refused."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rl", "probes"))
try:                                   # a broken sklearn build raises more than ImportError
    import sklearn                     # noqa: F401
except Exception as e:                 # noqa: BLE001
    pytest.skip(f"scikit-learn unavailable: {e}", allow_module_level=True)
import faithfulness as Fp   # noqa: E402
import leak as Lk           # noqa: E402


def test_faithfulness_recovers_and_refuses():
    assert Fp.self_test()


def test_leak_gate_refuses_planted_leak():
    assert Lk.self_test()
