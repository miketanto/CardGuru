"""Phase 4f (v7 plan §2): the belief module (design §8a) — a SEPARATE module
whose outputs are features the policy consumes and whose loss never reaches
a policy parameter.

    belief = BeliefModule(d)
    feats  = belief(toks)                       # reads legal tokens only, through stop-gradient
    toks2  = belief.attach(toks, feats)         # features appended to opp hand-slot and remaining-deck tokens
    loss   = belief.loss(feats, labels)         # its own optimiser; labels from -Drl.oracle self-play

Inputs (all legal information): the opponent remaining-deck tokens (their
deck context), the opponent hand-slot tokens, the opponent-action tokens,
the game token.  2-layer transformer, d 256.

Outputs: per hand slot, a pointer distribution over the remaining-deck
tokens (slot x card); per remaining card, P(in their hand) and P(next
draw).  They are attached as features: each hand-slot token gets its
expected remaining-deck token (the pointer-weighted average) and its
entropy; each remaining-deck token gets its two probabilities.

`off=True` masks every feature to zero and the attach is the identity on
the tokens' original dims, so the downstream net is bit-identical to
the 4e net (tests/test_v7_belief.py).  The gradient into the shared
builders is cut with `.detach()` on every input (stop-gradient).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class BeliefModule(nn.Module):
    N_FEAT_HAND = 2     # entropy, log(1 + n_remaining)
    N_FEAT_DECK = 2     # P(in hand), P(next draw)

    def __init__(self, d=256, heads=8, layers=2, off=False):
        super().__init__()
        self.off = off
        layer = nn.TransformerEncoderLayer(d, heads, 4 * d, dropout=0.0, batch_first=True, norm_first=True, activation="gelu")
        self.enc = nn.TransformerEncoder(layer, layers)
        self.group_emb = nn.Embedding(4, d)                      # game, hand slot, remaining card, action
        self.q = nn.Linear(d, d)                                 # hand slot query
        self.k = nn.Linear(d, d)                                 # remaining-card key
        self.p_hand = nn.Linear(d, 1)
        self.p_draw = nn.Linear(d, 1)
        self.hand_feat = nn.Linear(d + self.N_FEAT_HAND, d)       # expected card + scalars -> feature vector
        self.deck_feat = nn.Linear(self.N_FEAT_DECK, d)
        nn.init.zeros_(self.hand_feat.weight); nn.init.zeros_(self.hand_feat.bias)
        nn.init.zeros_(self.deck_feat.weight); nn.init.zeros_(self.deck_feat.bias)
        self.d = d

    def forward(self, toks):
        """toks: builder outputs (dict).  Returns a dict of belief outputs; all inputs detached."""
        g = toks["game"].detach()                                 # [B, 1, d]
        oh, od, oa = toks["opp_hand"].detach(), toks["opp_deck"].detach(), toks["opp_act"].detach()
        mh, md, ma = toks["opp_hand_mask"], toks["opp_deck_mask"], toks["opp_act_mask"]
        B = g.shape[0]
        dev = g.device
        x = torch.cat([g + self.group_emb.weight[0], oh + self.group_emb.weight[1],
                       od + self.group_emb.weight[2], oa + self.group_emb.weight[3]], 1)
        mask = torch.cat([torch.ones(B, 1, dtype=torch.bool, device=dev), mh, md, ma], 1)
        safe = mask.clone(); safe[:, 0] = True
        h = self.enc(x, src_key_padding_mask=~safe)
        H, D = oh.shape[1], od.shape[1]
        h_hand = h[:, 1:1 + H]
        h_deck = h[:, 1 + H:1 + H + D]
        logits = torch.einsum("bhd,bkd->bhk", self.q(h_hand), self.k(h_deck)) / (self.d ** 0.5)
        logits = logits.masked_fill(~md.unsqueeze(1), float("-inf"))
        pointer = torch.softmax(logits, -1)                         # [B, H, D]
        pointer = torch.nan_to_num(pointer)                          # rows with no deck tokens
        p_hand = torch.sigmoid(self.p_hand(h_deck)).squeeze(-1) * md.to(h.dtype)
        p_draw = torch.softmax(self.p_draw(h_deck).squeeze(-1).masked_fill(~md, float("-inf")), -1)
        p_draw = torch.nan_to_num(p_draw)
        return {"pointer": pointer, "p_hand": p_hand, "p_draw": p_draw, "h_hand": h_hand, "h_deck": h_deck}

    def attach(self, toks, out):
        """Features onto the opponent tokens.  off=True -> tokens returned unchanged (bit-identical)."""
        if self.off:
            return toks
        toks = dict(toks)
        od = toks["opp_deck"]                                        # [B, D, d]
        expected = torch.einsum("bhk,bkd->bhd", out["pointer"], od.detach())
        ent = -(out["pointer"] * (out["pointer"] + 1e-9).log()).sum(-1, keepdim=True)
        n_rem = toks["opp_deck_mask"].sum(1, keepdim=True).to(od.dtype).unsqueeze(-1).expand(-1, expected.shape[1], 1)
        hand_f = self.hand_feat(torch.cat([expected, ent, torch.log1p(n_rem)], -1))
        deck_f = self.deck_feat(torch.stack([out["p_hand"], out["p_draw"]], -1))
        toks["opp_hand"] = toks["opp_hand"] + hand_f * toks["opp_hand_mask"].unsqueeze(-1).to(od.dtype)
        toks["opp_deck"] = toks["opp_deck"] + deck_f * toks["opp_deck_mask"].unsqueeze(-1).to(od.dtype)
        return toks

    def loss(self, out, slot_target, hand_target, draw_target, hand_mask, deck_mask):
        """slot_target [B, H] long: index of the remaining-deck token that is the true card in that
        slot (-1 = unknown / not among remaining); hand_target [B, D] float: card is in their hand;
        draw_target [B] long: index of their next draw (-1 unknown)."""
        B, H, D = out["pointer"].shape
        lp = (out["pointer"] + 1e-9).log().view(B * H, D)
        st = slot_target.view(-1)
        ok = (st >= 0) & hand_mask.view(-1)
        l_slot = -(lp[ok, st[ok]]).mean() if ok.any() else lp.sum() * 0
        bce = F.binary_cross_entropy(out["p_hand"].clamp(1e-6, 1 - 1e-6), hand_target.to(out["p_hand"].dtype), reduction="none")
        l_hand = (bce * deck_mask.to(bce.dtype)).sum() / deck_mask.sum().clamp(min=1)
        okd = draw_target >= 0
        l_draw = -((out["p_draw"] + 1e-9).log()[okd, draw_target[okd]]).mean() if okd.any() else l_hand * 0
        return l_slot + l_hand + l_draw

    @staticmethod
    def baseline_loglik(deck_mask, slot_target, hand_mask):
        """Uniform-over-remaining log-likelihood of the true slots (the probe's baseline)."""
        n = deck_mask.sum(1).to(torch.float64).clamp(min=1)
        ok = (slot_target >= 0) & hand_mask
        per_row = -(n.log().unsqueeze(1).expand_as(slot_target.to(torch.float64)))
        return per_row[ok].mean() if ok.any() else torch.tensor(0.0)
