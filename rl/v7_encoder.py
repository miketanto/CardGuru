"""Phase 4c (v7 plan §2): the state-graph encoder (design L4).

One pre-LN transformer over EVERY token the builders produce, in one
sequence:

    [ game | me | opp | ent_1..ent_N | cand_1..cand_K | opp_hand.. | opp_deck.. | opp_act.. ]

with an additive, per-head, per-edge-type attention bias from the typed
edge matrix (WIRE-V7 §2e types 0..7, plus `refers_to` = 8 from a
candidate or an opponent-action token to the entities it acts on, and its
reverse `referred_by` = 9), and a stack-depth embedding added to stack
tokens (from entity field 9).  d = 256, 8 heads, 6 layers, FFN 1024.
No pooling anywhere: the output is the same sequence, re-encoded; the
heads (4d) read the candidate tokens and the game token from it.

Exactness properties, each a test in tests/test_v7_encoder.py:
  - the no-edge row of the bias table is a fixed zero (not a parameter),
    so with every edge zero the encoder IS plain attention, bit for bit
    (the v6 R0 precedent);
  - padding is masked out of every softmax and zeroed on output, so
    adding padding tokens never changes a real token;
  - no positional encoding: permuting entities (and candidates) permutes
    the outputs and nothing else;
  - the attention output projection and the FFN output layer are
    zero-initialised, so an untrained encoder is the identity on the
    builder tokens and the faithfulness probe after L4 holds at init by
    construction (as after L3); it must be rerun on the trained net.
"""
import math
import os
import sys

import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wire_validate as W                                   # noqa: E402

R_REFERS = W.RTYPES          # 8: candidate / opp-action -> entity
R_REFERRED = W.RTYPES + 1    # 9: reverse
N_EDGE = W.RTYPES + 3        # 0 = none, 1..8 = wire types 0..7 (+1), 9 = refers_to, 10 = referred_by
STACK_BUCKETS = 6


class EdgeAttention(nn.Module):
    def __init__(self, d, heads, n_edge=N_EDGE):
        super().__init__()
        self.h, self.dk = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d)
        self.out = nn.Linear(d, d)
        # row 0 (no edge) is a fixed zero buffer; rows 1.. are parameters
        self.bias_rows = nn.Parameter(torch.zeros(n_edge - 1, heads))
        self.register_buffer("zero_row", torch.zeros(1, heads))
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x, edges, mask):
        B, T, d = x.shape
        q, k, v = self.qkv(x).view(B, T, 3, self.h, self.dk).unbind(2)
        logits = torch.einsum("bihd,bjhd->bhij", q, k) / math.sqrt(self.dk)
        table = torch.cat([self.zero_row, self.bias_rows], 0)                  # [n_edge, h]
        if edges is not None:
            # one-hot matmul, NOT table[edges]: the gather's backward is
            # index_put(accumulate) over B*T*T indices per layer, a
            # sort-and-segment kernel that was 85% of the update's GPU time
            # (V7-VALIDATION §4g profile). The matmul picks exactly one row
            # per pair (0*x terms are exact), so the numbers are identical.
            onehot = torch.nn.functional.one_hot(edges, table.shape[0]).to(table.dtype)
            logits = logits + (onehot @ table).permute(0, 3, 1, 2)             # [B, h, T, T]
        logits = logits.masked_fill(~mask.view(B, 1, 1, T), float("-inf"))
        att = torch.softmax(logits, dim=-1)
        att = torch.nan_to_num(att)
        return self.out(torch.einsum("bhij,bjhd->bihd", att, v).reshape(B, T, d))


class Block(nn.Module):
    def __init__(self, d, heads, ffn):
        super().__init__()
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.att = EdgeAttention(d, heads)
        self.ffn = nn.Sequential(nn.Linear(d, ffn), nn.GELU(), nn.Linear(ffn, d))
        nn.init.zeros_(self.ffn[-1].weight)
        nn.init.zeros_(self.ffn[-1].bias)

    def forward(self, x, edges, mask):
        x = x + self.att(self.n1(x), edges, mask)
        return x + self.ffn(self.n2(x))


