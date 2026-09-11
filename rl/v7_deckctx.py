"""Phase 4g (v7 plan §2), WIRE-V7.md §5: server-side deck context.

The engine's hello carries the decklists it knows
(`"v7_decks":{"me":[[name,count],...],"opp":[...]|null}`).  Once per
game per side the server runs `deck_ctx_v1` (rl/deckctx/model.py) over
the list and keeps two things the policy consumes on every consult:

    ctx    a per-game override of e_card rows: card id -> c'_i (design L1),
           applied inside CardTable.forward BEFORE the adapter
    D      the pooled deck vector [d_c], appended to the game token
           (D_me / D_opp in v7_net.TokenBuilders)

    dc   = DeckCtx(device="cuda")                       # loads deck_ctx_v1 + card_emb_v8 once
    game = dc.game(hello["v7_decks"])                   # GameDeck(ctx_map_me, ctx_map_opp, D_me, D_opp)
    ctx, D_me, D_opp = batch_decks([game, game2, ...], device)   # per-row for a PPO window

Missing decklists (no key, null opp, or no DeckCtx configured) give
ctx=None and D=zeros: exactly what every 4a-4f gate ran with, so
`--deck-ctx none` is bit-identical to the fixtures path.
"""
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DECK_CTX_ART = os.path.join(HERE, "artifacts", "deck_ctx_v1")


class Ctx:
    """Callable for CardTable.forward(ids, ctx): one lookup table per batch row.
    maps: list (len B) of {card_id: c'_i tensor [d_c]} or None."""

    def __init__(self, maps, n_ids, device):
        self.rows = []
        for m in maps:
            if not m:
                self.rows.append(None)
                continue
            keys = torch.tensor(sorted(m.keys()), dtype=torch.long)
            vals = torch.stack([m[int(k)] for k in keys]).to(device)
            lut = torch.full((n_ids + 1,), -1, dtype=torch.long)
            lut[keys] = torch.arange(len(keys))
            self.rows.append((lut.to(device), vals))
        self.n_ids = n_ids

    def __call__(self, ids, e):
        """ids [B, ...] long (-1 unknown), e [B, ..., d_c] -> e with override rows swapped in."""
        if all(r is None for r in self.rows):
            return e
        e = e.clone()
        for b, r in enumerate(self.rows):
            if r is None:
                continue
            lut, vals = r
            idb = ids[b]
            safe = idb.clamp(0, self.n_ids)
            pos = lut[safe]
            hit = (idb >= 0) & (pos >= 0)
            if hit.any():
                e[b][hit] = vals[pos[hit]].to(e.dtype)
        return e


class GameDeck:
    __slots__ = ("map_me", "map_opp", "D_me", "D_opp")

    def __init__(self, map_me, map_opp, D_me, D_opp):
        self.map_me, self.map_opp, self.D_me, self.D_opp = map_me, map_opp, D_me, D_opp

    @property
    def ctx_map(self):
        """One override map for the game: my list and the opponent's merged (a card in both
        lists takes MY context - the policy is me)."""
        if not self.map_me and not self.map_opp:
            return None
        m = dict(self.map_opp or {})
        m.update(self.map_me or {})
        return m


class DeckCtx:
    def __init__(self, art=DECK_CTX_ART, model="model_seed0.pt", card_emb="card_emb_v8", device="cpu",
                 fingerprint=True):
        import deckctx.data as X
        from deckctx.model import DeckContext
        self.X = X
        self.names = X.load_names()
        self.n_ids = max(self.names.values()) + 1
        self.emb = torch.load(os.path.join(HERE, "artifacts", card_emb, "emb.pt")).float()
        self.device = torch.device(device)
        self.model = DeckContext(d_c=self.emb.shape[1]).to(self.device).eval()
        ck = torch.load(os.path.join(art, model), map_location="cpu", weights_only=False)
        self.model.load_state_dict(ck["model"])
        self.by_name = None
        if fingerprint:
            try:
                self.by_name = X.load_by_name()
            except Exception as exc:                        # noqa: BLE001
                print(f"note: deck context runs WITHOUT fingerprint bias ({exc})", flush=True)
        self.d_c = self.emb.shape[1]
        self.cache = {}

    @torch.no_grad()
    def side(self, decklist):
        """[(name, count), ...] -> ({card_id: c'_i [d_c] cpu}, D [d_c] cpu); (None, zeros) for an empty list."""
        if not decklist:
            return None, torch.zeros(self.d_c)
        key = tuple((str(n), int(c)) for n, c in decklist)
        if key in self.cache:
            return self.cache[key]
        E, counts, bias, mask, kept = self.X.deck_tensors([(n, c) for n, c in key], self.names, self.emb, self.by_name)
        if not kept:
            return None, torch.zeros(self.d_c)
        Eb, cb, bb, mb = self.X.collate([(E, counts, bias, mask)])
        c_prime, D = self.model(Eb.to(self.device), cb.to(self.device), bb.to(self.device), mb.to(self.device))
        c_prime, D = c_prime[0].cpu(), D[0].cpu()
        out = ({int(i): c_prime[j] for j, i in enumerate(kept)}, D)
        self.cache[key] = out
        return out

    def game(self, decks):
        """hello["v7_decks"] (or None) -> GameDeck."""
        if not decks:
            return GameDeck(None, None, torch.zeros(self.d_c), torch.zeros(self.d_c))
        m_me, D_me = self.side(decks.get("me") or [])
        m_opp, D_opp = self.side(decks.get("opp") or [])
        return GameDeck(m_me, m_opp, D_me, D_opp)


def batch_decks(games, device, n_ids=None, d_c=128):
    """Per-row GameDeck (or None) -> (ctx or None, D_me [B, d_c] or None, D_opp or None) on device."""
    if not any(g is not None for g in games):
        return None, None, None
    B = len(games)
    D_me = torch.zeros(B, d_c)
    D_opp = torch.zeros(B, d_c)
    maps = []
    for b, g in enumerate(games):
        if g is None:
            maps.append(None)
            continue
        D_me[b] = g.D_me
        D_opp[b] = g.D_opp
        maps.append(g.ctx_map)
    ctx = None
    if any(m for m in maps):
        if n_ids is None:
            n_ids = max(max(m.keys()) for m in maps if m) + 1
        ctx = Ctx(maps, n_ids, device)
    return ctx, D_me.to(device), D_opp.to(device)
