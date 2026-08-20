"""Phase 10: mint the shared from-scratch lstmattn initialization.

The flagship and its control arm (agent locked to BenchDimir) are only
an A/B if they start from the SAME random net, so the init is minted
once, committed to rl/artifacts, and both lanes point at it. Nothing is
trained here: this writes a checkpoint in exactly the format
policy_server.py's Trainer expects (net / opt / episodes / updates /
arch), with episodes=0.

Run: python3 rl/p10_init_net.py --out /tmp/rl_p10_scratch_init.pt [--seed 10]
"""
import argparse
import importlib.util
import os

import torch

HERE = os.path.dirname(os.path.abspath(__file__))


def load_policy_server():
    spec = importlib.util.spec_from_file_location(
        "policy_server", os.path.join(HERE, "policy_server.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=10,
                    help="10 = Phase 10; Phase 7b's scratch init used 0, "
                         "so this is an independent draw of the same "
                         "architecture, not a re-run of that line")
    ap.add_argument("--arch", default="lstmattn")
    ap.add_argument("--sdim", type=int, default=24)
    ap.add_argument("--cdim", type=int, default=91)
    # encoder v6 (--arch entattn): the entity/relation widths. They are
    # MEANING, not buffers, so they go into the checkpoint's dims record
    # and a server started with different ones refuses to load it.
    ap.add_argument("--gdim", type=int, default=16)
    ap.add_argument("--edim", type=int, default=48)
    ap.add_argument("--r0", action="store_true",
                    help="mint the ablation arm's init (relations dropped)")
    args = ap.parse_args()

    if os.path.exists(args.out):
        print(f"P10INIT|exists|{args.out} (left untouched)")
        return
    ps = load_policy_server()
    torch.manual_seed(args.seed)
    net = ps.build_net(args.arch, args.sdim, args.cdim, args.gdim, args.edim,
                       len(ps.RTYPES))
    opt = torch.optim.Adam(net.parameters(), lr=ps.LR)
    # the dims record Trainer._check_ckpt_dims validates on load: without
    # it the server prints "loading unchecked" and a mismatched arm would
    # get a whole run before anyone noticed
    dims = ({"gdim": args.gdim, "edim": args.edim, "cdim": args.cdim,
             "rtypes": len(ps.RTYPES), "r0": args.r0}
            if args.arch == "entattn"
            else {"sdim": args.sdim, "cdim": args.cdim})
    tmp = args.out + ".tmp"
    torch.save({"net": net.state_dict(), "opt": opt.state_dict(),
                "episodes": 0, "updates": 0, "arch": args.arch,
                "dims": dims}, tmp)
    os.replace(tmp, args.out)
    n = sum(p.numel() for p in net.parameters())
    print(f"P10INIT|out={args.out}|arch={args.arch}|seed={args.seed}"
          f"|cdim={args.cdim}|params={n}")


if __name__ == "__main__":
    main()
