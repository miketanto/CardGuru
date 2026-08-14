"""Phase 12 task B: attribute a JFR profile's cost to CALLERS, not just
to hot methods.

Phase 9 established that `PlayerImpl.getPlayable` is 82% of game-thread
time on the SCRIPTED workload, and fixed it with a memo that helps only
seats calling it twice on one state. On the POLICY workload that memo
recorded 0 hits in 207,830 calls — ~2000 calls per episode against ~30
agent consults. So the question this script answers is not "what is
hot" (jfr_flame.py already answers that) but:

    who calls the hot frame, and how much does each caller cost?

Because "make it cheaper" and "call it less" are different engineering
jobs with very different price tags, and the caller breakdown is what
decides which one we are buying.

Run: python3 rl/p12_profile_analyze.py <collapsed[.gz]> [--frame SUBSTR]
"""
import argparse
import collections
import gzip
import sys


def load(path):
    op = gzip.open if path.endswith(".gz") else open
    out = []
    with op(path, "rt") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, n = line.rpartition(" ")
            try:
                n = int(n)
            except ValueError:
                stack, n = line, 1
            out.append((stack.split(";"), n))
    return out


def short(frame):
    """mage.players.PlayerImpl.getPlayable(Game, boolean) -> PlayerImpl.getPlayable"""
    f = frame.split("(")[0]
    parts = f.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collapsed")
    ap.add_argument("--frame", default="getPlayable",
                    help="substring of the frame to attribute")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    stacks = load(args.collapsed)
    total = sum(n for _, n in stacks)
    if not total:
        sys.exit("no samples")

    # inclusive cost of every frame. Dedupe on the SHORT name: a stack
    # containing getPlayable(Game) and getPlayable(Game, boolean) must
    # count once, or "inclusive" exceeds 100%.
    incl = collections.Counter()
    for frames, n in stacks:
        for f in {short(x) for x in frames}:
            incl[f] += n

    print(f"samples: {total}\n")
    print("## Hottest frames (inclusive share)\n")
    print("| frame | inclusive |")
    print("|---|---|")
    for f, n in incl.most_common(args.top):
        print(f"| {f} | {n / total:.1%} |")

    # attribute the target frame to its immediate callers
    callers = collections.Counter()
    target_total = 0
    depth_hist = collections.Counter()
    for frames, n in stacks:
        idx = [i for i, f in enumerate(frames) if args.frame in f]
        if not idx:
            continue
        target_total += n
        first = idx[0]                      # outermost occurrence
        depth_hist[len(idx)] += n           # recursion / nesting depth
        callers[short(frames[first - 1]) if first else "<root>"] += n

    if not target_total:
        print(f"\n(no samples contain '{args.frame}')")
        return
    print(f"\n## Callers of *{args.frame}* "
          f"({target_total / total:.1%} of all samples)\n")
    print("| caller | share of total | share of frame |")
    print("|---|---|---|")
    for f, n in callers.most_common(args.top):
        print(f"| {f} | {n / total:.1%} | {n / target_total:.1%} |")

    print(f"\n## Nesting depth of {args.frame} in the stack\n")
    print("| occurrences in one stack | samples | share of frame |")
    print("|---|---|---|")
    for d, n in sorted(depth_hist.items()):
        print(f"| {d} | {n} | {n / target_total:.1%} |")


if __name__ == "__main__":
    main()
