"""Add the CHOSEN index to -Drl.candDump's priority rows.

`instCasts=0` and `tgtChoices=0` say the trained policy never casts its
removal. They do not say why, and there are three explanations with
very different consequences:

  1. the removal is never OFFERED - it never reaches `playable`, e.g.
     the agent is tapped out. A mana finding, not a policy one.
  2. it is offered and DECLINED in favour of something else - a policy
     finding, and the interesting one.
  3. the policy has collapsed onto one candidate index and is not
     choosing at all - which is what `under_over = 0/96` looks like at
     the attack site, and would mean the same pathology at the priority
     site.

The window census (§4) already separates 1 from the rest. Separating 2
from 3 needs the CHOICE, and candDump records only the candidate list.
This adds `"pick"` - the index the policy returned - so a dump answers
"Cruel Cut was on the menu N times and was chosen 0 of them, while
index k was chosen N times".

Idempotent. RLPlayer.java holds a non-UTF8 byte, so this edits bytes.

DO NOT RUN THIS WHILE A LANE IS RUNNING - applying it means a
recompile, and sync_engine_src.sh pkills the driver JVM.
"""
import sys

SRC = "/home/user/CardGuru/rl/xmage-src/RLPlayer.java"

# dumpCands is called BEFORE consult(), because the candidate rows are
# what it exists to record. The pick is only known after. So the call
# moves to after the consult and takes the result.
OLD = b"""        if (CAND_DUMP != null) {
            String[] nm = new String[cands.length];
            nm[0] = "PASS";
            for (int i = 0; i < playable.size(); i++) {
                Card c0 = game.getCard(playable.get(i).getSourceId());
                nm[i + 1] = c0 == null ? "?" : c0.getName();
            }
            dumpCands(game, playerId, opponentId(game), "prio", cands, nm);
            dumpWindow(game, playerId, playable.size(), holdsInstant(game));
        }
"""
NEW = b"""        if (CAND_DUMP != null) {
            dumpWindow(game, playerId, playable.size(), holdsInstant(game));
        }
"""

OLD2 = b"""        consults++;
        int pick = consult(game, opponentId(game), cands, "prio");
"""
NEW2 = b"""        consults++;
        int pick = consult(game, opponentId(game), cands, "prio");
        if (CAND_DUMP != null) {
            String[] nm = new String[cands.length];
            nm[0] = "PASS";
            for (int i = 0; i < playable.size(); i++) {
                Card c0 = game.getCard(playable.get(i).getSourceId());
                nm[i + 1] = c0 == null ? "?" : c0.getName();
            }
            dumpCands(game, playerId, opponentId(game), "prio", cands, nm, pick);
        }
"""

OLD3 = (b"    private static synchronized void dumpCands(Game game, UUID me, UUID opp,\n"
        b"                                               String site, float[][] cands,\n"
        b"                                               String[] names) {")
NEW3 = (b"    private static synchronized void dumpCands(Game game, UUID me, UUID opp,\n"
        b"                                               String site, float[][] cands,\n"
        b"                                               String[] names, int pick) {")

OLD4 = b"""             .append(",\\"names\\":[");"""
NEW4 = b"""             .append(",\\"pick\\":").append(pick)
             .append(",\\"names\\":[");"""


def main():
    raw = open(SRC, "rb").read()
    if b'\\"pick\\"' in raw:
        print("PATCH|already present|no-op")
        return 0
    for old, new, label in ((OLD, NEW, "call removed from pre-consult"),
                            (OLD2, NEW2, "call added post-consult"),
                            (OLD3, NEW3, "signature"),
                            (OLD4, NEW4, "pick field")):
        if raw.count(old) != 1:
            print("PATCH|FAIL|%s: matched %d times, expected 1"
                  % (label, raw.count(old)))
            return 1
        raw = raw.replace(old, new)
    open(SRC, "wb").write(raw)
    print("PATCH|OK|pick index added to candDump")
    return 0


if __name__ == "__main__":
    sys.exit(main())