class StateGraphEncoder(nn.Module):
    def __init__(self, d=256, heads=8, layers=6, ffn=1024, use_edges=True):
        super().__init__()
        self.blocks = nn.ModuleList(Block(d, heads, ffn) for _ in range(layers))
        self.stack_emb = nn.Embedding(STACK_BUCKETS, d)
        nn.init.zeros_(self.stack_emb.weight)
        self.use_edges = use_edges
        self.config = dict(d=d, heads=heads, layers=layers, ffn=ffn, use_edges=use_edges)

    @staticmethod
    def assemble(toks, ent_raw=None):
        """Builder outputs -> (seq [B, T, d], mask [B, T], edges [B, T, T] long, layout dict)."""
        parts = [("game", toks["game"], None), ("players", toks["players"], None),
                 ("ent", toks["ent"], toks["ent_mask"]), ("cand", toks["cand"], toks["cand_mask"]),
                 ("opp_hand", toks["opp_hand"], toks["opp_hand_mask"]),
                 ("opp_deck", toks["opp_deck"], toks["opp_deck_mask"]),
                 ("opp_act", toks["opp_act"], toks["opp_act_mask"])]
        B = toks["game"].shape[0]
        dev = toks["game"].device
        seqs, masks, layout, off = [], [], {}, 0
        for name, t, m in parts:
            n = t.shape[1]
            layout[name] = (off, off + n)
            seqs.append(t)
            masks.append(m if m is not None else torch.ones(B, n, dtype=torch.bool, device=dev))
            off += n
        seq, mask = torch.cat(seqs, 1), torch.cat(masks, 1)
        T = off
        edges = torch.zeros(B, T, T, dtype=torch.long, device=dev)
        t0, t1 = 0, layout["ent"][1]                                     # game, players, ents = wire token space
        edges[:, t0:t1, t0:t1] = toks["edges"]                            # already type+1, 0 = none
        c0, c1 = layout["cand"]
        ref = toks["refers"].to(torch.long)                                # [B, K, T_wire] multi-hot
        edges[:, c0:c1, t0:t1] = torch.where(ref > 0, torch.full_like(ref, R_REFERS + 1), torch.zeros_like(ref))
        edges[:, t0:t1, c0:c1] = torch.where(ref.transpose(1, 2) > 0, torch.full_like(ref.transpose(1, 2), R_REFERRED + 1),
                                             torch.zeros_like(ref.transpose(1, 2)))
        a0, a1 = layout["opp_act"]
        aref = toks["opp_act_refers"].to(torch.long)
        edges[:, a0:a1, t0:t1] = torch.where(aref > 0, torch.full_like(aref, R_REFERS + 1), torch.zeros_like(aref))
        edges[:, t0:t1, a0:a1] = torch.where(aref.transpose(1, 2) > 0, torch.full_like(aref.transpose(1, 2), R_REFERRED + 1),
                                             torch.zeros_like(aref.transpose(1, 2)))
        return seq, mask, edges, layout

    def forward(self, toks, ent_raw=None):
        seq, mask, edges, layout = self.assemble(toks)
        if ent_raw is not None:                                            # stack-depth embedding on stack tokens
            e0, e1 = layout["ent"]
            is_stack = ent_raw[..., 2] > 0.5                               # zone one-hot index 2 = stack
            depth = (ent_raw[..., 9] * 4).round().long().clamp(0, STACK_BUCKETS - 2) + 1
            depth = torch.where(is_stack, depth, torch.zeros_like(depth))
            seq = seq.clone()
            seq[:, e0:e1] = seq[:, e0:e1] + self.stack_emb(depth)
        x = seq
        e = edges if self.use_edges else None
        for blk in self.blocks:
            x = blk(x, e, mask)
        x = x * mask.unsqueeze(-1).to(x.dtype)
        return {name: x[:, a:b] for name, (a, b) in layout.items()} | {"seq": x, "mask": mask, "layout": layout}
