"""Phase 4d (v7 plan §2): the v7 heads (design L6) and memory (design L5).

    heads = V7Heads()
    logits, h_next = heads(enc_out, state)        # enc_out from StateGraphEncoder, state = (h, c) LSTM or None

Policy logits over candidates: a pointer score per candidate token
(MLP on the encoded candidate token) plus a bilinear term between the
encoded game token (after the LSTM) and the candidate token, masked
softmax over the real candidates.  No pooling: every candidate token
reaches the scorer.

Memory: an LSTM on the encoded game token, one step per consult
(decision 5: LSTM on the game token; history tokens later).  The LSTM
output is what the bilinear term reads and what the value trunk's game
token will read too, so the policy's memory is one bounded, inspectable
vector.

Gates (tests/test_v7_heads.py): logits are invariant to padding
(appending padding candidates or entities changes no real logit); a
linear probe reads the candidate count off the game token; the LSTM
state carries information across consults (a planted bit at consult t
is recoverable from the game vector at t+1).
"""
import torch
import torch.nn as nn


class V7Heads(nn.Module):
    def __init__(self, d=256, d_mem=256, hidden=256):
        super().__init__()
        self.lstm = nn.LSTMCell(d, d_mem)
        self.logit_bound = 0.0          # > 0: logits = B * tanh(logits / B) (7a arm A2); 0 = unbounded (default, identity)
        self.game_out = nn.Linear(d_mem, d)                     # memory path, residual on the game token
        nn.init.zeros_(self.game_out.weight)                    # at init game_vec == g exactly (information-preserving)
        nn.init.zeros_(self.game_out.bias)
        self.pointer = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, hidden), nn.GELU(), nn.Linear(hidden, 1))
        self.bilinear = nn.Bilinear(d, d, 1)
        self.d, self.d_mem = d, d_mem

    def init_state(self, B, device):
        dt = self.lstm.weight_hh.dtype
        return (torch.zeros(B, self.d_mem, device=device, dtype=dt), torch.zeros(B, self.d_mem, device=device, dtype=dt))

    def forward(self, enc, state=None):
        """enc: dict from StateGraphEncoder (game [B,1,d], cand [B,K,d], cand_mask via mask/layout).
        Returns (logits [B, K] with -inf on padding, game_vec [B, d], new_state)."""
        g = enc["game"][:, 0]                                        # [B, d]
        B = g.shape[0]
        if state is None:
            state = self.init_state(B, g.device)
        h, c = self.lstm(g, state)
        game_vec = g + self.game_out(h)                               # [B, d]
        cand = enc["cand"]                                            # [B, K, d]
        K = cand.shape[1]
        c0, c1 = enc["layout"]["cand"]
        cmask = enc["mask"][:, c0:c1]                                 # [B, K]
        ptr = self.pointer(cand).squeeze(-1)                          # [B, K]
        bil = self.bilinear(game_vec.unsqueeze(1).expand(B, K, self.d).reshape(B * K, self.d),
                            cand.reshape(B * K, self.d)).view(B, K)
        logits = ptr + bil
        if self.logit_bound:
            logits = self.logit_bound * torch.tanh(logits / self.logit_bound)
        logits = logits.masked_fill(~cmask, float("-inf"))
        return logits, game_vec, (h, c)

    @staticmethod
    def log_probs(logits):
        return torch.log_softmax(logits, dim=-1)
