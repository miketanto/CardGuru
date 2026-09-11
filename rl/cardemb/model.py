"""Phase 1b (v7 plan §2): the card embedder `card_emb_vN`.

Three channels (rl/cardemb/data.py) -> e_card in R^{d_c}:

  text     pretrained sentence encoder (MiniLM class), FINE-TUNED, mean
           pooled -> Linear -> d_t
  graph    the 68-column ability-graph readout -> MLP -> d_g
           (v1: readout bag; v1.5 would be a GNN over the ability tree)
  printed  83 explicit floats -> Linear -> d_p (kept shallow so a linear
           probe on e_card can still read the fields)

  e_card = LayerNorm(Linear([text | graph | printed]))            (d_c = 128)

Contrastive pretraining (train_contrastive.py): InfoNCE between the text
view z_t = norm(P_t(text)) and the structure view z_s = norm(P_s(graph,
printed)), symmetric, temperature tau.  Two objectives exist:

  v1 `supcon_loss`     cards with an identical structure vector are
                       positives of each other.  FAILED gate 1d
                       (V7-VALIDATION.md): it trains Spell Snare and
                       Force Spike to coincide.
  v2 `masked_infonce`  the only positive is the same card; identical-
                       structure cards are masked out of the denominator;
                       plus `relational_distill`, which keeps the
                       fine-tuned text view's in-batch cosine matrix close
                       to the frozen pretrained encoder's, so text-only
                       distinctions survive.

Inside an RL run e_card is frozen and consumed through one trainable
Linear(d_c, d_c) adapter (design decision 1); that adapter lives in the
policy, not here.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

DEFAULT_TEXT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def mean_pool(last_hidden, attention_mask):
    m = attention_mask.unsqueeze(-1).to(last_hidden.dtype)
    return (last_hidden * m).sum(1) / m.sum(1).clamp(min=1e-6)


class TreeAttention(nn.Module):
    """Self-attention over ability nodes with a learned per-head bias per edge type
    (both directions), so Execute / SubAbility / ref:* links shape the mixing."""

    def __init__(self, d, heads, n_edge_types):
        super().__init__()
        self.h, self.dk = heads, d // heads
        self.qkv = nn.Linear(d, 3 * d)
        self.out = nn.Linear(d, d)
        self.edge_bias = nn.Embedding(n_edge_types, heads)
        nn.init.zeros_(self.edge_bias.weight)

    def forward(self, x, edges, mask):
        B, N, d = x.shape
        q, k, v = self.qkv(x).view(B, N, 3, self.h, self.dk).unbind(2)
        logits = torch.einsum("bihd,bjhd->bhij", q, k) / (self.dk ** 0.5)
        eb = self.edge_bias(edges) + self.edge_bias(edges.transpose(1, 2))      # [B, N, N, h]
        logits = logits + eb.permute(0, 3, 1, 2)
        logits = logits.masked_fill(~mask.view(B, 1, 1, N), float("-inf"))
        att = torch.nan_to_num(torch.softmax(logits, dim=-1))
        return self.out(torch.einsum("bhij,bjhd->bihd", att, v).reshape(B, N, d))


class TreeEncoder(nn.Module):
    """v5 graph channel: the ability tree (rl/cardemb/tree.py tensors) -> d_out.
    Node = kind + api + apiKind + mode + keyword embeddings + mean over
    (param key, value piece) pairs of E_key * E_val; 2 transformer layers
    with edge-type attention bias; masked mean pool."""

    def __init__(self, d=128, heads=4, layers=2, d_out=128, piece_dropout=0.0):
        super().__init__()
        from tree import KINDS, N_API_BUCKETS, N_MODE_BUCKETS, N_KW_BUCKETS, N_KEY_BUCKETS, N_VAL_BUCKETS, N_EDGE_BUCKETS
        self.piece_dropout = piece_dropout
        self.e_kind = nn.Embedding(len(KINDS), d)
        self.e_api = nn.Embedding(N_API_BUCKETS, d)
        self.e_apik = nn.Embedding(5, d)
        self.e_mode = nn.Embedding(N_MODE_BUCKETS, d)
        self.e_kw = nn.Embedding(N_KW_BUCKETS, d)
        self.e_key = nn.Embedding(N_KEY_BUCKETS, d, padding_idx=0)
        self.e_val = nn.Embedding(N_VAL_BUCKETS, d, padding_idx=0)
        self.blocks = nn.ModuleList()
        for _ in range(layers):
            self.blocks.append(nn.ModuleDict({
                "n1": nn.LayerNorm(d), "att": TreeAttention(d, heads, N_EDGE_BUCKETS),
                "n2": nn.LayerNorm(d), "ffn": nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Linear(2 * d, d))}))
        self.norm = nn.LayerNorm(d)
        self.out = nn.Linear(d, d_out)

    def forward(self, t):
        pairs = t["pairs"]                                                       # [B, N, P, 2]
        pk, pv = self.e_key(pairs[..., 0]), self.e_val(pairs[..., 1])            # [B, N, P, d]
        valid = (pairs[..., 0] > 0)
        if self.training and self.piece_dropout > 0:                             # v6: against lookup behaviour
            valid = valid & (torch.rand_like(valid, dtype=torch.float32) >= self.piece_dropout)
        valid = valid.to(pk.dtype).unsqueeze(-1)
        pfeat = (pk * pv * valid).sum(2) / valid.sum(2).clamp(min=1.0)
        x = (self.e_kind(t["kind"]) + self.e_api(t["api"]) + self.e_apik(t["api_kind"])
             + self.e_mode(t["mode"]) + self.e_kw(t["kw"]) + pfeat)
        mask = t["mask"]
        x = x * mask.unsqueeze(-1).to(x.dtype)
        for blk in self.blocks:
            x = x + blk["att"](blk["n1"](x), t["edges"], mask)
            x = x + blk["ffn"](blk["n2"](x))
        h = self.norm(x)
        m = mask.unsqueeze(-1).to(h.dtype)
        return self.out((h * m).sum(1) / m.sum(1).clamp(min=1.0))


class CardEmbedder(nn.Module):
    # v6 block widths of e_card (sum = d_c = 128): a stated blend, not an accident of norms
    BLOCKS = {"text": 48, "tree": 32, "bag": 16, "printed": 32}

    def __init__(self, text_model=DEFAULT_TEXT_MODEL, graph_dim=68, printed_dim=83,
                 d_t=128, d_g=128, d_p=32, d_c=128, d_z=128, tau=0.05, tree=False, d_tree=128,
                 fuse="linear", piece_dropout=0.0):
        super().__init__()
        from transformers import AutoModel, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(text_model)
        self.text = AutoModel.from_pretrained(text_model)
        h = self.text.config.hidden_size
        self.text_proj = nn.Linear(h, d_t)
        self.graph_mlp = nn.Sequential(nn.Linear(graph_dim, 256), nn.GELU(),
                                       nn.Linear(256, d_g), nn.GELU())
        self.printed_proj = nn.Linear(printed_dim, d_p)
        self.tree_enc = TreeEncoder(d_out=d_tree, piece_dropout=piece_dropout) if tree else None
        d_struct = d_g + d_p + (d_tree if tree else 0)
        self.fuse_mode = fuse
        if fuse == "blocks":
            # v6: e_card = [LN(W_t ht) | LN(W_tree tree) | LN(W_bag bag) | LN(W_p printed)]
            assert tree, "fuse='blocks' needs the tree channel"
            B = self.BLOCKS
            assert sum(B.values()) == d_c
            self.b_text = nn.Sequential(nn.Linear(d_t, B["text"]), nn.LayerNorm(B["text"]))
            self.b_tree = nn.Sequential(nn.Linear(d_tree, B["tree"]), nn.LayerNorm(B["tree"]))
            self.b_bag = nn.Sequential(nn.Linear(d_g, B["bag"]), nn.LayerNorm(B["bag"]))
            self.b_printed = nn.Sequential(nn.Linear(d_p, B["printed"]), nn.LayerNorm(B["printed"]))
            # reconstruction heads (train-time only): the tree slice must compute the
            # 68-column readout, the printed slice must reproduce the printed fields
            self.rec_readout = nn.Linear(B["tree"], graph_dim)
            self.rec_printed = nn.Linear(B["printed"], printed_dim)
        else:
            self.fuse = nn.Linear(d_t + d_struct, d_c)
            self.norm = nn.LayerNorm(d_c)
        # contrastive views
        self.z_text = nn.Sequential(nn.Linear(d_t, d_z), nn.GELU(), nn.Linear(d_z, d_z))
        self.z_struct = nn.Sequential(nn.Linear(d_struct, d_z), nn.GELU(), nn.Linear(d_z, d_z))
        self.tau = tau
        self.config = dict(text_model=text_model, graph_dim=graph_dim, printed_dim=printed_dim,
                           d_t=d_t, d_g=d_g, d_p=d_p, d_c=d_c, d_z=d_z, tau=tau, tree=tree, d_tree=d_tree,
                           fuse=fuse, piece_dropout=piece_dropout)

    # --- channels
    def encode_text(self, texts, max_len=128):
        dev = next(self.parameters()).device
        tok = self.tokenizer(texts, padding=True, truncation=True, max_length=max_len,
                             return_tensors="pt").to(dev)
        out = self.text(**tok).last_hidden_state
        return self.text_proj(mean_pool(out, tok["attention_mask"]))

    def encode_struct(self, graph, printed, trees=None):
        parts = [self.graph_mlp(graph), self.printed_proj(printed)]
        if self.tree_enc is not None:
            assert trees is not None, "tree=True needs collated tree tensors"
            parts.append(self.tree_enc(trees))
        return torch.cat(parts, -1)

    def fuse_blocks(self, ht, hs):
        """v6 fused vector and its reconstruction targets' predictions."""
        d_g, d_p = self.config["d_g"], self.config["d_p"]
        hg, hp, htree = hs[:, :d_g], hs[:, d_g:d_g + d_p], hs[:, d_g + d_p:]
        bt, btree, bbag, bp = self.b_text(ht), self.b_tree(htree), self.b_bag(hg), self.b_printed(hp)
        e = torch.cat([bt, btree, bbag, bp], -1)
        return e, self.rec_readout(btree), self.rec_printed(bp)

    def forward(self, texts, graph, printed, trees=None):
        """Returns (e_card, z_text, z_struct, h_text).  With fuse='blocks' the
        reconstruction predictions are stored on self.last_rec = (readout_hat, printed_hat)."""
        ht = self.encode_text(texts)
        hs = self.encode_struct(graph, printed, trees)
        if self.fuse_mode == "blocks":
            e, r_hat, p_hat = self.fuse_blocks(ht, hs)
            self.last_rec = (r_hat, p_hat)
        else:
            e = self.norm(self.fuse(torch.cat([ht, hs], -1)))
            self.last_rec = None
        zt = F.normalize(self.z_text(ht), dim=-1)
        zs = F.normalize(self.z_struct(hs), dim=-1)
        return e, zt, zs, ht

    @torch.no_grad()
    def pooled_pretrained(self, texts, max_len=128):
        """Mean-pooled hidden states of the text encoder as it is NOW; called
        before any training step it is the frozen pretrained anchor."""
        dev = next(self.parameters()).device
        tok = self.tokenizer(texts, padding=True, truncation=True, max_length=max_len,
                             return_tensors="pt").to(dev)
        return mean_pool(self.text(**tok).last_hidden_state, tok["attention_mask"])

    @torch.no_grad()
    def embed(self, texts, graph, printed, trees=None):
        return self.forward(texts, graph, printed, trees)[0]


