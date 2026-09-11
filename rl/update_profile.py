"""Offline harness for ONE PPO update() of policy_server.Trainer.

THROUGHPUT-LOCAL.md §10. Two modes, no engine, no games:

  threads   run the same update from the same buffer and seed once per
            --threads value; report wall seconds and the max |Δweight|
            against the first arm (the §10.0 pre-registered 1e-6 check
            for --update-threads).
  profile   run the update under torch.profiler on --device; report the
            top-10 ops by device time and by CPU time, the number of CUDA
            kernel launches per stored consult, and GPU busy share.

The buffer is a real one dumped by the server (RL_DUMP_BUF=<path>, the
first update of a lane) or, with --synth, random tensors of the same
shapes (32 episodes, ~50 steps each). Weights come from --ckpt when
given, else from the seed. Nothing here writes a checkpoint.

    python3 rl/update_profile.py threads --buf /tmp/rl_buf.pt --threads 1 8 16
    python3 rl/update_profile.py profile --buf /tmp/rl_buf.pt --device cuda
"""
import argparse
import sys
import time

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402

CDIM, GDIM, EDIM, EMAX, MAXK = 94, 16, 48, 96, 96


def make_trainer(args):
    ps.MAX_K = MAXK
    ps.DEVICE = torch.device(args.device)
    if args.arch == "v7":
        # v7 plan §2 4g memory gate: the assembled policy at its real size
        # unless --layers/--value-layers shrink it for a CPU smoke run
        tr = ps.Trainer(None, args.seed, None, arch="v7", card_emb="random")
        if args.layers or args.value_layers:
            import v7_policy
            torch.manual_seed(args.seed)
            tr.net = v7_policy.V7Policy(random_table=True, layers=args.layers or 6,
                                        value_layers=args.value_layers or 4).to(tr.device)
            tr.opt = torch.optim.Adam(tr.net.policy_parameters(), lr=ps.LR)
        tr.tbptt, tr.ep_batch = args.tbptt, args.ep_batch
    else:
        tr = ps.Trainer(None, args.seed, None, cdim=CDIM, arch="entattn",
                        gdim=GDIM, edim=EDIM, emax=EMAX)
    if args.ckpt:
        data = torch.load(args.ckpt, map_location="cpu", weights_only=False)
        tr.net.load_state_dict(data["net"])
        if "opt" in data:
            tr.opt.load_state_dict(data["opt"])
    return tr


def load_buf(path):
    d = torch.load(path, map_location="cpu", weights_only=False)
    if d.get("arch") == "v7":
        # the v7 dump holds V7Obs entries as the server stored them
        return list(d["buf"]), [tuple(c) for c in d["completed"]]
    buf = [(ps.EntityObs(*b[0]),) + tuple(b[1:]) for b in d["buf"]]
    return buf, [tuple(c) for c in d["completed"]]


def mem_line():
    """Peak memory of this process: RSS high-water mark (Linux: KB from
    getrusage) and the CUDA allocator's peak, in MB. The 4g gate is the
    RSS against the 16 GB cgroup."""
    import resource
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    cuda = (torch.cuda.max_memory_allocated() / 2 ** 20
            if torch.cuda.is_available() else 0.0)
    return f"UPDMEM|rss_max_mb={rss:.0f}|cuda_peak_mb={cuda:.0f}"


