"""-Drl.oracle=true: emit the OPPONENT'S HAND as a separate entity list.

Asymmetric actor-critic (Suphx's oracle guiding, AlphaStar's
opponent-conditioned value). The critic may see hidden information at
TRAINING time; the policy may never see it, at any time.

THE INFORMATION SET IS ENFORCED IN ONE PLACE and this patch is careful
not to move it. `encodeEntities` today does:

    for (Card c : my.getHand().getCards(game))      // mine are tokens
        ents.add(cardEnt(c, game, true, Z_HAND, 5));
    g[14] = op.getHand().size() / 10f;              // theirs is a COUNT

The opponent's hand rows go into a SEPARATE list (`view.oracle`) that is
never appended to `ents`, never sorted into it, never indexed by
`relations`, and is serialised under its own wire key `"oe"`. The
policy's observation is byte-identical whether or not the flag is set -
which `rl/oracle_gate.py` asserts rather than assumes, because that
assertion is the only thing standing between this and a cheating agent.

No relations are emitted for oracle rows. They are consumed as a bag by
the critic's pooling path; the question the critic needs answered is
"what is in their hand", not how it relates to the board.

Idempotent. Bytes, not text - RLPlayer/StateEncoder carry a non-UTF8 byte.
"""
import sys

ENC = "/home/user/CardGuru/rl/xmage-src/StateEncoder.java"
SOCK = "/home/user/CardGuru/rl/xmage-src/SocketPolicyClient.java"


def patch_encoder(raw):
    # 1. the flag, beside the other class-init constants
    old = b'    private static final String DUMP = System.getProperty("rl.entityDump");'
    new = (b'    /** -Drl.oracle=true: also emit the opponent\'s hand, for the\n'
           b'     *  CRITIC ONLY. Class-init like every other rl.* constant, so a\n'
           b'     *  driver JVM that served one arm cannot serve the other. */\n'
           b'    public static final boolean ORACLE = Boolean.getBoolean("rl.oracle");\n\n'
           b'    private static final String DUMP = System.getProperty("rl.entityDump");')
    assert raw.count(old) == 1, "DUMP anchor"
    raw = raw.replace(old, new)

    # 2. EntityView carries the oracle rows, defaulting to empty
    old = b"""    public static final class EntityView {
        public final float[] globals;
        public final float[][] entities;
        public final int[][] relations;

        EntityView(float[] g, float[][] e, int[][] r) {
            globals = g;
            entities = e;
            relations = r;
        }
    }"""
    new = b"""    public static final class EntityView {
        public final float[] globals;
        public final float[][] entities;
        public final int[][] relations;
        /** opponent-hand rows, CRITIC ONLY. Empty unless -Drl.oracle.
         *  Never merged into `entities` - see patch_oracle.py. */
        public final float[][] oracle;

        EntityView(float[] g, float[][] e, int[][] r) {
            this(g, e, r, EMPTY);
        }

        EntityView(float[] g, float[][] e, int[][] r, float[][] o) {
            globals = g;
            entities = e;
            relations = r;
            oracle = o;
        }
    }

    private static final float[][] EMPTY = new float[0][];"""
    assert raw.count(old) == 1, "EntityView anchor"
    raw = raw.replace(old, new)

    # 3. emit them - after the view's own rows are final, so there is no
    #    chance of the oracle list being caught by ents.sort/truncate
    old = b"""        EntityView view = new EntityView(encodeGlobals(game, me, opp), rows,
                relations(game, me, opp, index));"""
    new = b"""        float[][] oracleRows = EMPTY;
        if (ORACLE) {
            List<Ent> oe = new ArrayList<>();
            for (Card c : op.getHand().getCards(game)) {
                oe.add(cardEnt(c, game, false, Z_HAND, 5));
            }
            oe.sort(ORDER);
            if (oe.size() > EMAX) {
                oe = oe.subList(0, EMAX);
            }
            oracleRows = new float[oe.size()][];
            for (int i = 0; i < oe.size(); i++) {
                oracleRows[i] = oe.get(i).row;
            }
        }
        EntityView view = new EntityView(encodeGlobals(game, me, opp), rows,
                relations(game, me, opp, index), oracleRows);"""
    assert raw.count(old) == 1, "view anchor"
    raw = raw.replace(old, new)
    return raw


def patch_socket(raw):
    old = b"""            sb.append("],\\"c\\":[");"""
    new = b"""            sb.append(']');
            // CRITIC-ONLY channel. Emitted as its own key so a server
            // that does not know about it simply ignores it, and so the
            // policy's own "e" is byte-identical either way.
            if (view.oracle.length > 0) {
                sb.append(",\\"oe\\":[");
                for (int i = 0; i < view.oracle.length; i++) {
                    if (i > 0) {
                        sb.append(',');
                    }
                    floats(view.oracle[i]);
                }
                sb.append(']');
            }
            sb.append(",\\"c\\":[");"""
    assert raw.count(old) == 1, "candidates anchor"
    raw = raw.replace(old, new)
    return raw


def main():
    enc = open(ENC, "rb").read()
    sock = open(SOCK, "rb").read()
    if b"rl.oracle" in enc:
        print("PATCH|already present|no-op")
        return 0
    enc = patch_encoder(enc)
    sock = patch_socket(sock)
    open(ENC, "wb").write(enc)
    open(SOCK, "wb").write(sock)
    print("PATCH|OK|oracle emission + wire key added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
