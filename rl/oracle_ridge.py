"""Does privileged information predict the outcome? A ridge probe.

ORACLE-GUIDING.md §8: the online critic probe was underpowered by
construction. Every state in an episode carries the SAME terminal
outcome, so the effective sample size for predicting it is the number of
EPISODES, not the number of states - 256 labels against 40,809 states
and ~700k parameters. It measured nothing, as it had to.

This matches capacity to the label count, which is what anvil's frozen
probe does (ADR-0039: ridge / kNN / MLP on a pooled representation, with
a learning-curve guard). Two ridge fits on the same rows:

    base   = [globals, entity-sum, entity-mean, n]
    oracle = base + [opp-hand-sum, opp-hand-mean, k]

and the question is whether the second predicts the discounted outcome
better OUT OF SAMPLE.

THE HOLDOUT IS GROUPED BY GAME, and that is not a detail. Every consult
in an episode shares one label; a random split puts states from the same
game on both sides and the label leaks straight across, inflating both
arms' R^2 and - worse - inflating them by different amounts. Grouped
splitting is the only honest way to score this.

    python3 rl/oracle_ridge.py /tmp/ds.jsonl
    python3 rl/oracle_ridge.py /tmp/ds.jsonl --curve   # power check

WHAT IT IS NOT. Not a win rate, and not evidence that a better critic
would help the policy - only whether the opponent's hand carries
outcome-relevant signal a value function could use.
"""
import argparse
import json
import sys

GAMMA = 0.997


def load(path):
    """-> episodes: list of (rows, reward); row = feature dict."""
    eps, cur = [], []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("end"):
            if cur:
                eps.append((cur, float(d["r"])))
            cur = []
        else:
            cur.append(d)
    return eps


def featurize(eps, with_oracle):
    X, y, grp = [], [], []
    for gi, (rows, reward) in enumerate(eps):
        n_ep = len(rows)
        for t, d in enumerate(rows):
            en = max(1, d["en"])
            f = list(d["g"]) + list(d["es"]) + [v / en for v in d["es"]] \
                + [d["en"] / 10.0]
            if with_oracle:
                on = max(1, d["on"])
                f += list(d["os"]) + [v / on for v in d["os"]] \
                    + [d["on"] / 10.0]
            X.append(f)
            # the same per-consult discounting the trainer uses
            y.append(reward * (GAMMA ** (n_ep - 1 - t)))
            grp.append(gi)
    return X, y, grp


def ridge_fit(X, y, lam):
    """Closed-form ridge; no sklearn in this container."""
    import torch
    Xt = torch.tensor(X, dtype=torch.float64)
    yt = torch.tensor(y, dtype=torch.float64)
    mu, sd = Xt.mean(0), Xt.std(0).clamp_min(1e-8)
    Xs = (Xt - mu) / sd
    Xs = torch.cat([Xs, torch.ones(len(Xs), 1, dtype=torch.float64)], 1)
    A = Xs.T @ Xs + lam * torch.eye(Xs.shape[1], dtype=torch.float64)
    w = torch.linalg.solve(A, Xs.T @ yt)
    return (mu, sd, w)


def ridge_pred(model, X):
    import torch
    mu, sd, w = model
    Xt = torch.tensor(X, dtype=torch.float64)
    Xs = (Xt - mu) / sd
    Xs = torch.cat([Xs, torch.ones(len(Xs), 1, dtype=torch.float64)], 1)
    return Xs @ w


def r2(pred, y):
    import torch
    yt = torch.tensor(y, dtype=torch.float64)
    ss = ((yt - pred) ** 2).sum()
    tot = ((yt - yt.mean()) ** 2).sum()
    return float(1 - ss / tot) if float(tot) > 1e-12 else float("nan")


def grouped_eval(eps, with_oracle, lam, folds):
    """Held-out R^2, splitting by GAME so the shared label cannot leak."""
    n_ep = len(eps)
    out = []
    for f in range(folds):
        te = [i for i in range(n_ep) if i % folds == f]
        tr = [i for i in range(n_ep) if i % folds != f]
        if not te or not tr:
            continue
        Xtr, ytr, _ = featurize([eps[i] for i in tr], with_oracle)
        Xte, yte, _ = featurize([eps[i] for i in te], with_oracle)
        m = ridge_fit(Xtr, ytr, lam)
        out.append(r2(ridge_pred(m, Xte), yte))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--lam", type=float, default=10.0)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--curve", action="store_true",
                    help="R^2 vs episode count - the power check that says "
                         "whether a null is a null or just too few labels")
    args = ap.parse_args()

    eps = load(args.dataset)
    if not eps:
        print("RIDGE|FAIL|no complete episodes in %s" % args.dataset)
        sys.exit(1)
    n_states = sum(len(r) for r, _ in eps)
    n_or = sum(1 for r, _ in eps for d in r if d["on"] > 0)
    print("RIDGE|episodes=%d|states=%d|states_with_oracle=%d (%.1f%%)"
          % (len(eps), n_states, n_or, 100.0 * n_or / max(1, n_states)))
    if n_or == 0:
        print("RIDGE|FAIL|no privileged rows in this dataset - collect with "
              "-Drl.oracle=true and a server built from the patched source")
        sys.exit(1)

    def report(tag, sizes):
        for n in sizes:
            sub = eps[:n]
            b = grouped_eval(sub, False, args.lam, args.folds)
            o = grouped_eval(sub, True, args.lam, args.folds)
            mb = sum(b) / len(b)
            mo = sum(o) / len(o)
            print("RIDGE|%s|episodes=%-5d|base_r2=%+.4f|oracle_r2=%+.4f"
                  "|delta=%+.4f" % (tag, n, mb, mo, mo - mb))
        return mb, mo

    if args.curve:
        # A flat delta at every size is a null; a delta that GROWS with
        # labels is a null that has not been reached yet. The online
        # probe could not tell these apart, which is why it is retired.
        sizes = [n for n in (64, 128, 256, 512, 1024, 2048)
                 if n <= len(eps)] or [len(eps)]
        if sizes[-1] != len(eps):
            sizes.append(len(eps))
        report("CURVE", sizes)
    else:
        mb, mo = report("FIT", [len(eps)])
        print("RIDGE|VERDICT|%s" % (
            "privileged information predicts the outcome better"
            if mo - mb > 0.01 else
            "no detectable gain from the opponent's hand at this "
            "label count - run --curve before calling it a null"))


if __name__ == "__main__":
    main()