def synth_buf_v7(seed=0, episodes=32, mean_len=50, ent_max=160, k_max=40,
                 hand=7, deck=40, acts=8, n_ids=1000):
    """Random V7Obs of realistic sizes (WIRE-V7.md §2 widths; entities
    uniform in [20, ent_max], candidates in [2, k_max], opponent tokens as
    given): the same tuple layout act_v7 stores. Tokens per state run
    to 3 + ent_max + k_max + hand + deck + acts (~260 at the defaults)."""
    import v7_obs as V
    import wire_validate as W
    g = torch.Generator().manual_seed(seed)
    D = W.DIMS
    buf, completed = [], []

    def onehot_rows(n, width, start, end):
        x = torch.rand(n, width, generator=g)
        x[:, start:end] = 0
        x[torch.arange(n), start + torch.randint(0, end - start, (n,), generator=g)] = 1.0
        return x

    for _ in range(episodes):
        n = int(torch.poisson(torch.tensor([float(mean_len)]), generator=g).item()) + 5
        start = len(buf)
        for _t in range(n):
            N = int(torch.randint(20, ent_max + 1, (1,), generator=g))
            K = int(torch.randint(2, k_max + 1, (1,), generator=g))
            T = 3 + N
            edges = torch.zeros(T, T, dtype=torch.int8)
            for _e in range(int(torch.randint(0, 3 * N, (1,), generator=g))):
                s, d_ = torch.randint(0, T, (2,), generator=g)
                edges[s, d_] = int(torch.randint(1, W.RTYPES + 1, (1,), generator=g))
            refers = torch.zeros(K, T, dtype=torch.uint8)
            refers[torch.arange(K), torch.randint(0, T, (K,), generator=g)] = 1
            oar = torch.zeros(acts, T, dtype=torch.uint8)
            oar[torch.arange(acts), torch.randint(0, T, (acts,), generator=g)] = 1
            obs = V.V7Obs(
                game=torch.rand(D["game"], generator=g), players=torch.rand(2, D["player"], generator=g),
                ent=onehot_rows(N, D["ent"], 0, W.ZONES), ent_id=torch.randint(-1, n_ids, (N,), generator=g),
                ent_name=[""] * N, edges=edges,
                cand_type=torch.randint(0, W.CTYPES, (K,), generator=g), cand=torch.rand(K, D["cand"], generator=g),
                refers=refers, opp_hand=torch.rand(hand, D["opp_hand"], generator=g),
                opp_hand_id=torch.full((hand,), -1, dtype=torch.long),
                opp_deck=torch.rand(deck, D["opp_deck"], generator=g),
                opp_deck_id=torch.randint(0, n_ids, (deck,), generator=g),
                opp_act=torch.rand(acts, D["opp_action"], generator=g), opp_act_refers=oar)
            a = int(torch.randint(0, K, (1,), generator=g))
            buf.append((obs, a, -float(torch.log(torch.tensor(float(K)))),
                        float(torch.randn(1, generator=g)) * 0.1, 0.0, [], None))
        reward = 1.0 if int(torch.randint(0, 2, (1,), generator=g)) else -1.0
        completed.append((start, len(buf), reward))
    return buf, completed


def synth_buf(seed=0, episodes=32, mean_len=50):
    g = torch.Generator().manual_seed(seed)
    buf, completed = [], []
    for _ in range(episodes):
        n = int(torch.poisson(torch.tensor([float(mean_len)]),
                              generator=g).item()) + 5
        start = len(buf)
        h = torch.zeros(128)
        for _t in range(n):
            ne = int(torch.randint(4, 40, (1,), generator=g))
            k = int(torch.randint(1, 24, (1,), generator=g))
            e = torch.zeros(EMAX, EDIM)
            e[:ne] = torch.rand(ne, EDIM, generator=g)
            m = torch.zeros(EMAX, dtype=torch.bool)
            m[:ne] = True
            rel = torch.zeros(EMAX, EMAX, dtype=torch.long)
            nrel = int(torch.randint(0, 8, (1,), generator=g))
            for _r in range(nrel):
                s, d_ = torch.randint(0, ne, (2,), generator=g)
                rel[s, d_] = int(torch.randint(1, len(ps.RTYPES) + 1, (1,),
                                               generator=g))
            obs = ps.EntityObs(torch.rand(GDIM, generator=g), e, m, rel)
            c = torch.zeros(MAXK, CDIM)
            c[:k] = torch.rand(k, CDIM, generator=g)
            cm = torch.zeros(MAXK, dtype=torch.bool)
            cm[:k] = True
            a = int(torch.randint(0, k, (1,), generator=g))
            buf.append((obs, c, cm, a, -float(torch.log(torch.tensor(k))),
                        float(torch.randn(1, generator=g)) * 0.1, 0.0,
                        (h.clone(), h.clone()), None))
        reward = 1.0 if int(torch.randint(0, 2, (1,), generator=g)) else -1.0
        completed.append((start, len(buf), reward))
    return buf, completed


def arm(args, buf, completed):
    tr = make_trainer(args)
    tr.buf = list(buf)
    tr.completed = list(completed)
    tr.ep_start = len(tr.buf)
    tr.episodes_seen = len(completed)
    return tr


def run_update(tr, seed):
    torch.manual_seed(seed)           # randperm inside _update_recurrent
    if tr.device.type == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()
    tr.update()
    if tr.device.type == "cuda":
        torch.cuda.synchronize()
    return time.time() - t0


def mode_threads(args, buf, completed):
    n = len(buf)
    base = None
    print(f"UPDPROF|buf steps={n} episodes={len(completed)} "
          f"device={args.device} torch={torch.__version__}", flush=True)
    for nt in args.threads:
        tr = arm(args, buf, completed)
        tr.update_threads = nt
        before = torch.get_num_threads()
        secs = run_update(tr, args.seed + 1)
        after = torch.get_num_threads()
        sd = {k: v.detach().cpu().clone() for k, v in tr.net.state_dict().items()}
        if base is None:
            base, dmax = sd, 0.0
        else:
            dmax = max(float((sd[k] - base[k]).abs().max()) for k in sd)
        print(f"UPDTHREADS|threads={nt}|update_s={secs:.2f}"
              f"|ms_per_step={1000 * secs / n:.2f}"
              f"|max_abs_dw_vs_first={dmax:.3e}"
              f"|threads_restored={'yes' if before == after else 'NO'}",
              flush=True)
        print(mem_line(), flush=True)


