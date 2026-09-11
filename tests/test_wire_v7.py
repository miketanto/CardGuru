"""Phase 0a gate (v7 plan §2): wire_validate.py passes every valid fixture and
rejects every deliberately broken one naming the field."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rl"))
import wire_validate as W        # noqa: E402
import wire_fixtures as F        # noqa: E402

EXPECT = {
    "hello_no_wire": "hello.wire", "hello_dims": "hello.v7_dims", "ent_width": "v7_ent[0]: width",
    "ent_zone_onehot": "not one-hot", "edge_type": "v7_rtypes", "edge_endpoint": "outside token space",
    "refers_out_of_range": "v7_cand_refers", "refers_empty_nonpass": "empty for non-PASS",
    "cand_type_mismatch": "does not match v7_cand_type", "nan": "not a finite number",
    "name_missing": "lengths differ", "reply_range": "reply.a", "opp_known_flag": "known flag",
    "v6_key_missing": "v6 key",
}


def _lines(msgs):
    import json
    return [json.dumps(m) for m in msgs]


@pytest.mark.parametrize("decision", F.DECISIONS)
def test_valid_streams_pass(decision):
    n, err = W.validate_stream(_lines(F.valid_stream(decision, seed=7, n=10, with_opp=True)))
    assert err is None, err
    assert n == 10


@pytest.mark.parametrize("what", F.BROKEN)
def test_broken_streams_fail_naming_the_field(what):
    base = F.valid_stream("spell", seed=100, n=3, with_opp=True)
    n, err = W.validate_stream(_lines(F._break(base, what)))
    assert err is not None, what
    assert EXPECT[what] in err, (what, err)


def test_schema_is_json_serialisable():
    import json
    s = json.loads(json.dumps(W.json_schema()))
    assert s["properties"]["v7_ent"]["items"]["maxItems"] == W.DIMS["ent"]
