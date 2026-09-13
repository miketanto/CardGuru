"""Phase B patches (apply ONLY after the seed-1 lane is idle):
  1. rl/rung0_lane.sh: R0_INIT hook, R0_BATTERY_START, stop only this lane's driver port.
  2. rl/policy_server.py: act_v7 eval branch honours --argmax-classes.
  3. tests/test_v7_server.py: the act_v7 argmax-classes test.
Run from the repo root (Windows checkout):  python patch_phaseb.py
"""
import sys

def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:60], s.count(old))
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s)
    print("patched", path)

patch("rl/rung0_lane.sh", [
("""pkill -f "[R]LDriverServer" 2>/dev/null
sleep 2
""",
"""# 7d: stop only THIS lane's driver port (RL_DRIVER_PORT, default 7910). The
# former blanket `pkill -f "[R]LDriverServer"` took every JVM down - the
# recording driver 7911 and a second lane's 7912 included.
bash $RL/driver_server.sh stop ${RL_DRIVER_PORT:-7910} > /dev/null 2>&1
sleep 2
"""),
("""INIT=$OUT/init.pt
INITEXTRA=""
[ "$ARCH" = "entattn" ] && INITEXTRA="--gdim 16 --edim 48"
[ "${R0_RELATIONS:-1}" = "0" ] && [ "$ARCH" = "entattn" ] && INITEXTRA="$INITEXTRA --r0"
python3 $RL/p10_init_net.py --out $INIT --seed $((10 + SEED)) --sdim $SDIM \\
    --cdim $CDIM --arch $ARCH $INITEXTRA 2>/dev/null | tail -1
CKPT=$OUT/agent.pt
""",
"""INIT=$OUT/init.pt
if [ -n "${R0_INIT:-}" ]; then
    # 7d: start from a given checkpoint (bc.pt, or a trained ck_N.pt). Its
    # "episodes" counter is kept: `trained` starts there and the budget is
    # absolute (from ck_2048 with budget 3072 the rows are 2560 and 3072).
    [ -s "$R0_INIT" ] || { echo "R0_FAILED|init|$R0_INIT missing"; exit 1; }
    cp "$R0_INIT" $INIT
    echo "R0_INIT|from=$R0_INIT|episodes=$(python3 -c "
import torch
print(int(torch.load('$INIT',map_location='cpu',weights_only=False).get('episodes',0)))" 2>/dev/null)"
else
    INITEXTRA=""
    [ "$ARCH" = "entattn" ] && INITEXTRA="--gdim 16 --edim 48"
    [ "${R0_RELATIONS:-1}" = "0" ] && [ "$ARCH" = "entattn" ] && INITEXTRA="$INITEXTRA --r0"
    python3 $RL/p10_init_net.py --out $INIT --seed $((10 + SEED)) --sdim $SDIM \\
        --cdim $CDIM --arch $ARCH $INITEXTRA 2>/dev/null | tail -1
fi
CKPT=$OUT/agent.pt
"""),
("""[ "$trained" -eq 0 ] && battery 0
""",
"""# R0_BATTERY_START=1 (7d): a lane resumed/started from a trained checkpoint
# runs the battery once at its start too (the +0 row), skipped if present.
if [ "$trained" -eq 0 ] || { [ "${R0_BATTERY_START:-0}" = "1" ] && [ ! -s $OUT/probe_TWIN_${trained}.txt ]; }; then
    battery $trained
fi
"""),
])

patch("rl/policy_server.py", [
("""            else:
                a = int(torch.argmax(logits[0]))
        return a
""",
"""            else:
                # 7d correction: --argmax-classes (B7) used to apply on the
                # v6 act() path only; every v7 eval consult before this was
                # a plain argmax (V7-VALIDATION "7d overnight - correction")
                a = (_argmax_classes(logits[0], msg) if ARGMAX_CLASSES
                     else int(torch.argmax(logits[0])))
        return a
"""),
])

TEST = '''

def test_act_v7_eval_honours_argmax_classes(tmp_path, monkeypatch):
    """7d correction: act_v7's eval branch must apply _argmax_classes when the flag is
    on (it used to be a plain argmax; the flag lived on the v6 act() path only)."""
    tr = _small(tmp_path)
    msgs = F.valid_stream("block", seed=3, n=1, with_opp=True)
    hello, m = msgs[0], dict(msgs[1])
    ps.check_hello(hello, tr)
    tr.hello, tr.n_validated, tr.hidden = hello, 0, None
    tr.deck = None
    # candidate 1 duplicated as candidate 2 (same type / row / referents): one class
    for key in ("c", "v7_cand_type", "v7_cand", "v7_cand_refers"):
        m[key] = list(m[key]) + [m[key][1]]
    K = len(m["v7_cand_type"])
    lg = torch.full((1, K), -5.0)
    lg[0, 0], lg[0, 1], lg[0, 2] = 0.6, 0.5, 0.5     # plain argmax 0; class mass 1+2 > 0
    monkeypatch.setattr(ps.Trainer, "_v7_forward", staticmethod(lambda *a, **k: (lg, torch.zeros(1), None)))
    monkeypatch.setattr(ps, "ARGMAX_CLASSES", False)
    assert tr.act_v7(m, sample=False) == 0
    tr.hidden = None
    monkeypatch.setattr(ps, "ARGMAX_CLASSES", True)
    assert tr.act_v7(m, sample=False) == 1
'''
p = "tests/test_v7_server.py"
s = open(p, encoding="utf-8").read()
assert "test_act_v7_eval_honours_argmax_classes" not in s
open(p, "a", encoding="utf-8", newline="").write(TEST)
print("appended test")