def mode_profile(args, buf, completed):
    from torch.profiler import profile, ProfilerActivity
    n = len(buf)
    # warm-up (cuDNN/cuBLAS handles, allocator) on a throwaway copy
    tr = arm(args, buf, completed)
    warm = run_update(tr, args.seed + 1)
    tr = arm(args, buf, completed)
    acts = [ProfilerActivity.CPU]
    if args.device == "cuda":
        acts.append(ProfilerActivity.CUDA)
    with profile(activities=acts) as prof:
        secs = run_update(tr, args.seed + 1)
    # key_averages, not events(): a full update is ~10^6 events and the
    # per-event Python walk swapped the machine out (12 GB) the first time
    ka = prof.key_averages()
    kern = [r for r in ka if r.device_type == torch.autograd.DeviceType.CUDA]
    launches = sum(r.count for r in kern)
    ktime = sum(r.self_device_time_total for r in kern) / 1e6
    print(f"UPDPROF|buf steps={n} episodes={len(completed)} device={args.device}"
          f"|warmup_s={warm:.2f}|profiled_s={secs:.2f}"
          f"|ms_per_step={1000 * secs / n:.2f}", flush=True)
    print(mem_line(), flush=True)
    if kern:
        us = sorted((r.self_device_time_total / r.count, r.count)
                    for r in kern)
        cum, med = 0, 0.0
        for d, c in us:
            cum += c
            if cum * 2 >= launches:
                med = d
                break
        print(f"UPDKERN|launches={launches}|per_step={launches / n:.1f}"
              f"|distinct_kernels={len(kern)}"
              f"|kernel_time_s={ktime:.2f}|gpu_busy={ktime / secs:.1%}"
              f"|median_launch_us={med:.1f}", flush=True)
    key = "cuda_time_total" if args.device == "cuda" else "cpu_time_total"
    print("TOP10 by", key)
    print(prof.key_averages().table(sort_by=key, row_limit=10,
                                    max_name_column_width=48))
    if args.device == "cuda":
        print("TOP10 by cpu_time_total")
        print(prof.key_averages().table(sort_by="cpu_time_total",
                                        row_limit=10,
                                        max_name_column_width=48))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["threads", "profile"])
    ap.add_argument("--buf", default=None, help="RL_DUMP_BUF file")
    ap.add_argument("--synth", action="store_true")
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, nargs="+", default=[1, 8, 16])
    ap.add_argument("--episodes", type=int, default=0,
                    help="use only the first K episodes of the buffer "
                         "(profiler traces of a full update do not fit "
                         "in 12 GB)")
    # v7 (plan §2 4g memory gate): --arch v7 --synth builds V7Obs buffers
    ap.add_argument("--arch", default="entattn", choices=["entattn", "v7"])
    ap.add_argument("--steps", type=int, default=0,
                    help="v7 --synth: total steps to generate (episodes "
                         "of --mean-len); 0 = 32 episodes")
    ap.add_argument("--mean-len", type=int, default=50)
    ap.add_argument("--ent-max", type=int, default=160)
    ap.add_argument("--tbptt", type=int, default=32)
    ap.add_argument("--ep-batch", type=int, default=4)
    ap.add_argument("--layers", type=int, default=0, help="v7: encoder layers (0 = 6)")
    ap.add_argument("--value-layers", type=int, default=0, help="v7: value trunk layers (0 = 4)")
    args = ap.parse_args()
    if args.buf:
        buf, completed = load_buf(args.buf)
    elif args.synth and args.arch == "v7":
        eps = max(1, args.steps // args.mean_len) if args.steps else 32
        buf, completed = synth_buf_v7(args.seed, episodes=eps, mean_len=args.mean_len,
                                      ent_max=args.ent_max)
        if args.steps:
            completed = [c for c in completed if c[1] <= args.steps]
            buf = buf[:completed[-1][1]]
    elif args.synth:
        buf, completed = synth_buf(args.seed)
    else:
        ap.error("--buf or --synth")
    if args.episodes and args.episodes < len(completed):
        completed = completed[:args.episodes]
        buf = buf[:completed[-1][1]]
    torch.set_num_threads(1)          # the server's inference count
    if args.mode == "threads":
        mode_threads(args, buf, completed)
    else:
        mode_profile(args, buf, completed)


if __name__ == "__main__":
    main()
