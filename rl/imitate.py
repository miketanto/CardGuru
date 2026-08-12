"""Phase 5 C1: supervised imitation of the D1 search teacher.

Input: NDJSON from TeacherLogPlayer (rl.imitateOut) — one example per
consult ({"t","y","s","c"}) plus {"t":"end","r"} episode markers.
Net: E0Policy from policy_server.py, unchanged — cross-entropy on the
teacher's action over the candidate softmax; value head regressed on the
per-consult-discounted terminal reward (gamma 0.997, matching PPO), so a
later fine-tune starts with a sane critic.
Checkpoint: policy_server.py --ckpt format (net/opt/episodes/updates) —
the trained student is served for eval with the stock server.

Run: python3 rl/imitate.py --data /tmp/rl_p5_c1/train.ndjson \
        --ckpt /tmp/rl_p5_c1/student.pt [--epochs 4] [--batch 256] \
        [--val-frac 0.05] [--seed 0] [--log /tmp/rl_p5_c1/imitate.csv]
"""
import argparse
import json
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from policy_server import build_net, GAMMA, MAX_K  # noqa: E402


def load(path):
    """-> episodes: list of (examples, reward); example = (kind, y, s, c)"""
    episodes, cur = [], []
    for line in open(path):
        d = json.loads(line)
        if d["t"] == "end":
            episodes.append((cur, float(d["r"])))
            cur = []
        else:
            cur.append((d["t"], d["y"], d["s"], d["c"]))
    if cur:
        episodes.append((cur, 0.0))    # truncated tail: neutral reward
    return episodes


def flatten(episodes):
    """-> list of (kind, y, s, c, value_target) with per-consult discount"""
    out = []
    for examples, reward in episodes:
        n = len(examples)
        for i, (k, y, s, c) in enumerate(examples):
            out.append((k, y, s, c, reward * (GAMMA ** (n - 1 - i))))
    return out


def batches(data, batch_size, cdim, shuffle, gen):
    idx = torch.randperm(len(data), generator=gen) if shuffle \
        else torch.arange(len(data))
    for b0 in range(0, len(data), batch_size):
        chunk = [data[i] for i in idx[b0:b0 + batch_size]]
        bs = len(chunk)
        s = torch.tensor([e[2] for e in chunk])
        c = torch.zeros(bs, MAX_K, cdim)
        m = torch.zeros(bs, MAX_K, dtype=torch.bool)
        y = torch.tensor([e[1] for e in chunk])
        v = torch.tensor([e[4] for e in chunk])
        for i, e in enumerate(chunk):
            k = min(len(e[3]), MAX_K)
            c[i, :k] = torch.tensor(e[3][:k])
            m[i, :k] = True
        yield chunk, s, c, m, y, v


def fwd(net, s, c, m):
    out = net(s, c, m)          # lstmattn returns (logits, value, hidden)
    return out[0], out[1]


def seq_step_tensors(group, live, t, cdim):
    """Tensors for step t of the live episodes in this group."""
    rows = [group[bi][t] for bi in live]
    bs = len(rows)
    s = torch.tensor([e[2] for e in rows])
    c = torch.zeros(bs, MAX_K, cdim)
    m = torch.zeros(bs, MAX_K, dtype=torch.bool)
    for i, e in enumerate(rows):
        k = len(e[3])
        c[i, :k] = torch.tensor(e[3])
        m[i, :k] = True
    y = torch.tensor([e[1] for e in rows])
    v = torch.tensor([e[4] for e in rows])
    return rows, s, c, m, y, v


