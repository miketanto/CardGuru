"""Self-test for policy_server.InferenceBatcher (BATCHED-INFERENCE-PLAN.md §3).

No engine, no games, seconds. Every row is a property the batcher must
have before a single throughput arm is worth running:

  T1  collate/scatter round-trip: a batched forward equals each row's
      single forward (the path every lane uses today)
  T2  recurrent state isolation: two sessions batched together carry the
      same LSTM hidden as the same sessions run alone; batch order is
      irrelevant
  T3  queue semantics: one request -> one forward within the wait; a
      full batch -> one forward; batch_max+1 -> two; no request waits
      for a later batch
  T4  --batch-max 1 (the default) never touches the batcher
  T5  T1 on cuda at 1e-4, reporting the argmax-flip COUNT (skipped with
      a message when cuda is absent)
  T6  a malformed request fails alone; the rest of its batch completes

    python3 rl/batch_check.py

Exit 0 = every check passed. Numbers, not adjectives.
"""
import sys
import threading
import time

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402

CDIM, GDIM, EDIM, EMAX, MAXK = 94, 16, 48, 96, 96
FAILURES = []
RAN = []


def check(name, ok, detail):
    print("CHECK|%-9s|%s|%s" % (name, "PASS" if ok else "FAIL", detail),
          flush=True)
    RAN.append(name)
    if not ok:
        FAILURES.append(name)


def trainer(seed=0, device="cpu"):
    ps.MAX_K = MAXK
    ps.DEVICE = torch.device(device)
    return ps.Trainer(None, seed, None, cdim=CDIM, arch="entattn",
                      gdim=GDIM, edim=EDIM, emax=EMAX)


def rand_request(tr, gen, ne=None, k=None, hidden="rand", gwidth=GDIM):
    """One consult's tensors exactly as act() builds them: a batch-1
    EntityObs on the device, (1,MAX_K,cdim) cands, (1,MAX_K) mask and a
    (1,d) LSTM hidden pair (or the initial one)."""
    dev = tr.device
    ne = ne or int(torch.randint(1, EMAX + 1, (1,), generator=gen))
    k = k or int(torch.randint(1, MAXK + 1, (1,), generator=gen))
    e = torch.zeros(1, EMAX, EDIM)
    e[0, :ne] = torch.rand(ne, EDIM, generator=gen)
    m = torch.zeros(1, EMAX, dtype=torch.bool)
    m[0, :ne] = True
    rel = torch.zeros(1, EMAX, EMAX, dtype=torch.long)
    for _ in range(int(torch.randint(0, 6, (1,), generator=gen))):
        a, b = torch.randint(0, ne, (2,), generator=gen)
        rel[0, a, b] = int(torch.randint(1, len(ps.RTYPES) + 1, (1,),
                                         generator=gen))
    g = torch.rand(1, gwidth, generator=gen)
    s = ps.EntityObs(g, e, m, rel).to(dev)
    c = torch.zeros(1, MAXK, CDIM)
    c[0, :k] = torch.rand(k, CDIM, generator=gen)
    cm = torch.zeros(1, MAXK, dtype=torch.bool)
    cm[0, :k] = True
    if hidden == "rand":
        hin = (torch.randn(1, tr.net.d, generator=gen).to(dev),
               torch.randn(1, tr.net.d, generator=gen).to(dev))
    elif hidden is None:
        hin = tr.net.initial_hidden(1)
    else:
        hin = hidden
    return s, c.to(dev), cm.to(dev), hin, k


def single(tr, s, c, m, hin):
    with torch.no_grad():
        return tr.net(s, c, m, hin)


def batcher_for(tr, batch_max=8, wait_ms=1.0, net=None):
    return ps.InferenceBatcher(net or tr.net, tr.recurrent, threading.Lock(),
                               batch_max, wait_ms)


# ------------------------------------------------------------------ T1/T5
def roundtrip(tr, atol, name, seeds=3):
    """Batched forward vs each row's single forward. Returns
    (max logit diff, max value diff, argmax flips, rows, padding hits)."""
    worst_l = worst_v = 0.0
    flips = rows = pad_hits = 0
    b = batcher_for(tr)
    for seed in range(seeds):
        gen = torch.Generator().manual_seed(100 + seed)
        for B in (1, 2, 3, 5, 8, 16):
            reqs = [rand_request(tr, gen) for _ in range(B)]
            rq = [ps.InferenceRequest(s, c, m, hin) for s, c, m, hin, _ in reqs]
            b.run_batch(rq)
            for (s, c, m, hin, k), r in zip(reqs, rq):
                if r.error is not None:
                    raise r.error
                lg, v, (h2, c2) = r.out
                lg1, v1, (h1, c1) = single(tr, s, c, m, hin)
                worst_l = max(worst_l, float((lg[m] - lg1[m]).abs().max()))
                worst_v = max(worst_v, float((v - v1).abs().max()),
                              float((h2 - h1).abs().max()),
                              float((c2 - c1).abs().max()))
                ab, a1 = int(lg[0].argmax()), int(lg1[0].argmax())
                flips += int(ab != a1)
                pad_hits += int(ab >= k)
                rows += 1
    ok = worst_l <= atol and worst_v <= atol and flips == 0 and pad_hits == 0
    check(name, ok, "rows=%d max|dlogit|=%.2e max|dvalue,dhidden|=%.2e "
          "argmax_flips=%d padding_selected=%d atol=%g device=%s"
          % (rows, worst_l, worst_v, flips, pad_hits, atol, tr.device))


