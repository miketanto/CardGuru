"""Phase 0d (v7 plan §2): the faithfulness probe.

Design principle 1 (ARCHITECTURE-V7-DESIGN.md §0): the encoder's job is
to describe the game state; faithfulness is checked by probes that are
never trained into the net.  This module is that instrument: given
tokens after some stage (L3 builder output, L4 encoder output, ...) and
the input fields those tokens were built from, fit a LINEAR readout per
field on a game-grouped training split and report recovery on held-out
games.  A field the readout cannot recover on held-out games was not
carried by the stage.

    probe(tokens, targets, groups, kinds)  ->  {field: {"score", "chance", "pass"}}

  tokens   [N, d] float      one row per token after the stage
  targets  [N, F] float      the planted / input fields (NaN = not defined for that token)
  groups   [N]   int         game id per token; the split is by game, so a
                             token and its neighbours from the same game
                             never straddle train / held-out
  kinds    list[str]         per field: "binary" (accuracy, chance = majority),
                             "cat" (integer classes, accuracy), "real" (R^2)

Pass criteria (pre-set, per field): binary/cat accuracy >= 0.99 on
held-out when the stage is expected to preserve the field exactly
(the token-builder gate), R^2 >= 0.95 for reals; the caller may pass
its own thresholds.  Ridge regression / logistic regression from
scikit-learn; features are standardised on the training split only.

Self-test (`python3 rl/probes/faithfulness.py`): synthetic tokens that
carry 6 planted fields through a random linear map plus noise dims must
be recovered at 1.0 / R^2 > 0.99; the same probe on tokens that DROPPED
a field must report chance for that field.  A probe that could pass on
dropped fields would be worthless, so the self-test checks both.

Nothing here can write to the model: it only reads tensors.
"""
import numpy as np


def _split_by_group(groups, frac=0.2, seed=0):
    rng = np.random.RandomState(seed)
    gids = np.unique(groups)
    rng.shuffle(gids)
    held = set(gids[: max(1, int(round(frac * len(gids))))].tolist())
    te = np.array([g in held for g in groups])
    return ~te, te


def probe(tokens, targets, groups, kinds, thresholds=None, frac=0.2, seed=0):
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    X = np.asarray(tokens, dtype=np.float64)
    Y = np.asarray(targets, dtype=np.float64)
    groups = np.asarray(groups)
    tr, te = _split_by_group(groups, frac, seed)
    out = {}
    for f, kind in enumerate(kinds):
        y = Y[:, f]
        ok = ~np.isnan(y)
        trf, tef = tr & ok, te & ok
        if trf.sum() < 10 or tef.sum() < 5:
            out[f] = {"score": None, "chance": None, "pass": None, "n_test": int(tef.sum())}
            continue
        sc = StandardScaler().fit(X[trf])
        Xtr, Xte = sc.transform(X[trf]), sc.transform(X[tef])
        if kind in ("binary", "cat"):
            ytr, yte = y[trf].astype(int), y[tef].astype(int)
            if len(np.unique(ytr)) < 2:
                score = float((yte == ytr[0]).mean()); chance = score
            else:
                clf = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr, ytr)
                score = float((clf.predict(Xte) == yte).mean())
                vals, cnt = np.unique(yte, return_counts=True)
                chance = float(cnt.max() / cnt.sum())
            thr = (thresholds or {}).get(f, 0.99)
        else:
            reg = Ridge(alpha=1.0).fit(Xtr, y[trf])
            pred = reg.predict(Xte)
            ss_res = float(((y[tef] - pred) ** 2).sum())
            ss_tot = float(((y[tef] - y[tef].mean()) ** 2).sum()) + 1e-12
            score = 1.0 - ss_res / ss_tot
            chance = 0.0
            thr = (thresholds or {}).get(f, 0.95)
        out[f] = {"score": score, "chance": chance, "pass": bool(score >= thr), "n_test": int(tef.sum())}
    return out


def table(result, names=None):
    rows = ["| field | held-out score | chance | n | result |", "|---|---|---|---|---|"]
    for f, r in result.items():
        name = names[f] if names else str(f)
        if r["score"] is None:
            rows.append(f"| {name} | — | — | {r['n_test']} | too few |")
        else:
            rows.append(f"| {name} | {r['score']:.3f} | {r['chance']:.3f} | {r['n_test']} | {'pass' if r['pass'] else '**FAIL**'} |")
    return "\n".join(rows)


# --- self-test -------------------------------------------------------------------

def _synthetic(n_games=60, per_game=40, d=64, seed=0, drop=None):
    rng = np.random.RandomState(seed)
    N = n_games * per_game
    groups = np.repeat(np.arange(n_games), per_game)
    fields = np.stack([
        rng.randint(0, 2, N),          # binary
        rng.randint(0, 2, N),          # binary
        rng.randint(0, 5, N),          # cat
        rng.rand(N),                   # real
        rng.rand(N) * 6,               # real
        rng.randint(0, 2, N),          # binary
    ], 1).astype(np.float64)
    kinds = ["binary", "binary", "cat", "real", "real", "binary"]
    src = fields.copy()
    onehot = np.eye(5)[src[:, 2].astype(int)]                       # cat as one-hot for the map
    inputs = np.concatenate([src[:, [0, 1, 3, 4, 5]], onehot], 1)  # 10 planted dims
    if drop is not None:
        cols = {0: [0], 1: [1], 2: [5, 6, 7, 8, 9], 3: [2], 4: [3], 5: [4]}[drop]
        inputs = inputs.copy(); inputs[:, cols] = 0.0
    W = rng.randn(inputs.shape[1], d)
    tokens = np.tanh(inputs @ W * 0.3) + 0.01 * rng.randn(N, d)      # a fixed nonlinear stage
    return tokens, fields, groups, kinds


def self_test():
    tokens, fields, groups, kinds = _synthetic()
    res = probe(tokens, fields, groups, kinds)
    ok = all(r["pass"] for r in res.values())
    print("planted fields, all carried:")
    print(table(res, ["bin0", "bin1", "cat5", "real01", "real06", "bin2"]))
    tokens_d, fields_d, groups_d, kinds_d = _synthetic(drop=2)
    res_d = probe(tokens_d, fields_d, groups_d, kinds_d)
    dropped_detected = (not res_d[2]["pass"]) and res_d[2]["score"] <= res_d[2]["chance"] + 0.1
    print("\ncat5 dropped from the input:")
    print(table(res_d, ["bin0", "bin1", "cat5", "real01", "real06", "bin2"]))
    print(f"\nSELFTEST|carried_all_pass={ok}|dropped_field_refused={dropped_detected}")
    return ok and dropped_detected


if __name__ == "__main__":
    import sys
    sys.exit(0 if self_test() else 1)
