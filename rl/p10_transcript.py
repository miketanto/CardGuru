"""Phase 10: pull a readable game transcript out of the surefire report.

The forked test JVM's stdout does not reach the console (surefire
captures it into <system-out> of TEST-*.xml), and the Phase 9 persistent
driver writes XMage's [LOG][GAME] lines to its OWN console rather than
to the job's captured stdout. So neither runner path hands a transcript
back directly - this reads it out of the surefire report instead.

Run: python3 rl/p10_transcript.py --xml <TEST-*.xml> --out FILE [--header TEXT]
"""
import argparse
import xml.etree.ElementTree as ET

KEEP = ("[LOG][GAME]", "RL|summary", "RL|playableMemo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--header", default="")
    args = ap.parse_args()

    root = ET.parse(args.xml).getroot()
    text = "\n".join(e.text or "" for e in root.iter("system-out"))
    lines = [ln.rstrip() for ln in text.splitlines()
             if any(k in ln for k in KEEP)]
    with open(args.out, "w") as fh:
        if args.header:
            fh.write("# " + args.header + "\n")
        fh.write("\n".join(lines) + "\n")
    print(f"P10TRANSCRIPT|out={args.out}|lines={len(lines)}")


if __name__ == "__main__":
    main()