def test_t1():
    roundtrip(trainer(), 1e-5, "T1-ROUND")


def test_t5():
    if not torch.cuda.is_available():
        check("T5-CUDA", True, "SKIPPED: torch.cuda.is_available() is False")
        return
    roundtrip(trainer(device="cuda"), 1e-4, "T5-CUDA")


# -------------------------------------------------------------------- T2
def test_t2():
    tr = trainer()
    gen = torch.Generator().manual_seed(7)
    steps = 6
    inputs = {sid: [rand_request(tr, gen, hidden=None)[:3]
                    for _ in range(steps)] for sid in "AB"}
    # unbatched trajectories, the existing path
    ref = {}
    for sid in "AB":
        h = None
        traj = []
        for s, c, m in inputs[sid]:
            hin = h if h is not None else tr.net.initial_hidden(1)
            _, _, h = single(tr, s, c, m, hin)
            traj.append(h)
        ref[sid] = traj
    b = batcher_for(tr)
    worst = 0.0
    hid = {"A": None, "B": None}
    for t in range(steps):
        order = "AB" if t % 2 == 0 else "BA"
        rq = {}
        for sid in order:
            s, c, m = inputs[sid][t]
            hin = hid[sid] if hid[sid] is not None \
                else tr.net.initial_hidden(1)
            rq[sid] = ps.InferenceRequest(s, c, m, hin)
        b.run_batch([rq[sid] for sid in order])
        for sid in "AB":
            if rq[sid].error is not None:
                raise rq[sid].error
            hid[sid] = rq[sid].out[2]
            worst = max(worst, float((hid[sid][0] - ref[sid][t][0]).abs().max()),
                        float((hid[sid][1] - ref[sid][t][1]).abs().max()))
    check("T2-HIDDEN", worst <= 1e-5,
          "sessions=2 steps=%d order alternated max|dh|=%.2e atol=1e-5"
          % (steps, worst))


# -------------------------------------------------------------------- T3
class FakeNet:
    """Records batch sizes and forward start times; sleeps like a net."""

    def __init__(self, sleep_s):
        self.sleep_s = sleep_s
        self.sizes, self.starts, self.ends = [], [], []
        self.d = 4

    def __call__(self, S, C, M, H):
        self.starts.append(time.time())
        B = S.size(0)
        self.sizes.append(B)
        time.sleep(self.sleep_s)
        self.ends.append(time.time())
        return torch.zeros(B, C.size(1)), torch.zeros(B), (H[0], H[1])


