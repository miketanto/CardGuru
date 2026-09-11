"""Where does one consult's server-side time go? (THROUGHPUT-LOCAL.md §11.3)

Single process, no engine, no sockets. A realistic v6 consult message
(gdim 16, N entity rows of 48 floats, a few relation edges, K candidates
of 94 floats) is serialised the way the driver sends it, then each
stage the handler thread runs is timed on its own:

  json     json.loads of the wire line
  obs      Trainer._entity_obs (the per-row Python loop) + cands/mask
  fwd1     one forward, batch 1, on --device
  fwdB     one forward, batch B, on --device (per-row cost = fwdB / B)
  sample   Categorical + log_prob + the float()/int() syncs act() does

Numbers are ms per consult, medians over --reps repetitions after a
warm-up. Nothing here involves the GIL contention of the real server;
this is the floor a single handler thread pays.

    python3 rl/consult_cost.py --device cuda --entities 30 --k 10 --batch 8
"""
import argparse
import json
import statistics
import sys
import time

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402

CDIM, GDIM, EDIM, EMAX, MAXK = 94, 16, 48, 96, 96


def message(gen, n_ent, k, n_rel=8):
    g = torch.rand(GDIM, generator=gen).tolist()
    e = torch.rand(n_ent, EDIM, generator=gen).tolist()
    r = []
    for _ in range(min(n_rel, n_ent * n_ent)):
        a, b = torch.randint(0, n_ent, (2,), generator=gen).tolist()
        r.append([a, b, int(torch.randint(0, len(ps.RTYPES), (1,),
                                          generator=gen))])
    c = torch.rand(k, CDIM, generator=gen).tolist()
    # the driver prints floats with limited precision; 4 decimals is the
    # order of the wire size, which is what json.loads pays for
    def r4(x):
        return [round(v, 4) for v in x]
    msg = {"t": "consult", "g": r4(g), "e": [r4(row) for row in e],
           "r": r, "c": [r4(row) for row in c], "phi": 0.0}
    return json.dumps(msg, separators=(",", ":")) + "\n"


def med(fn, reps, sync):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        if sync:
            torch.cuda.synchronize()
        ts.append((time.perf_counter() - t0) * 1000)
    return statistics.median(ts)


