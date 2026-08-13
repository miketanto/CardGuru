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
    args = ap.parse_args()

    if os.path.exists(args.out):
        print(f"P10INIT|exists|{args.out} (left untouched)")
        return
    ps = load_policy_server()
    torch.manual_seed(args.seed)
    net = ps.build_net(args.arch, args.sdim, args.cdim)
    opt = torch.optim.Adam(net.parameters(), lr=ps.LR)
    tmp = args.out + ".tmp"
    torch.save({"net": net.state_dict(), "opt": opt.state_dict(),
                "episodes": 0, "updates": 0, "arch": args.arch}, tmp)
    os.replace(tmp, args.out)
    n = sum(p.numel() for p in net.parameters())
    print(f"P10INIT|out={args.out}|arch={args.arch}|seed={args.seed}"
          f"|cdim={args.cdim}|params={n}")


if __name__ == "__main__":
    main()
