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


class CardEmbedder(nn.Module):
    def __init__(self, text_model=DEFAULT_TEXT_MODEL, graph_dim=68, printed_dim=83,
                 d_t=128, d_g=128, d_p=32, d_c=128, d_z=128, tau=0.05):
        super().__init__()
        from transformers import AutoModel, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(text_model)
        self.text = AutoModel.from_pretrained(text_model)
        h = self.text.config.hidden_size
        self.text_proj = nn.Linear(h, d_t)
        self.graph_mlp = nn.Sequential(nn.Linear(graph_dim, 256), nn.GELU(),
                                       nn.Linear(256, d_g), nn.GELU())
        self.printed_proj = nn.Linear(printed_dim, d_p)
        self.fuse = nn.Linear(d_t + d_g + d_p, d_c)
        self.norm = nn.LayerNorm(d_c)
        # contrastive views
        self.z_text = nn.Sequential(nn.Linear(d_t, d_z), nn.GELU(), nn.Linear(d_z, d_z))
        self.z_struct = nn.Sequential(nn.Linear(d_g + d_p, d_z), nn.GELU(), nn.Linear(d_z, d_z))
        self.tau = tau
        self.config = dict(text_model=text_model, graph_dim=graph_dim, printed_dim=printed_dim,
                           d_t=d_t, d_g=d_g, d_p=d_p, d_c=d_c, d_z=d_z, tau=tau)

    # --- channels
    def encode_text(self, texts, max_len=128):
        dev = next(self.parameters()).device
        tok = self.tokenizer(texts, padding=True, truncation=True, max_length=max_len,
                             return_tensors="pt").to(dev)
        out = self.text(**tok).last_hidden_state
        return self.text_proj(mean_pool(out, tok["attention_mask"]))

    def encode_struct(self, graph, printed):
        return self.graph_mlp(graph), self.printed_proj(printed)

    def forward(self, texts, graph, printed):
        """Returns (e_card, z_text, z_struct, h_text)."""
        ht = self.encode_text(texts)
        hg, hp = self.encode_struct(graph, printed)
        e = self.norm(self.fuse(torch.cat([ht, hg, hp], -1)))
        zt = F.normalize(self.z_text(ht), dim=-1)
        zs = F.normalize(self.z_struct(torch.cat([hg, hp], -1)), dim=-1)
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
    def embed(self, texts, graph, printed):
        return self.forward(texts, graph, printed)[0]


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