def run_seq(net, episodes_ex, cdim, ep_batch, tbptt, val_coef,
            opt=None, gen=None):
    """One pass over episode sequences with carried hidden (TBPTT when
    opt is set; pure inference for validation when opt is None).
    -> (mean_loss, acc, by_kind, nonpass_acc)"""
    order = (torch.randperm(len(episodes_ex), generator=gen) if opt is not None
             else torch.arange(len(episodes_ex)))
    tot_loss = tot_n = hits = 0
    by_kind = {}
    np_hits = np_tot = 0
    ctx = torch.enable_grad() if opt is not None else torch.no_grad()
    with ctx:
        for g0 in range(0, len(episodes_ex), ep_batch):
            group = [episodes_ex[i] for i in order[g0:g0 + ep_batch]]
            maxlen = max(len(e) for e in group)
            h, hc = net.initial_hidden(len(group))
            losses, n_group = [], 0
            for t in range(maxlen):
                live = [bi for bi, e in enumerate(group) if t < len(e)]
                lt = torch.tensor(live)
                rows, s, c, m, y, v = seq_step_tensors(group, live, t, cdim)
                logits, value, (h2, c2) = net(s, c, m, (h[lt], hc[lt]))
                h = h.clone(); hc = hc.clone()
                h[lt] = h2; hc[lt] = c2
                if opt is not None and (t + 1) % tbptt == 0:
                    h = h.detach(); hc = hc.detach()
                losses.append(F.cross_entropy(logits, y, reduction="sum")
                              + val_coef * F.mse_loss(value, v,
                                                      reduction="sum"))
                n_group += len(rows)
                pred = logits.argmax(dim=1)
                ok = pred == y
                hits += int(ok.sum())
                for i, e in enumerate(rows):
                    kh, kt = by_kind.get(e[0], (0, 0))
                    by_kind[e[0]] = (kh + int(ok[i]), kt + 1)
                    if e[0] in ("tgt", "card") or e[1] > 0:
                        np_hits += int(ok[i])
                        np_tot += 1
            loss = torch.stack(losses).sum() / max(1, n_group)
            if opt is not None:
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
                opt.step()
            tot_loss += float(loss.detach()) * n_group
            tot_n += n_group
    return (tot_loss / max(1, tot_n), hits / max(1, tot_n),
            {k: kh / max(1, kt) for k, (kh, kt) in sorted(by_kind.items())},
            np_hits / max(1, np_tot))


