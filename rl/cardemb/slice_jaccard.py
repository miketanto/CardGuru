"""G3 diagnostic for a block-structured e_card: per-slice seed stability.

Top-10 Jaccard between seed 0 and seed 1 on 2,000 random cards, for the
whole vector, for each slice (text 0:48, tree 48:80, bag 80:96, printed
96:128), and for the whole vector with one slice removed.

Run: python3 rl/cardemb/slice_jaccard.py rl/artifacts/card_emb_vN
     (needs emb.pt and emb_seed1.pt in that directory)
"""
import random
import sys

import torch

art = sys.argv[1]
E0 = torch.load(f"{art}/emb.pt").float()
E1 = torch.load(f"{art}/emb_seed1.pt").float()
SL = {"text": (0, 48), "tree": (48, 80), "bag": (80, 96), "printed": (96, 128)}


def jac(A, B, k=10, n=2000):
    A = A / A.norm(dim=1, keepdim=True).clamp(min=1e-6)
    B = B / B.norm(dim=1, keepdim=True).clamp(min=1e-6)
    g = random.Random(0)
    idx = g.sample(range(A.shape[0]), n)
    js = []
    for i in idx:
        sa = A @ A[i]; sa[i] = -2
        sb = B @ B[i]; sb[i] = -2
        ta, tb = set(sa.topk(k).indices.tolist()), set(sb.topk(k).indices.tolist())
        js.append(len(ta & tb) / len(ta | tb))
    return sum(js) / len(js)


print(f"whole            {jac(E0, E1):.3f}")
for name, (a, b) in SL.items():
    print(f"slice {name:8s}  {jac(E0[:, a:b], E1[:, a:b]):.3f}")
for name, (a, b) in SL.items():
    keep = [i for i in range(128) if not (a <= i < b)]
    print(f"without {name:8s} {jac(E0[:, keep], E1[:, keep]):.3f}")
