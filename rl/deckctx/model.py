"""Phase 2a (v7 plan §2): deck context L1 — the card *in this deck*.

DeckContext(e_card rows of the distinct cards in a deck, copy counts,
enabler->payoff relation bias) ->
    c'_i  [B, N, d_c]   per-card context vector (replaces e_card as the
                        card's identity for the rest of the game)
    D     [B, d_c]      pooled deck vector (joins the game token)

Design (ARCHITECTURE-V7-DESIGN.md L1): a 2-layer transformer over the
distinct cards, copy count as a feature, NO positional encoding, an
additive attention bias on enabler->payoff edges mined by
cardguru/fingerprint.py, ending in a per-card MLP.  Because nothing
depends on token order, c' is permutation-equivariant and D is
permutation-invariant by construction; tests/test_deckctx.py checks it
to 1e-6 in float64 and checks that changing a copy count moves the
outputs (2a gates).

Inputs:
    E      [B, N, d_c]  float, e_card per distinct card (zeros on padding)
    counts [B, N]       long, copies (0 on padding), clipped to COUNT_MAX
    bias   [B, N, N]    float, relation weight enabler(row)->payoff(col),
                        0 where no edge (built by deckctx/data.py)
    mask   [B, N]       bool, True on real cards
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

COUNT_MAX = 8            # copies beyond this share one embedding (singleton decks are 1s)


class BiasedAttention(nn.Module):
    """Multi-head self-attention with a per-head learned scale on an external
    additive bias: logits += a_h * bias + b_h * [bias != 0]."""

    def __init__(self, d, heads):
        super().__init__()
        self.h, self.dk = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d)
        self.out = nn.Linear(d, d)
        self.bias_scale = nn.Parameter(torch.ones(heads) * 0.5)
        self.edge_const = nn.Parameter(torch.zeros(heads))

    def forward(self, x, bias, mask):
        B, N, d = x.shape
        q, k, v = self.qkv(x).view(B, N, 3, self.h, self.dk).unbind(2)      # [B, N, h, dk]
        logits = torch.einsum("bihd,bjhd->bhij", q, k) / math.sqrt(self.dk)  # [B, h, N, N]
        sym = bias + bias.transpose(1, 2)                                    # relation is used both ways
        logits = logits + self.bias_scale.view(1, -1, 1, 1) * sym.unsqueeze(1) \
            + self.edge_const.view(1, -1, 1, 1) * (sym != 0).to(x.dtype).unsqueeze(1)
        logits = logits.masked_fill(~mask.view(B, 1, 1, N), float("-inf"))
        att = torch.softmax(logits, dim=-1)
        att = torch.nan_to_num(att)                                          # fully-masked rows
        y = torch.einsum("bhij,bjhd->bihd", att, v).reshape(B, N, d)
        return self.out(y)


class Block(nn.Module):
    def __init__(self, d, heads, ffn):
        super().__init__()
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.att = BiasedAttention(d, heads)
        self.ffn = nn.Sequential(nn.Linear(d, ffn), nn.GELU(), nn.Linear(ffn, d))

    def forward(self, x, bias, mask):
        x = x + self.att(self.n1(x), bias, mask)
        return x + self.ffn(self.n2(x))


class DeckContext(nn.Module):
    def __init__(self, d_c=128, d=128, heads=4, ffn=256, layers=2):
        super().__init__()
        self.inp = nn.Linear(d_c, d)
        self.count_emb = nn.Embedding(COUNT_MAX + 1, d)
        self.blocks = nn.ModuleList(Block(d, heads, ffn) for _ in range(layers))
        self.norm = nn.LayerNorm(d)
        self.card_mlp = nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Linear(2 * d, d_c))
        self.pool = nn.Linear(d, d_c)
        self.config = dict(d_c=d_c, d=d, heads=heads, ffn=ffn, layers=layers)

    def forward(self, E, counts, bias, mask):
        x = self.inp(E) + self.count_emb(counts.clamp(0, COUNT_MAX))
        x = x * mask.unsqueeze(-1).to(x.dtype)
        for blk in self.blocks:
            x = blk(x, bias, mask)
        h = self.norm(x)
        # residual on e_card: identity_init() makes c' == e_card exactly
        c_prime = (E + self.card_mlp(h)) * mask.unsqueeze(-1).to(h.dtype)
        m = mask.unsqueeze(-1).to(h.dtype)
        D = self.pool((h * m).sum(1) / m.sum(1).clamp(min=1.0))
        return c_prime, D

    @torch.no_grad()
    def identity_init(self):
        """2b fallback (no corpus): start as e_card pass-through, D = mean e_card.
        Requires d == d_c."""
        d = self.config["d"]
        assert d == self.config["d_c"]
        nn.init.eye_(self.inp.weight); nn.init.zeros_(self.inp.bias)
        nn.init.zeros_(self.count_emb.weight)
        for blk in self.blocks:
            nn.init.zeros_(blk.att.out.weight); nn.init.zeros_(blk.att.out.bias)
            nn.init.zeros_(blk.ffn[2].weight); nn.init.zeros_(blk.ffn[2].bias)
        nn.init.zeros_(self.card_mlp[2].weight); nn.init.zeros_(self.card_mlp[2].bias)
        nn.init.eye_(self.pool.weight); nn.init.zeros_(self.pool.bias)
        return self
