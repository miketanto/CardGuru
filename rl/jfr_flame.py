"""Turn a JFR recording into collapsed stacks, a hot-method table and an
SVG flame graph — no external profiler needed (async-profiler and the
FlameGraph scripts are not installable in this container).

    python3 rl/jfr_flame.py /tmp/rl_p9/profile.jfr rl/perf/scripted

writes <out>.collapsed, <out>.top.txt and <out>.svg. Input is whatever
`jfr print --events jdk.ExecutionSample` emits: one stack per sample,
leaf frame first.
"""
import collections
import html
import subprocess
import sys


def collapsed_from_jfr(path, thread_filter="GAME"):
    """[(stack_root_first, count)] for samples on game threads."""
    txt = subprocess.run(["jfr", "print", "--stack-depth", "512",
                          "--events", "jdk.ExecutionSample", path],
                         capture_output=True, text=True).stdout
    stacks = collections.Counter()
    cur, thread, in_trace = [], "", False
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("jdk.ExecutionSample {"):
            if cur and (not thread_filter or thread_filter in thread):
                stacks[tuple(reversed(cur))] += 1
            cur, thread, in_trace = [], "", False
            continue
        if s.startswith("sampledThread ="):
            thread = s
            continue
        if s.startswith("stackTrace = ["):
            in_trace = True
            continue
        if in_trace:
            if s in ("]", "}", ""):
                in_trace = False
                continue
            # "mage.game.GameImpl.copy() line: 246"
            frame = s.split(" line:")[0].strip()
            if frame.endswith(","):
                frame = frame[:-1]
            if frame.startswith("..."):
                continue
            cur.append(frame)
    if cur and (not thread_filter or thread_filter in thread):
        stacks[tuple(reversed(cur))] += 1
    return stacks


def svg(stacks, out, title, width=1400, cell=16, min_px=2.0):
    """Minimal icicle/flame renderer: one rect per (depth, frame-run).

    min_px prunes anything thinner than that many pixels (0.14% of the
    run at the default width) - it keeps the file small enough to commit
    without losing any frame that matters.
    """
    total = sum(stacks.values())
    # build a prefix tree of counts
    tree = {}
    for stack, n in stacks.items():
        node = tree
        for frame in stack:
            node = node.setdefault(frame, [0, {}])
            node[0] += n
            node = node[1]
    rows, maxdepth = [], [0]

    def walk(node, depth, x0):
        for frame, (n, kids) in sorted(node.items(), key=lambda kv: -kv[1][0]):
            w = width * n / total
            if w >= min_px:
                rows.append((x0, depth, w, frame, n))
                maxdepth[0] = max(maxdepth[0], depth)
                walk(kids, depth + 1, x0)
            x0 += w

    walk(tree, 0, 0)
    height = (maxdepth[0] + 2) * cell + 34
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
             f'height="{height}" font-family="monospace" font-size="11">',
             f'<rect width="{width}" height="{height}" fill="#f8f8f8"/>',
             f'<text x="8" y="16" font-size="13">{html.escape(title)} '
             f'({total} samples)</text>']
    for x, depth, w, frame, n in rows:
        # warm hue by depth, like the classic flame palette
        r, g, b = 205 + (depth * 7) % 50, 60 + (depth * 37) % 130, 40
        y = 26 + depth * cell
        label = frame.split("(")[0]
        pct = 100.0 * n / total
        parts.append(
            f'<g><title>{html.escape(frame)} — {n} ({pct:.1f}%)</title>'
            f'<rect x="{x:.1f}" y="{y}" width="{max(w - 0.6, 0.4):.1f}" '
            f'height="{cell - 1}" fill="rgb({r},{g},{b})"/>')
        if w > 55:
            parts.append(f'<text x="{x + 3:.1f}" y="{y + cell - 5}" '
                         f'fill="#fff">'
                         f'{html.escape(label[-int(w / 6.2):])}</text>')
        parts.append('</g>')
    parts.append('</svg>')
    open(out, "w").write("\n".join(parts))


def main():
    jfr, out = sys.argv[1], sys.argv[2]
    stacks = collapsed_from_jfr(jfr)
    total = sum(stacks.values())
    with open(out + ".collapsed", "w") as f:
        for stack, n in stacks.most_common():
            f.write(";".join(stack) + f" {n}\n")

    leaf = collections.Counter()
    incl = collections.Counter()
    for stack, n in stacks.items():
        leaf[stack[-1]] += n
        for frame in set(stack):
            incl[frame] += n
    with open(out + ".top.txt", "w") as f:
        f.write(f"samples={total} (game threads only)\n\n")
        f.write("== self time (leaf frame) ==\n")
        for frame, n in leaf.most_common(25):
            f.write(f"{100.0 * n / total:6.2f}%  {frame}\n")
        f.write("\n== inclusive (frame anywhere on stack) ==\n")
        for frame, n in incl.most_common(40):
            f.write(f"{100.0 * n / total:6.2f}%  {frame}\n")
    svg(stacks, out + ".svg", "XMage RL episode loop — " + jfr.split("/")[-1])
    print(open(out + ".top.txt").read()[:1500])


if __name__ == "__main__":
    main()
