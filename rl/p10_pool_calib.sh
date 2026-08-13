#!/bin/bash
# Phase 10 pre-flight: budget-test every pool deck, measure its POWER
# against the agent's own deck under equal piloting, and emit the
# flagship's seed pool.
#
# Why re-measure decks 7c already rated: the flagship pool mixes rows
# from three sources (7c archetypes, 8b meta decks, snapshots and
# champions) and PFSP compares their Elos to each other. 7c's
# curriculum Elos were priors from a screen against a 916-rated agent;
# the champion/snapshot rows are Phase 6 mirror ratings (D0 = 1000).
# Those are not the same scale. So every DECK row is (re)derived here by
# one protocol, on the scale the champion rows already live on:
#
#   power p = win rate of D0 piloting X vs D0 piloting BenchDimir (100g)
#   row Elo  = 1000 + 400*log10(p/(1-p))
#
# i.e. "how strong is this seat+deck combination, measured against the
# D0-on-BenchDimir anchor that is pinned at 1000". Both seats are the
# same frozen instrument, so the number is deck power, not pilot skill -
# which is exactly p7c_pilot_calib.sh's protocol A, re-run here for the
# meta decks and re-run for the archetypes as a scale check against the
# powers 7c published.
#
# Scripted-vs-scripted, so no policy server and no torch: this is
# workload (a), the one Phase 9's equivalence gate covers at conc4.
#
# Usage: bash rl/p10_pool_calib.sh [games=100]
set -u
G=${1:-100}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p10_calib
MIRROR=BenchDimir.dck
SEEDFILE=$RL/p10_pool_seed.tsv
mkdir -p $OUT

# name|deck|source
DECKS=(
  "sweep|P7cSweepControl.dck|7c"
  "tokens|M3SelesnyaTokens.dck|7c"
  "wweenie|M3WhiteWeenie.dck|7c"
  "skies|M3BlueSkies.dck|7c"
  "redrush|M3RedRush.dck|7c"
  "ramp|M3GreenRamp.dck|7c"
  "meta_monored|P8MetaMonoRed.dck|8b"
  "meta_boros|P8MetaBoros.dck|8b"
  "meta_golgari|P8MetaGolgari.dck|8b"
  "meta_dimirbounce|P8MetaDimirBounce.dck|8b"
  "meta_domain|P8MetaDomain.dck|8b"
  "meta_azorius|P8MetaAzorius.dck|8b"
)

run() {  # $1 out $2 games $3 oppDeck $4 seed $5 conc
    [ -s "$1" ] && return 0
    RL_PERSIST=1 RL_AUTOSTART=1 RL_CONC=$5 \
    bash $RL/run_driver.sh \
        -Drl.episodes=$2 \
        -Drl.agent=heuristic -Drl.policy=random \
        -Drl.opponent=heuristic \
        -Drl.agentPlies=1 -Drl.agentBreadth=8 \
        -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$3 -Drl.oppDeck=$MIRROR -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$4 -Drl.report=0 \
        -Drl.out=$1 > /dev/null 2>&1
}
field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

cd /home/user/mage
echo "=== 1. budget test (4 episodes/deck; the M3 rule) ==="
for D in "${DECKS[@]}"; do
    IFS='|' read -r NAME DCK SRC <<< "$D"
    F=$OUT/budget_${NAME}.txt
    run $F 4 $DCK 949000 1
    if [ ! -s "$F" ]; then
        echo "P10CALIB_FAILED|deck=$NAME|budget_test_produced_nothing"; exit 1
    fi
    echo "P10BUDGET|deck=$NAME|file=$DCK|episodes=$(field $F episodes)|turns_per_ep=$(field $F turns_per_ep)|stalls=$(field $F stalls)"
done

echo "=== 2. deck power, both seats D0 (X vs BenchDimir, ${G}g, conc4) ==="
for D in "${DECKS[@]}"; do
    IFS='|' read -r NAME DCK SRC <<< "$D"
    F=$OUT/power_${NAME}.txt
    run $F $G $DCK 953000 4
    P=$(field $F win_rate)
    echo "P10POWER|deck=$NAME|file=$DCK|source=$SRC|power=${P:-NA}|stalls=$(field $F stalls)"
done

