"""Phase 2a gates (v7 plan §2): DeckContext is permutation-equivariant /
invariant to 1e-6 (checked in float64 so the gate measures the model,
not float32 summation order), copy-count sensitive, and identity-
initialisable (c' == e_card exactly, the 2b no-corpus fallback)."""
import os
import sys

import pytest

torch = pytest.importorskip("torch")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rl", "deckctx"))
from model import DeckContext   # noqa: E402


def _inputs(B=2, N=23, d=128, seed=0, dtype=torch.float64):
    g = torch.Generator().manual_seed(seed)
    E = torch.randn(B, N, d, generator=g, dtype=dtype)
    counts = torch.randint(1, 5, (B, N), generator=g)
    bias = (torch.rand(B, N, N, generator=g, dtype=dtype) < 0.1).to(dtype) * torch.randint(1, 5, (B, N, N), generator=g).to(dtype)
    bias.diagonal(dim1=1, dim2=2).zero_()
    mask = torch.ones(B, N, dtype=torch.bool)
    mask[1, N - 3:] = False                       # a shorter second deck
    E[1, N - 3:] = 0; counts[1, N - 3:] = 0; bias[1, N - 3:, :] = 0; bias[1, :, N - 3:] = 0
    return E, counts, bias, mask


def test_permutation_equivariance_and_invariance():
    torch.manual_seed(0)
    m = DeckContext().double().eval()
    E, counts, bias, mask = _inputs()
    c1, D1 = m(E, counts, bias, mask)
    perm = torch.randperm(E.shape[1], generator=torch.Generator().manual_seed(1))
    c2, D2 = m(E[:, perm], counts[:, perm], bias[:, perm][:, :, perm], mask[:, perm])
    assert (c2 - c1[:, perm]).abs().max().item() <= 1e-6
    assert (D2 - D1).abs().max().item() <= 1e-6


def test_copy_count_sensitivity():
    torch.manual_seed(0)
    m = DeckContext().double().eval()
    E, counts, bias, mask = _inputs()
    c1, D1 = m(E, counts, bias, mask)
    counts2 = counts.clone()
    counts2[0, 3] = 1 if counts2[0, 3] != 1 else 4
    c2, D2 = m(E, counts2, bias, mask)
    assert (c2[0, 3] - c1[0, 3]).norm().item() > 0
    assert (D2[0] - D1[0]).norm().item() > 0
    assert (c2[1] - c1[1]).abs().max().item() == 0     # the other deck is untouched


def test_relation_bias_matters():
    torch.manual_seed(0)
    m = DeckContext().double().eval()
    E, counts, bias, mask = _inputs()
    c1, _ = m(E, counts, bias, mask)
    c2, _ = m(E, counts, torch.zeros_like(bias), mask)
    assert (c2 - c1).abs().max().item() > 0


def test_identity_init_is_passthrough():
    m = DeckContext().double().eval().identity_init()
    E, counts, bias, mask = _inputs()
    c, D = m(E, counts, bias, mask)
    assert (c - E * mask.unsqueeze(-1).double()).abs().max().item() == 0
    assert torch.isfinite(D).all()
