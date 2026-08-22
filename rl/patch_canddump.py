"""Add -Drl.candDump to RLPlayer.java.

The §2a timing-collision test needs, per consult: the candidate rows,
the CARD NAME behind each row, and the STEP the consult happened in.
`-Drl.entityDump` (StateEncoder) carries none of those - it dumps the
v6 view and the v5 state vector and nothing about candidates - so the
gate cannot be run on real emission without this hook.

Writes one JSON line per priority consult:
  {"site","turn","step","active","names":[...],"cands":[[...]],
   "state":[...]}

Idempotent: re-running is a no-op if the hook is already present.
RLPlayer.java holds a non-UTF8 byte, so this edits bytes, not text.
"""
import re
import sys

SRC = "/home/user/CardGuru/rl/xmage-src/RLPlayer.java"

HOOK = b'''
    /**
     * -Drl.candDump=<file>: one JSON line per priority consult, with the
     * candidate rows, the card name behind each row, and the step it was
     * taken in. This is what makes the timing-collision gate a
     * measurement on REAL emission: group the rows by card name, split
     * them by step, and ask whether the same card looks different in a
     * main phase and in the opponent's declare-attackers step.
     *
     * Off unless the property is set; the name resolution alone would
     * cost a getCard per candidate per consult.
     */
    private static final String CAND_DUMP = System.getProperty("rl.candDump");
    private static java.io.PrintWriter candOut;

    private static synchronized void dumpCands(Game game, UUID me, String site,
                                               float[][] cands, String[] names) {
        try {
            if (candOut == null) {
                candOut = new java.io.PrintWriter(new java.io.BufferedWriter(
                        new java.io.FileWriter(CAND_DUMP, true)));
                Runtime.getRuntime().addShutdownHook(
                        new Thread(() -> candOut.flush()));
            }
            StringBuilder b = new StringBuilder(1 << 12);
            b.append("{\\"site\\":\\"").append(site)
             .append("\\",\\"turn\\":").append(game.getTurnNum())
             .append(",\\"step\\":\\"").append(game.getTurnStepType())
             .append("\\",\\"active\\":")
             .append(me.equals(game.getActivePlayerId()) ? 1 : 0)
             .append(",\\"names\\":[");
            for (int i = 0; i < names.length; i++) {
                b.append(i > 0 ? "," : "").append('"')
                 .append(names[i] == null ? "?"
                         : names[i].replace("\\\\", "").replace("\\"", ""))
                 .append('"');
            }
            b.append("],\\"cands\\":[");
            for (int i = 0; i < cands.length; i++) {
                b.append(i > 0 ? "," : "").append(candArr(cands[i]));
            }
            // the flat state for the SAME consult: s[15] is active-player
            // and s[16..19] are the phase-step buckets, so the gate can
            // say whether the STATE separates what the CANDIDATE does not
            b.append("],\\"state\\":")
             .append(candArr(StateEncoder.encodeState(game, me, opponentId(game))))
             .append('}');
            candOut.println(b);
            // flush per line: the driver JVM is persistent, so a buffered
            // tail sits unwritten while the gate is already reading
            candOut.flush();
        } catch (java.io.IOException e) {
            throw new IllegalStateException("rl.candDump failed: " + CAND_DUMP, e);
        }
    }

    private static String candArr(float[] v) {
        StringBuilder b = new StringBuilder(v.length * 7 + 2);
        b.append('[');
        for (int i = 0; i < v.length; i++) {
            b.append(i > 0 ? "," : "")
             .append(String.format(java.util.Locale.ROOT, "%.6f", v[i]));
        }
        return b.append(']').toString();
    }

'''

# the emission loop at the prio site, matched on its distinctive tail
ANCHOR = b"""                    card, game);
        }
"""

CALL = b"""                    card, game);
        }
        if (CAND_DUMP != null) {
            String[] nm = new String[cands.length];
            nm[0] = "PASS";
            for (int i = 0; i < playable.size(); i++) {
                Card c0 = game.getCard(playable.get(i).getSourceId());
                nm[i + 1] = c0 == null ? "?" : c0.getName();
            }
            dumpCands(game, playerId, "prio", cands, nm);
        }
"""


def main():
    raw = open(SRC, "rb").read()
    if b"rl.candDump" in raw:
        print("PATCH|already present|no-op")
        return 0

    if raw.count(ANCHOR) != 1:
        print("PATCH|FAIL|prio anchor matched %d times, expected 1"
              % raw.count(ANCHOR))
        return 1
    raw = raw.replace(ANCHOR, CALL)

    # insert the hook before the consult funnel's javadoc
    m = re.search(rb"\n    private int consult\(Game game", raw)
    if not m:
        print("PATCH|FAIL|consult funnel not found")
        return 1
    raw = raw[:m.start()] + HOOK + raw[m.start() + 1:]

    open(SRC, "wb").write(raw)
    print("PATCH|OK|candDump hook added to RLPlayer.java")
    return 0


if __name__ == "__main__":
    sys.exit(main())
