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
    buf = [(ps.EntityObs(*b[0]),) + tuple(b[1:]) for b in d["buf"]]
    return buf, [tuple(c) for c in d["completed"]]


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
    ev = prof.events()
    kern = [e for e in ev
            if e.device_type == torch.autograd.DeviceType.CUDA]
    ktime = sum(e.time_range.elapsed_us() for e in kern) / 1e6
    print(f"UPDPROF|buf steps={n} episodes={len(completed)} device={args.device}"
          f"|warmup_s={warm:.2f}|profiled_s={secs:.2f}"
          f"|ms_per_step={1000 * secs / n:.2f}", flush=True)
    if kern:
        durs = sorted(e.time_range.elapsed_us() for e in kern)
        print(f"UPDKERN|launches={len(kern)}|per_step={len(kern) / n:.1f}"
              f"|kernel_time_s={ktime:.2f}|gpu_busy={ktime / secs:.1%}"
              f"|median_us={durs[len(durs) // 2]:.1f}"
              f"|p90_us={durs[int(0.9 * len(durs))]:.1f}", flush=True)
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
    args = ap.parse_args()
    if args.buf:
        buf, completed = load_buf(args.buf)
    elif args.synth:
        buf, completed = synth_buf(args.seed)
    else:
        ap.error("--buf or --synth")
    torch.set_num_threads(1)          # the server's inference count
    if args.mode == "threads":
        mode_threads(args, buf, completed)
    else:
        mode_profile(args, buf, completed)


if __name__ == "__main__":
    main()