def accuracy(net, data, batch_size, cdim):
    hits = tot = 0
    by_kind = {}
    nonpass_hits = nonpass_tot = 0
    with torch.no_grad():
        for chunk, s, c, m, y, v in batches(data, batch_size, cdim,
                                            False, None):
            logits, _ = fwd(net, s, c, m)
            pred = logits.argmax(dim=1)
            ok = pred == y
            hits += int(ok.sum())
            tot += len(chunk)
            for i, e in enumerate(chunk):
                h, t = by_kind.get(e[0], (0, 0))
                by_kind[e[0]] = (h + int(ok[i]), t + 1)
                # non-pass: prio/blk label>0 is an action; atk label 1;
                # tgt/card have no pass slot, count all
                if e[0] in ("tgt", "card") or e[1] > 0:
                    nonpass_hits += int(ok[i])
                    nonpass_tot += 1
    return (hits / max(1, tot),
            {k: h / max(1, t) for k, (h, t) in sorted(by_kind.items())},
            nonpass_hits / max(1, nonpass_tot))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--val-frac", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--val-coef", type=float, default=0.5)
    ap.add_argument("--sdim", type=int, default=24)
    ap.add_argument("--cdim", type=int, default=38)
    ap.add_argument("--log", default=None)
    ap.add_argument("--arch", default="e0",
                    choices=["e0", "attn", "lstmattn"])
    ap.add_argument("--seq", type=int, default=None,
                    help="1=episode-sequence BC with carried hidden "
                         "(default for lstmattn), 0=flat shuffled BC")
    ap.add_argument("--ep-batch", type=int, default=16)
    ap.add_argument("--tbptt", type=int, default=64)
    ap.add_argument("--init", default=None,
                    help="ckpt to resume BC from (net+opt state)")
    args = ap.parse_args()
    seq = (args.arch == "lstmattn") if args.seq is None else bool(args.seq)

    torch.manual_seed(args.seed)
    gen = torch.Generator().manual_seed(args.seed)
    if seq:
        # tiny per-step batches: default thread pool thrashes (>10x
        # slowdown observed on the BPTT smoke test)
        torch.set_num_threads(2)

    episodes = load(args.data)
    n_val_ep = max(1, int(len(episodes) * args.val_frac))
    net = build_net(args.arch, args.sdim, args.cdim)
    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    if args.init:
        data = torch.load(args.init, weights_only=False)
        if data.get("arch", "e0") != args.arch:
            raise RuntimeError(f"init arch {data.get('arch')} != {args.arch}")
        net.load_state_dict(data["net"])
        opt.load_state_dict(data["opt"])
        print(f"resumed BC from {args.init}", flush=True)
    logf = open(args.log, "a") if args.log else None

    if seq:
        # Phase 7: episode-sequence BC - hidden carried across a whole
        # episode's consults (TBPTT), so the cell learns real memory
        # dynamics instead of a zero-hidden approximation. An episode
        # containing any over-length candidate set is dropped whole:
        # skipping a consult mid-sequence would desync the hidden state.
        def to_seq(eps):
            out, dropped = [], 0
            for examples, reward in eps:
                fl = flatten([(examples, reward)])
                if any(len(e[3]) > MAX_K for e in fl) or not fl:
                    dropped += 1
                    continue
                out.append(fl)
            return out, dropped
        train_ep, d1 = to_seq(episodes[:-n_val_ep])
        val_ep, d2 = to_seq(episodes[-n_val_ep:])
        print(f"episodes={len(episodes)} train_eps={len(train_ep)} "
              f"val_eps={len(val_ep)} dropped_episodes={d1 + d2}",
              flush=True)
        for ep in range(args.epochs):
            tr_loss, _, _, _ = run_seq(
                net, train_ep, args.cdim, args.ep_batch, args.tbptt,
                args.val_coef, opt=opt, gen=gen)
            _, acc, by_kind, nonpass = run_seq(
                net, val_ep, args.cdim, args.ep_batch, args.tbptt,
                args.val_coef)
            line = (f"epoch={ep + 1} loss={tr_loss:.4f} "
                    f"val_acc={acc:.4f} nonpass_acc={nonpass:.4f} "
                    f"by_kind={by_kind}")
            print(line, flush=True)
            if logf:
                logf.write(line + "\n")
                logf.flush()
    else:
        train = flatten(episodes[:-n_val_ep])
        val = flatten(episodes[-n_val_ep:])
        # drop the rare over-length candidate sets entirely (train AND
        # val): truncation would relabel actions beyond MAX_K
        dropped = sum(1 for e in train + val if len(e[3]) > MAX_K)
        train = [e for e in train if len(e[3]) <= MAX_K]
        val = [e for e in val if len(e[3]) <= MAX_K]
        print(f"episodes={len(episodes)} train={len(train)} val={len(val)} "
              f"dropped_overlength={dropped}", flush=True)

        for ep in range(args.epochs):
            tot_loss = n_batches = 0
            for chunk, s, c, m, y, v in batches(train, args.batch,
                                                args.cdim, True, gen):
                logits, value = fwd(net, s, c, m)
                loss = F.cross_entropy(logits, y) \
                    + args.val_coef * F.mse_loss(value, v)
                opt.zero_grad()
                loss.backward()
                opt.step()
                tot_loss += float(loss)
                n_batches += 1
            acc, by_kind, nonpass = accuracy(net, val, args.batch,
                                             args.cdim)
            line = (f"epoch={ep + 1} "
                    f"loss={tot_loss / max(1, n_batches):.4f} "
                    f"val_acc={acc:.4f} nonpass_acc={nonpass:.4f} "
                    f"by_kind={by_kind}")
            print(line, flush=True)
            if logf:
                logf.write(line + "\n")
                logf.flush()

    torch.save({"net": net.state_dict(), "opt": opt.state_dict(),
                "episodes": len(episodes), "updates": 0,
                "arch": args.arch}, args.ckpt)
    print(f"saved {args.ckpt}", flush=True)


if __name__ == "__main__":
    main()
