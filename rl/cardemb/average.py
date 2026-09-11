"""Seed-averaged artifact (CARDEMB-RESEARCH.md §2a: Antoniak & Mimno 2018,
Wendlandt et al. 2018 — average over runs; Moschella et al. 2023 — spaces
differ by a quasi-isometry).

For a block-structured e_card, each slice of every extra seed is aligned
to seed 0's slice by orthogonal Procrustes (the rotation/reflection that
best maps one onto the other, fitted on all rows), the aligned slices
are averaged, and each row's slice is re-standardised (zero mean, unit
variance across its dimensions) so the width-weighted cosine blend of
the block design is preserved.

Run:  python3 rl/cardemb/average.py OUT.pt IN0.pt IN1.pt [IN2.pt ...]
"""
import sys

import torch

SLICES = [(0, 48), (48, 80), (80, 96), (96, 128)]


def procrustes(A, B):
    """Orthogonal R minimising ||B R - A||_F  (maps B's frame onto A's)."""
    U, _, Vt = torch.linalg.svd(B.t() @ A, full_matrices=False)
    return U @ Vt


def standardise(X):
    return (X - X.mean(dim=1, keepdim=True)) / X.std(dim=1, keepdim=True, unbiased=False).clamp(min=1e-6)


def average(paths, slices=SLICES):
    embs = [torch.load(p).float() for p in paths]
    ref = embs[0]
    out = torch.zeros_like(ref)
    for a, b in slices:
        acc = ref[:, a:b].clone()
        for E in embs[1:]:
            R = procrustes(ref[:, a:b], E[:, a:b])
            acc += E[:, a:b] @ R
        out[:, a:b] = standardise(acc / len(embs))
    return out


if __name__ == "__main__":
    out_path, ins = sys.argv[1], sys.argv[2:]
    E = average(ins)
    torch.save(E, out_path)
    print(f"averaged {len(ins)} seeds -> {out_path} {tuple(E.shape)}")