def main_v7(args):
    import random
    import v7_obs as V
    import wire_fixtures as F
    tr = ps.Trainer(None, 0, None, arch="v7", card_emb="card_emb_v8")
    tr.net.eval()
    g = random.Random(0)
    hello = F.hello()
    msg = F.consult(g, "block", True)
    raw = (json.dumps(msg, separators=(",", ":")) + "\n").encode()
    n_ent, k = len(msg["v7_ent"]), len(msg["v7_cand_type"])
    sync = args.device == "cuda"
    ids = tr.ids

    def do_json():
        return json.loads(raw)

    def do_obs():                       # after the first 100: validate=False in act_v7
        return V.compact(V.parse_consult(msg, ids, hello, validate=False))

    def do_validate():
        return V.parse_consult(msg, ids, hello, validate=True)
    obs = do_obs()
    B = args.batch
    hin = None

    def do_fwd1():
        with torch.no_grad():
            return tr._v7_forward(tr.net, [obs], [[]], [None], hin, tr.device, ids.n)

    def do_fwdB():
        with torch.no_grad():
            return tr._v7_forward(tr.net, [obs] * B, [[]] * B, [None] * B, None, tr.device, ids.n)
    lg, v, _ = do_fwd1()

    def do_sample():
        dist = torch.distributions.Categorical(logits=lg[0])
        a = int(dist.sample())
        return float(dist.log_prob(torch.tensor(a, device=lg.device))), float(v[0])
    for f in (do_json, do_obs, do_validate, do_fwd1, do_fwdB, do_sample):
        for _ in range(10):
            f()
    if sync:
        torch.cuda.synchronize()
    t_json = med(do_json, args.reps, False)
    t_obs = med(do_obs, args.reps, sync)
    t_val = med(do_validate, args.reps, False)
    t_f1 = med(do_fwd1, args.reps, sync)
    t_fB = med(do_fwdB, args.reps, sync)
    t_smp = med(do_sample, args.reps, sync)
    total1 = t_json + t_obs + t_f1 + t_smp
    print(f"CONSULT|arch=v7|device={args.device}|entities={n_ent}|k={k}"
          f"|tokens={obs.n_tokens + k + obs.opp_hand.shape[0] + obs.opp_deck.shape[0] + obs.opp_act.shape[0]}"
          f"|wire_bytes={len(raw)}|json_ms={t_json:.2f}|obs_ms={t_obs:.2f}"
          f"|validate_ms={t_val:.2f}"
          f"|fwd1_ms={t_f1:.2f}|fwd{B}_ms={t_fB:.2f}"
          f"|fwd{B}_per_row_ms={t_fB / B:.2f}|sample_ms={t_smp:.2f}"
          f"|total_single_ms={total1:.2f}"
          f"|python_share={(t_json + t_obs + t_smp) / total1:.0%}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--entities", type=int, default=30)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--arch", default="entattn", choices=["entattn", "v7"],
                    help="v7 (plan §2 4g): the same stages over a WIRE-V7 "
                         "consult from rl/wire_fixtures.py (--entities/--k "
                         "are the fixture's own draw; 'obs' = parse + collate)")
    args = ap.parse_args()
    torch.set_num_threads(1)
    ps.MAX_K = MAXK
    ps.DEVICE = torch.device(args.device)
    if args.arch == "v7":
        return main_v7(args)
    tr = ps.Trainer(None, 0, None, cdim=CDIM, arch="entattn",
                    gdim=GDIM, edim=EDIM, emax=EMAX)
    gen = torch.Generator().manual_seed(0)
    line = message(gen, args.entities, args.k)
    sync = args.device == "cuda"
    raw = line.encode()

    def do_json():
        return json.loads(raw)
    msg = do_json()
    st, cd, ent = ps.consult_args(msg, tr)

    def do_obs():
        s = tr._entity_obs(*ent)
        c = torch.zeros(1, MAXK, CDIM)
        c[0, :len(cd)] = torch.tensor(cd)
        m = torch.zeros(1, MAXK, dtype=torch.bool)
        m[0, :len(cd)] = True
        return s.to(tr.device), c.to(tr.device), m.to(tr.device)
    s, c, m = do_obs()
    hin = tr.net.initial_hidden(1)
    B = args.batch
    SB = ps.EntityObs(*(torch.cat([t] * B) for t in (s.g, s.e, s.mask, s.rel)))
    CB, MB = torch.cat([c] * B), torch.cat([m] * B)
    HB = tr.net.initial_hidden(B)

    def do_fwd1():
        with torch.no_grad():
            return tr.net(s, c, m, hin)

    def do_fwdB():
        with torch.no_grad():
            return tr.net(SB, CB, MB, HB)
    lg, v, _ = do_fwd1()

    def do_sample():
        dist = torch.distributions.Categorical(logits=lg[0])
        a = int(dist.sample())
        return float(dist.log_prob(torch.tensor(a, device=lg.device))), float(v[0])
    for f in (do_json, do_obs, do_fwd1, do_fwdB, do_sample):
        for _ in range(10):
            f()
    if sync:
        torch.cuda.synchronize()
    t_json = med(do_json, args.reps, False)
    t_obs = med(do_obs, args.reps, sync)
    t_f1 = med(do_fwd1, args.reps, sync)
    t_fB = med(do_fwdB, args.reps, sync)
    t_smp = med(do_sample, args.reps, sync)
    total1 = t_json + t_obs + t_f1 + t_smp
    print(f"CONSULT|device={args.device}|entities={args.entities}|k={args.k}"
          f"|wire_bytes={len(raw)}|json_ms={t_json:.2f}|obs_ms={t_obs:.2f}"
          f"|fwd1_ms={t_f1:.2f}|fwd{B}_ms={t_fB:.2f}"
          f"|fwd{B}_per_row_ms={t_fB / B:.2f}|sample_ms={t_smp:.2f}"
          f"|total_single_ms={total1:.2f}"
          f"|python_share={(t_json + t_obs + t_smp) / total1:.0%}", flush=True)


if __name__ == "__main__":
    main()