def supcon_loss(zt, zs, keys, tau):
    """Symmetric InfoNCE where every pair with equal `keys` is a positive.
    keys: LongTensor [B] (an id per distinct structure vector)."""
    logits = zt @ zs.t() / tau                                   # [B, B]
    pos = (keys.unsqueeze(0) == keys.unsqueeze(1)).float()       # [B, B], diag included
    def one_side(lg):
        log_prob = lg - torch.logsumexp(lg, dim=1, keepdim=True)
        return -((log_prob * pos).sum(1) / pos.sum(1)).mean()
    return 0.5 * (one_side(logits) + one_side(logits.t()))


def masked_infonce(zt, zs, keys, tau):
    """v2 objective: the only positive of text i is structure i; other cards
    with an identical structure vector are removed from the denominator
    (neither positive nor negative), so text-only distinctions between
    structurally identical cards (Spell Snare / Force Spike) are never
    trained away.  Symmetric."""
    logits = zt @ zs.t() / tau
    same = keys.unsqueeze(0) == keys.unsqueeze(1)
    eye = torch.eye(len(keys), dtype=torch.bool, device=keys.device)
    logits = logits.masked_fill(same & ~eye, float("-inf"))
    tgt = torch.arange(len(keys), device=keys.device)
    return 0.5 * (F.cross_entropy(logits, tgt) + F.cross_entropy(logits.t(), tgt))


def relational_distill(ht, anchor):
    """Keep the fine-tuned text view's similarity structure close to the frozen
    pretrained encoder's: MSE between the two in-batch cosine matrices.
    ht: [B, d_t] fine-tuned text features; anchor: [B, d_a] frozen pooled
    embeddings of the same cards (normalised or not)."""
    a = F.normalize(ht, dim=-1)
    b = F.normalize(anchor, dim=-1)
    return F.mse_loss(a @ a.t(), b @ b.t())


@torch.no_grad()
def retrieval_at_k(zt, zs, keys, k=1):
    """Fraction of text views whose top-k structure neighbours contain a positive."""
    sims = zt @ zs.t()
    top = sims.topk(k, dim=1).indices
    hit = (keys[top] == keys.unsqueeze(1)).any(1).float()
    return hit.mean().item()