echo "=== 3. seed pool ==="
python3 - "$OUT" "$SEEDFILE" "$G" <<'PY'
import math, os, sys
out, seedfile, games = sys.argv[1], sys.argv[2], int(sys.argv[3])
DECKS = [
    ("sweep", "P7cSweepControl.dck", "7c"),
    ("tokens", "M3SelesnyaTokens.dck", "7c"),
    ("wweenie", "M3WhiteWeenie.dck", "7c"),
    ("skies", "M3BlueSkies.dck", "7c"),
    ("redrush", "M3RedRush.dck", "7c"),
    ("ramp", "M3GreenRamp.dck", "7c"),
    ("meta_monored", "P8MetaMonoRed.dck", "8b"),
    ("meta_boros", "P8MetaBoros.dck", "8b"),
    ("meta_golgari", "P8MetaGolgari.dck", "8b"),
    ("meta_dimirbounce", "P8MetaDimirBounce.dck", "8b"),
    ("meta_domain", "P8MetaDomain.dck", "8b"),
    ("meta_azorius", "P8MetaAzorius.dck", "8b"),
]


def wr(path):
    for line in open(path):
        if "win_rate=" in line:
            return float(line.split("win_rate=")[1].split("|")[0])
    return None


def elo(p):
    # clamp so a 100g shutout does not produce an infinite rating
    p = min(max(p, 1.0 / (2 * games)), 1 - 1.0 / (2 * games))
    return int(round(1000 + 400 * math.log10(p / (1 - p))))


rows = ["# Phase 10 flagship seed pool - rows are name|kind|deck|elo",
        "# kind: heuristic|search|searchhold (scripted seat piloting deck)",
        "#       rl:<arch>:<ckpt>          (a served policy seat)",
        "# Deck rows: Elo = 1000 + 400*log10(p/(1-p)), p = D0(deck) vs",
        "# D0(BenchDimir) over %dg (rl/p10_pool_calib.sh). Champion and" % games,
        "# snapshot rows: Phase 6 mirror ratings, same D0=1000 anchor.",
        "# --- scripted mirror ladder (the frozen instruments) ---",
        "D0|heuristic|BenchDimir.dck|1000",
        "D1|search|BenchDimir.dck|1085",
        "D1h|searchhold|BenchDimir.dck|1088",
        "# --- 7c archetype decks, D0-piloted ---"]
seen_8b = False
for name, deck, src in DECKS:
    if src == "8b" and not seen_8b:
        rows.append("# --- 8b Standard-meta approximations, D0-piloted ---")
        seen_8b = True
    p = wr(os.path.join(out, "power_%s.txt" % name))
    if p is None:
        raise SystemExit("no power measurement for %s" % name)
    rows.append("%s|heuristic|%s|%d" % (name, deck, elo(p)))

rows.append("# --- prior champions (all cdim 91) ---")
CHAMPS = [
    ("p7b_ck6144", "lstmattn", "/tmp/rl_p7_lstmattn_s0/p7b_champion.pt", 1101),
    ("p7c_ck1536", "lstmattn", "/tmp/rl_p7c_lstmattn_s0/pool/ck_1536.pt", 1096),
    ("p7c_ck3072", "lstmattn", "/tmp/rl_p7c_lstmattn_s0/p7c_final.pt", 1046),
    ("attn_desp", "attn", "/tmp/rl_c6_attn_s7/attn_desp_final.pt", 1053),
    ("attn_bc", "attn", "/tmp/rl_p5_c1/student_e2attn.pt", 1044),
    ("attn_v2", "attn", "/tmp/rl_c6_attn_s0/attn_v2_final.pt", 1039),
]
for name, arch, ck, e in CHAMPS:
    rows.append("%s|rl:%s:%s|BenchDimir.dck|%d" % (name, arch, ck, e))

rows.append("# --- 7b snapshot ladder: the low rungs a from-scratch net needs ---")
LADDER = "/tmp/rl_p7_lstmattn_s0/pool_elo.tsv"
for line in open(LADDER):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, arch, ck, e = line.split("|")
    if not name.startswith("ck_"):
        continue                      # champions already added above
    if not os.path.exists(ck):
        continue
    rows.append("p7b_%s|rl:%s:%s|BenchDimir.dck|%s" % (name, arch, ck, e))

open(seedfile, "w").write("\n".join(rows) + "\n")
n = len([r for r in rows if not r.startswith("#")])
print("P10POOL_SEEDED|file=%s|rows=%d" % (seedfile, n))
PY
echo "P10CALIB_DONE"