def submit_n(b, n, dev="cpu"):
    """n threads submit one request each at once; returns per-request
    (submit time, return time)."""
    times = [None] * n
    errs = [None] * n

    def go(i):
        s = torch.zeros(1, 4); c = torch.zeros(1, 8, 3)
        m = torch.ones(1, 8, dtype=torch.bool)
        hin = (torch.zeros(1, 4), torch.zeros(1, 4))
        t0 = time.time()
        try:
            b.infer(s, c, m, hin)
        except Exception as exc:      # noqa: BLE001
            errs[i] = exc
        times[i] = (t0, time.time())
    th = [threading.Thread(target=go, args=(i,)) for i in range(n)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    return times, errs


def test_t3():
    wait_ms, sleep_s = 50.0, 0.02
    net = FakeNet(sleep_s)
    b = ps.InferenceBatcher(net, True, threading.Lock(), 4, wait_ms)
    b.start()
    # (a) one request
    times, errs = submit_n(b, 1)
    lat = times[0][1] - times[0][0]
    ok_a = errs[0] is None and net.sizes == [1] and \
        lat <= wait_ms / 1000 + sleep_s + 0.05
    det_a = "one: sizes=%s latency_ms=%.1f (<= %.0f wait + 20 fwd + 50)" % (
        net.sizes, 1000 * lat, wait_ms)
    # (b) batch_max at once
    net.sizes.clear(); net.starts.clear(); net.ends.clear()
    times, errs = submit_n(b, 4)
    ok_b = all(e is None for e in errs) and net.sizes == [4]
    det_b = "full: sizes=%s" % net.sizes
    # (c) batch_max + 1 -> two forwards; the first batch never waits for
    # the second: every member of batch 1 has returned before forward 2
    # starts
    net.sizes.clear(); net.starts.clear(); net.ends.clear()
    times, errs = submit_n(b, 5)
    rets = sorted(t1 for _, t1 in times)
    ok_c = all(e is None for e in errs) and sorted(net.sizes) == [1, 4] \
        and len(net.starts) == 2 and rets[net.sizes[0] - 1] <= net.starts[1]
    det_c = "over: sizes=%s first_batch_all_returned_before_fwd2=%s" % (
        net.sizes, len(net.starts) == 2 and rets[net.sizes[0] - 1] <= net.starts[1])
    st = b.stats()
    check("T3-QUEUE", ok_a and ok_b and ok_c,
          "%s | %s | %s | stats: %s" % (det_a, det_b, det_c, st))


# -------------------------------------------------------------------- T4
def test_t4():
    tr = trainer()
    calls = []
    orig_infer, orig_run = ps.InferenceBatcher.infer, ps.InferenceBatcher.run_batch

    def spy(self, *a, **kw):
        calls.append(1)
        return orig_infer(self, *a, **kw)

    def spy2(self, *a, **kw):
        calls.append(1)
        return orig_run(self, *a, **kw)
    ps.InferenceBatcher.infer, ps.InferenceBatcher.run_batch = spy, spy2
    try:
        gen = torch.Generator().manual_seed(3)
        sess = ps.Session()
        for _ in range(5):
            ne = int(torch.randint(1, 20, (1,), generator=gen))
            k = int(torch.randint(1, 10, (1,), generator=gen))
            g = torch.rand(GDIM, generator=gen).tolist()
            ents = torch.rand(ne, EDIM, generator=gen).tolist()
            cands = torch.rand(k, CDIM, generator=gen).tolist()
            tr.act(None, cands, sample=True, session=sess, ent=(g, ents, []))
    finally:
        ps.InferenceBatcher.infer, ps.InferenceBatcher.run_batch = \
            orig_infer, orig_run
    check("T4-OLDPATH", getattr(tr, "batcher", None) is None and not calls,
          "batcher=%r batcher_calls=%d consults=5 pending=%d"
          % (getattr(tr, "batcher", None), len(calls), len(sess.pending)))


# -------------------------------------------------------------------- T6
def test_t6():
    tr = trainer()
    gen = torch.Generator().manual_seed(11)
    good = [rand_request(tr, gen) for _ in range(2)]
    bad = rand_request(tr, gen, gwidth=GDIM + 1)
    reqs = [good[0], bad, good[1]]
    b = batcher_for(tr, batch_max=3, wait_ms=100.0)
    b.start()
    outs = [None] * 3
    errs = [None] * 3

    def go(i):
        s, c, m, hin, _ = reqs[i]
        try:
            outs[i] = b.infer(s, c, m, hin)
        except Exception as exc:      # noqa: BLE001
            errs[i] = exc
    th = [threading.Thread(target=go, args=(i,)) for i in range(3)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    worst = 0.0
    for i in (0, 2):
        if outs[i] is not None:
            s, c, m, hin, _ = reqs[i]
            lg1, v1, _ = single(tr, s, c, m, hin)
            worst = max(worst, float((outs[i][0][m] - lg1[m]).abs().max()))
    ok = errs[1] is not None and errs[0] is None and errs[2] is None \
        and outs[0] is not None and outs[2] is not None and worst <= 1e-5
    check("T6-ERROR", ok, "bad_req_error=%s good_errors=%s good_max|dlogit|=%.2e"
          % (type(errs[1]).__name__ if errs[1] else None,
             [type(e).__name__ if e else None for e in (errs[0], errs[2])],
             worst))


def main():
    t0 = time.time()
    torch.set_num_threads(1)
    for name, fn in (("T1", test_t1), ("T2", test_t2), ("T3", test_t3),
                     ("T4", test_t4), ("T5", test_t5), ("T6", test_t6)):
        try:
            fn()
        except Exception as exc:      # noqa: BLE001
            check(name + "-RAISED", False, "%s: %s" % (type(exc).__name__,
                                                       str(exc)[:160]))
    print("BATCH|checks=%d|failures=%d|%.1fs"
          % (len(RAN), len(FAILURES), time.time() - t0), flush=True)
    if FAILURES:
        print("FAILED: " + ", ".join(FAILURES))
        sys.exit(1)


if __name__ == "__main__":
    main()
