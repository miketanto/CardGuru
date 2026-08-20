"""E0 policy server: PPO over a candidate-scoring MLP, IPC V1 (TCP, NDJSON).

One connection = one driver invocation. The hello message declares the
connection mode:
  train : sample from the policy, collect trajectories, PPO-update every
          UPDATE_EPISODES completed episodes
  eval  : argmax actions, no trajectory collection, no updates
  random: uniform-random replies (throughput probe for milestone 3)

Model (E0, the ablation control): state MLP 24->128->128; candidate MLP
38->64; logit = MLP([state_emb || cand_emb]) per candidate, softmax over
the variable-length candidate set (padded+masked); value head off the
state embedding. Per-action log-prob normalization (Phase 2 B7: <=6
callbacks per action, no hierarchical decoder needed).

PPO: terminal-only reward (+1/-1/0), discounting PER CONSULT (gamma
0.997), GAE lambda 0.95, clip 0.2, 4 epochs, entropy 0.01. All standard,
deliberately non-novel.

Encoder v6 (--arch entattn, ENCODER-V6-BUILD.md) replaces the flat state
vector with one token per card plus a typed relation edge list:
  -> {"t":"consult","g":[...],"e":[[...],...],"r":[[s,d,t],...],"c":[...]}
and the hello advertises gdim/edim/emax/rtypes, which the server checks
and refuses to guess at. Everything from the state token onward -
candidates, scorer, value head - is the v5 path unchanged.

Run: python3 rl/policy_server.py --port 7777 --ckpt /tmp/rl_e0.pt \
        [--seed 0] [--log /tmp/rl_train.csv]
     python3 rl/policy_server.py --port 7777 --arch entattn --cdim 94 \
        --ckpt /tmp/rl_v6.pt [--r0]        # v6, and its ablation arm

Checked by: python3 rl/entattn_check.py
"""
import argparse
import json
import os
import socket
import threading
import time

import torch
import torch.nn as nn

SDIM, CDIM = 24, 38          # defaults; --sdim/--cdim override (E2 uses a wider cdim)
GAMMA, LAM, CLIP, LR = 0.997, 0.95, 0.2, 3e-4
EPOCHS, ENT_COEF, VAL_COEF = 4, 0.01, 0.5
UPDATE_EPISODES = 32
MAX_K = 40                   # candidate buffer; --max-k overrides
# MAX_K is a BUFFER SIZE, not an architectural constant: every parameter
# is shaped by sdim/cdim/d and padded candidates are masked out, so
# raising it changes no weights and no checkpoint compatibility. It only
# costs compute (cand_net runs over MAX_K rows per consult), which is why
# it stays at 40 by default and is raised only for the joint-assignment
# encoder, whose action space is whole assignments rather than cards.

# ---- encoder v6 (entity tokens + relations), ENCODER-V6-BUILD.md §1-§3 ----
GDIM, EDIM = 16, 48             # --gdim/--edim override
# EMAX was 24 in the build plan, which was a guess made before
# anything had been emitted. MEASURED on 40 rung-0 games: 458 of
# 1944 consults (23.6%) carried more than 24 entities and the
# largest board was 45, so 24 blinded the agent to a quarter of
# its own consults. 48 covers that run with room; the driver
# reports entityTrunc every job, so if it ever bites again it
# says so rather than degrading quietly.
EMAX = 48                       # --emax overrides
# RTYPES is the wire's relation vocabulary (§2). The INDEX IS THE
# CONTRACT with StateEncoder.encodeRelations: an edge arrives as
# [src, dst, type] with type an index into this list, so reordering it
# silently relabels every edge in every transcript. Append only.
RTYPES = ["blocks", "blocked_by", "attacking_player",
          "targets", "controls", "attached_to"]
# EMAX, like MAX_K, is a buffer size and not an architectural constant:
# ent_in/rel_emb are shaped by EDIM/heads and padded slots are masked
# out, so raising it changes no weights. GDIM/EDIM/len(RTYPES) are NOT
# buffers - they are the meaning of the vectors, and a driver that
# disagrees about them is rejected at the handshake.


class E0Policy(nn.Module):
    def __init__(self, sdim=SDIM, cdim=CDIM):
        super().__init__()
        self.cdim = cdim
        self.state_net = nn.Sequential(
            nn.Linear(sdim, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.cand_net = nn.Sequential(nn.Linear(cdim, 64), nn.ReLU())
        self.scorer = nn.Sequential(
            nn.Linear(128 + 64, 64), nn.ReLU(), nn.Linear(64, 1))
        self.value = nn.Sequential(nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 1))

    def forward(self, state, cands, mask):
        # state (B,SDIM); cands (B,K,CDIM); mask (B,K) True=valid
        se = self.state_net(state)                      # (B,128)
        ce = self.cand_net(cands)                       # (B,K,64)
        se_exp = se.unsqueeze(1).expand(-1, cands.size(1), -1)
        logits = self.scorer(torch.cat([se_exp, ce], dim=-1)).squeeze(-1)
        logits = logits.masked_fill(~mask, -1e9)
        return logits, self.value(se).squeeze(-1)


class AttnPolicy(nn.Module):
    """C6: attention over candidates (optionally + LSTM memory).

    Tokens = [state] + candidates; a small transformer lets candidates
    attend to each other and to the state (the E0 scorer was pointwise -
    candidates never saw each other). ~300k params vs E0's 43k; the
    engine is 87% of wall-clock so the extra compute is free.

    lstm=True threads an LSTMCell over the consult sequence: the state
    token is replaced by the cell's hidden state. Training uses the
    STORED rollout hidden (detached, IMPALA-style stale-hidden) - the
    cell gets gradient through one step only, not BPTT. Documented
    approximation; hidden resets every episode.
    """

    def __init__(self, sdim=SDIM, cdim=CDIM, d=128, heads=4, layers=2,
                 lstm=False):
        super().__init__()
        self.cdim, self.d = cdim, d
        self.state_in = nn.Linear(sdim, d)
        self.cand_in = nn.Linear(cdim, d)
        enc_layer = nn.TransformerEncoderLayer(
            d, heads, dim_feedforward=256, dropout=0.0, batch_first=True)
        self.enc = nn.TransformerEncoder(enc_layer, layers)
        self.cell = nn.LSTMCell(d, d) if lstm else None
        self.scorer = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 1))
        self.value_head = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 1))

    def initial_hidden(self, batch=1):
        z = torch.zeros(batch, self.d)
        return (z, z.clone())

    def forward(self, state, cands, mask, hidden=None):
        return self.from_state_token(self.state_in(state),   # (B,d)
                                     cands, mask, hidden)

    def from_state_token(self, s, cands, mask, hidden=None):
        """Everything downstream of the state embedding.

        Extracted verbatim from forward() so EntityAttnPolicy can reuse
        the candidate path rather than copy it - ENCODER-V6-BUILD.md
        §4c is explicit that from state_tok onward nothing changes, and
        a copy is a place for the two to drift.
        """
        new_hidden = None
        if self.cell is not None:
            if hidden is None:
                hidden = self.initial_hidden(s.size(0))
            h, c = self.cell(s, hidden)
            new_hidden = (h, c)
            s_tok = h.unsqueeze(1)
        else:
            s_tok = s.unsqueeze(1)
        ct = self.cand_in(cands)                            # (B,K,d)
        x = torch.cat([s_tok, ct], dim=1)                   # (B,1+K,d)
        pad = torch.cat([torch.ones_like(mask[:, :1]), mask], dim=1)
        y = self.enc(x, src_key_padding_mask=~pad)
        logits = self.scorer(y[:, 1:]).squeeze(-1)
        logits = logits.masked_fill(~mask, -1e9)
        value = self.value_head(y[:, 0]).squeeze(-1)
        return (logits, value, new_hidden) if self.cell is not None \
            else (logits, value)


class EntityObs:
    """The v6 state, as tensors: globals, entity rows, mask, relations.

    Holds either ONE step (no batch dim, what the trajectory buffer
    stores) or a BATCH (what the net is called with). It exists so the
    PPO code can keep writing `states[mb]` and `torch.stack(...)`
    against a state that is four tensors instead of one.

    rel is a DENSE (E,E) type-index matrix, not the wire's edge list:
    0 means "no edge" and t+1 means RTYPES[t]. The index (rather than a
    precomputed bias) is what gets stored, so rel_emb receives gradient
    during the PPO update - a stored bias would freeze it.
    """

    __slots__ = ("g", "e", "mask", "rel")

    def __init__(self, g, e, mask, rel):
        self.g, self.e, self.mask, self.rel = g, e, mask, rel

    def __getitem__(self, idx):
        return EntityObs(self.g[idx], self.e[idx],
                         self.mask[idx], self.rel[idx])

    def size(self, dim=0):
        return self.g.size(dim)

    @staticmethod
    def stack(items):
        return EntityObs(torch.stack([o.g for o in items]),
                         torch.stack([o.e for o in items]),
                         torch.stack([o.mask for o in items]),
                         torch.stack([o.rel for o in items]))


class EntityAttnPolicy(AttnPolicy):
    """v6: one token per card, relations as attention bias, SUM pooled.

    ENCODER-V6-BUILD.md §4c. The six board scalars are replaced by

        state_tok = glob_in(globals) + pool(SUM_i ent_enc(ent_in(E))_i)

    and from state_tok onward this is `AttnPolicy.from_state_token`,
    unchanged and shared rather than copied. `--arch entattn` carries
    the LSTMCell because the arm it is compared against (`lstmattn`,
    what rung0_lane.sh trains) has it: the point of the A/B is that the
    STATE PATH is the only difference.

    SUM, NOT MEAN (§4c). Mean-pooling is exactly the collision this
    change exists to remove: with no positional encoding, three
    identical tokens each attend to three identical keys and come out
    of the encoder identical to one token attending to itself, so their
    MEAN is bit-identical to the single token's. `entattn_check.py`
    measures both and prints the pair.

    Relations. `rel_emb` is Embedding(len(RTYPES)+1, heads) with
    padding_idx=0, so the "no edge" row is exactly zero and STAYS
    exactly zero under training (padding_idx zeroes its gradient). That
    is what makes arm R0 - relations zeroed - degrade to plain
    self-attention numerically rather than approximately.

    Edge direction: an edge [s, d, t] adds bias to the score of QUERY s
    attending to KEY d. §2's reverse edges (`blocks` / `blocked_by`)
    are typed separately precisely because the bias is directed. A
    repeated (s,d) pair keeps the last type written.
    """

    def __init__(self, gdim=GDIM, edim=EDIM, cdim=CDIM, d=128, heads=4,
                 layers=2, ent_layers=2, lstm=True, n_rtypes=len(RTYPES)):
        # sdim=gdim: the inherited state_in IS glob_in (see the property
        # below). One Linear, two names, no duplicated parameter.
        super().__init__(sdim=gdim, cdim=cdim, d=d, heads=heads,
                         layers=layers, lstm=lstm)
        self.gdim, self.edim, self.heads = gdim, edim, heads
        self.n_rtypes, self.ent_layers = n_rtypes, ent_layers
        self.ent_in = nn.Linear(edim, d)
        self.rel_emb = nn.Embedding(n_rtypes + 1, heads, padding_idx=0)
        ent_layer = nn.TransformerEncoderLayer(
            d, heads, dim_feedforward=256, dropout=0.0, batch_first=True)
        self.ent_enc = nn.TransformerEncoder(ent_layer, ent_layers)
        self.pool = nn.Linear(d, d)

    @property
    def glob_in(self):
        """§4c's name for the inherited state_in: Linear(GDIM -> d)."""
        return self.state_in

    def entity_bias(self, rel, mask):
        """(B,E,E) type indices + (B,E) validity -> (B*heads,E,E) float.

        Padded KEYS get -inf so a padding slot cannot reach any real
        token. Padded QUERIES are computed and then thrown away by the
        pool; their rows must not be entirely -inf or softmax returns
        NaN, which is also why a board with zero entities keeps key 0
        open.
        """
        b, e = mask.shape
        bias = self.rel_emb(rel)                       # (B,E,E,heads)
        bias = bias.permute(0, 3, 1, 2)                # (B,heads,E,E)
        keys = mask.clone()
        keys[~mask.any(dim=1), 0] = True
        neg = torch.zeros(b, 1, 1, e, device=bias.device)
        neg = neg.masked_fill(~keys[:, None, None, :], float("-inf"))
        return (bias + neg).reshape(b * self.heads, e, e)

    def state_token(self, obs):
        """EntityObs (batched) -> (B,d) state token."""
        x = self.ent_in(obs.e)                                   # (B,E,d)
        y = self.ent_enc(x, mask=self.entity_bias(obs.rel, obs.mask))
        y = y * obs.mask.unsqueeze(-1)          # padded slots contribute 0
        return self.glob_in(obs.g) + self.pool(y.sum(dim=1))     # SUM

    def forward(self, obs, cands, mask, hidden=None):
        return self.from_state_token(self.state_token(obs),
                                     cands, mask, hidden)


def build_net(arch, sdim, cdim, gdim=GDIM, edim=EDIM,
              n_rtypes=len(RTYPES)):
    if arch == "e0":
        return E0Policy(sdim, cdim)
    if arch == "attn":
        return AttnPolicy(sdim, cdim, lstm=False)
    if arch == "lstmattn":
        return AttnPolicy(sdim, cdim, lstm=True)
    if arch == "entattn":
        return EntityAttnPolicy(gdim, edim, cdim, n_rtypes=n_rtypes)
    raise ValueError(f"unknown arch {arch}")


class Trainer:
    def __init__(self, ckpt, seed, log_path, sdim=SDIM, cdim=CDIM,
                 shape=0.0, phi_scale=2000.0, arch="e0",
                 desperation=0.0, gdim=GDIM, edim=EDIM, emax=EMAX,
                 n_rtypes=len(RTYPES), r0=False):
        torch.manual_seed(seed)
        self.sdim, self.cdim = sdim, cdim
        # v6 state path; unused (and unvalidated) by the v1-v5 arches
        self.gdim, self.edim, self.emax = gdim, edim, emax
        self.n_rtypes = n_rtypes
        self.entity = (arch == "entattn")
        # R0 ablation arm: relations dropped on arrival, so the bias is
        # the all-zero padding_idx row and the entity encoder is plain
        # self-attention. Recorded in the ckpt because an R0 net
        # fine-tuned with relations live is exactly the confound R0
        # exists to remove.
        self.r0 = r0
        # C2a potential-based shaping: r'_t = r_t + shape*(GAMMA*Φ_{t+1}-Φ_t)
        # with Φ = tanh(raw_phi/phi_scale) and Φ(terminal) = 0 (policy-
        # invariant, Ng et al. 1999). shape=0 reproduces Phase 3/4 exactly.
        self.shape, self.phi_scale = shape, phi_scale
        self.arch = arch
        self.recurrent = arch in ("lstmattn", "entattn")
        self.hidden = None          # rollout hidden state (recurrent only)
        # C7 emergence: "I can't win now - try something." Training-time
        # sampling temperature scales with how LOSING the value head says
        # the state is: tau = 1 + desperation * max(0, -V), capped at 2.5.
        # logp is stored under the ACTUAL (tempered) sampling
        # distribution; PPO's ratio does the off-policy correction.
        self.desperation = desperation
        self.net = build_net(arch, sdim, cdim, gdim, edim, n_rtypes)
        self.opt = torch.optim.Adam(self.net.parameters(), lr=LR)
        self.ckpt = ckpt
        self.log_path = log_path
        self.episodes_seen = 0
        self.updates = 0
        if ckpt and os.path.exists(ckpt):
            data = torch.load(ckpt, weights_only=False)
            ck_arch = data.get("arch", "e0")
            if ck_arch != arch:
                raise RuntimeError(
                    f"ckpt arch {ck_arch} != requested {arch}")
            self._check_ckpt_dims(data, ckpt)
            self.net.load_state_dict(data["net"])
            self.opt.load_state_dict(data["opt"])
            self.episodes_seen = data.get("episodes", 0)
            self.updates = data.get("updates", 0)
            print(f"resumed ckpt: {self.episodes_seen} episodes, "
                  f"{self.updates} updates", flush=True)
        # trajectory buffers (across episodes until update)
        self.buf = []          # list of (state, cands, mask, action, logp, value)
        self.ep_start = 0      # index in buf where current episode began
        self.completed = []    # per finished episode: (start, end, reward)

    def dims(self):
        """What the vectors MEAN, as opposed to how big the buffers are.

        Written into every checkpoint so a load that would silently
        reinterpret them dies here instead of mispredicting for a run.
        emax/max_k are buffers and deliberately absent.
        """
        d = {"sdim": self.sdim, "cdim": self.cdim}
        if self.entity:
            d.update({"gdim": self.gdim, "edim": self.edim,
                      "rtypes": self.n_rtypes, "r0": self.r0})
            del d["sdim"]           # entattn has no flat state to mean
        return d

    def _check_ckpt_dims(self, data, path):
        have = data.get("dims")
        if have is None:
            # v1-v5 checkpoints predate this field. They can still be
            # loaded by their own arch; say out loud that the check did
            # not run rather than implying it passed.
            print(f"WARN: {path} has no dims record - loading unchecked "
                  f"(pre-v6 checkpoint)", flush=True)
            return
        want = self.dims()
        bad = [f"{k}: ckpt {have.get(k)} != server {v}"
               for k, v in want.items() if have.get(k) != v]
        if bad:
            raise RuntimeError(
                "CHECKPOINT DIM MISMATCH loading %s\n  %s\nThe weights "
                "would load and then mean something else. Match the "
                "flags (--gdim/--edim/--cdim/--r0) or start from a "
                "fresh checkpoint." % (path, "\n  ".join(bad)))

    def _entity_obs(self, g, ents, rels):
        """Wire lists -> a batch-1 EntityObs, validating as it goes.

        Every raise here is a drift the handshake cannot catch: a row
        that changed width mid-run, an edge indexing a padding slot, a
        relation type outside RTYPES.
        """
        if len(g) != self.gdim:
            raise ValueError(
                "consult globals carried %d dims, server expects GDIM=%d "
                "- start the server with --gdim %d or fix the emitter"
                % (len(g), self.gdim, len(g)))
        n = len(ents)
        if n > self.emax:
            # the k > MAX_K guard, extended to entities: without it the
            # assignment below fails with a shape error two frames down
            raise ValueError(
                "consult carried %d entities, buffer is %d - start the "
                "server with --emax >= %d (EMAX is a buffer size: "
                "raising it changes no weights)" % (n, self.emax, n))
        e = torch.zeros(1, self.emax, self.edim)
        for i, row in enumerate(ents):
            if len(row) != self.edim:
                raise ValueError(
                    "entity row %d carried %d dims, server expects "
                    "EDIM=%d" % (i, len(row), self.edim))
            e[0, i] = torch.tensor(row)
        m = torch.zeros(1, self.emax, dtype=torch.bool)
        m[0, :n] = True
        rel = torch.zeros(1, self.emax, self.emax, dtype=torch.long)
        if not self.r0:
            for edge in rels:
                if len(edge) != 3:
                    raise ValueError(
                        "relation edge %r is not [src,dst,type]" % (edge,))
                if any(float(x) != int(x) for x in edge):
                    # a JSON float here means the emitter formatted the
                    # indices with %.4f; int() would truncate silently
                    raise ValueError(
                        "relation edge %r is not integral - src/dst/type "
                        "are token indices, not floats" % (edge,))
                src, dst, ty = int(edge[0]), int(edge[1]), int(edge[2])
                if not (0 <= src < n and 0 <= dst < n):
                    raise ValueError(
                        "relation edge [%d,%d,%d] indexes outside the %d "
                        "emitted entities - the edge list and the token "
                        "order have drifted apart" % (src, dst, ty, n))
                if not (0 <= ty < self.n_rtypes):
                    raise ValueError(
                        "relation type %d is outside RTYPES (0..%d) - "
                        "driver and server disagree about the relation "
                        "vocabulary" % (ty, self.n_rtypes - 1))
                rel[0, src, dst] = ty + 1
        return EntityObs(torch.tensor(g, dtype=torch.float32).unsqueeze(0),
                         e, m, rel)

    def act(self, state, cands, sample, phi=0.0, session=None, ent=None):
        # session is None for the single-connection path (unchanged
        # behaviour); with --threads N every connection passes its own
        # Session so trajectories and LSTM memory never interleave
        sink = self if session is None else session
        with torch.no_grad():
            if self.entity:
                # ent = (globals, entity rows, relation edge list)
                s = self._entity_obs(*ent)      # batch-1 EntityObs
                store = s[0]                    # per-step, no batch dim
            else:
                s = torch.tensor(state).unsqueeze(0)
                store = s[0]
            k = len(cands)
            if k > MAX_K:
                # Without this the assignment below fails with a tensor
                # shape error two frames down, which is what a joint-
                # assignment arm against the default 40-slot buffer
                # actually looked like the first time: the server died
                # mid-run and the lane recorded nothing. Name the cause.
                raise ValueError(
                    "consult carried %d candidates, buffer is %d - start "
                    "the server with --max-k >= %d (joint arms need it: "
                    "rl.jointMaxCands for blocks, rl.attackMaxCands for "
                    "attacks)" % (k, MAX_K, k))
            c = torch.zeros(1, MAX_K, self.cdim)
            c[0, :k] = torch.tensor(cands)
            m = torch.zeros(1, MAX_K, dtype=torch.bool)
            m[0, :k] = True
            if self.recurrent:
                hin = sink.hidden if sink.hidden is not None \
                    else self.net.initial_hidden(1)
                logits, value, sink.hidden = self.net(s, c, m, hin)
            else:
                hin = None
                logits, value = self.net(s, c, m)
            if sample:
                lg = logits[0]
                if self.desperation > 0:
                    tau = min(2.5, 1.0 + self.desperation
                              * max(0.0, -float(value[0])))
                    lg = lg / tau
                dist = torch.distributions.Categorical(logits=lg)
                a = int(dist.sample())
                import math
                (self.buf if session is None else session.pending).append(
                    (store, c[0], m[0], a,
                                 float(dist.log_prob(torch.tensor(a))),
                                 float(value[0]),
                                 math.tanh(phi / self.phi_scale),
                     (hin[0][0].clone(), hin[1][0].clone())
                     if self.recurrent else None))
            else:
                a = int(torch.argmax(logits[0]))
            return a

    def end_episode(self, reward, training, session=None):
        self.hidden = None          # memory never crosses episodes
        if session is not None:
            session.hidden = None
        if not training:
            return
        if session is not None:
            # concurrent lane: append this game's steps as ONE contiguous
            # block, so every trajectory PPO sees is still a whole
            # episode in order - only the ORDER OF EPISODES in the batch
            # becomes scheduler-dependent (documented in PHASE9-PERF.md)
            self.ep_start = len(self.buf)
            self.buf.extend(session.pending)
            session.pending = []
        self.completed.append((self.ep_start, len(self.buf), reward))
        self.ep_start = len(self.buf)
        self.episodes_seen += 1
        if len(self.completed) >= UPDATE_EPISODES:
            self.update()

    def update(self):
        if not self.buf:
            self.completed = []
            return
        states = (EntityObs.stack([b[0] for b in self.buf]) if self.entity
                  else torch.stack([b[0] for b in self.buf]))
        cands = torch.stack([b[1] for b in self.buf])
        masks = torch.stack([b[2] for b in self.buf])
        actions = torch.tensor([b[3] for b in self.buf])
        old_logp = torch.tensor([b[4] for b in self.buf])
        values = torch.tensor([b[5] for b in self.buf])

        phis = [b[6] if len(b) > 6 else 0.0 for b in self.buf]
        if self.recurrent:
            hid_h = torch.stack([b[7][0] for b in self.buf])
            hid_c = torch.stack([b[7][1] for b in self.buf])
        adv = torch.zeros(len(self.buf))
        ret = torch.zeros(len(self.buf))
        for start, end, reward in self.completed:
            gae = 0.0
            for t in range(end - 1, start - 1, -1):
                v_next = values[t + 1] if t + 1 < end else 0.0
                r = reward if t == end - 1 else 0.0
                if self.shape:
                    phi_next = phis[t + 1] if t + 1 < end else 0.0
                    r += self.shape * (GAMMA * phi_next - phis[t])
                delta = r + GAMMA * v_next - values[t]
                gae = delta + GAMMA * LAM * gae
                adv[t] = gae
                ret[t] = gae + values[t]
        if adv.std() > 1e-6:
            adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        if self.recurrent:
            # Phase 7: TRUE BPTT - replay each episode as a sequence
            # through the cell, gradients through time (truncated), so
            # the hidden state is trained to CONTAIN useful history
            # (the stored-hidden one-step variant demonstrably fed the
            # attention a noise token - C6 lstm arm).
            self._update_recurrent(states, cands, masks, actions,
                                   old_logp, adv, ret)
            self._finish_update(n=len(self.buf), phis=phis)
            return

        n = len(self.buf)
        idx = torch.arange(n)
        for _ in range(EPOCHS):
            perm = idx[torch.randperm(n)]
            for mb in perm.split(256):
                logits, value = self.net(states[mb], cands[mb], masks[mb])
                dist = torch.distributions.Categorical(logits=logits)
                logp = dist.log_prob(actions[mb])
                ratio = torch.exp(logp - old_logp[mb])
                a = adv[mb]
                pg = -torch.min(ratio * a,
                                torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a).mean()
                vloss = ((value - ret[mb]) ** 2).mean()
                ent = dist.entropy().mean()
                loss = pg + VAL_COEF * vloss - ENT_COEF * ent
                self.opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), 0.5)
                self.opt.step()
        self._finish_update(n=n, phis=phis)

    def _update_recurrent(self, states, cands, masks, actions,
                          old_logp, adv, ret, tbptt=64, ep_batch=8):
        """True-BPTT PPO for lstmattn: episodes replayed as sequences,
        hidden carried by the live net, gradients through time
        (detached every tbptt steps). Episodes are batched together and
        stepped in lockstep; finished episodes drop out of the batch
        via a live mask."""
        episodes = [(s, e) for s, e, _ in self.completed if e > s]
        for _ in range(EPOCHS):
            order = torch.randperm(len(episodes))
            for g0 in range(0, len(episodes), ep_batch):
                group = [episodes[i] for i in order[g0:g0 + ep_batch]]
                maxlen = max(e - s for s, e in group)
                B = len(group)
                h, c = self.net.initial_hidden(B)
                losses = []
                for t in range(maxlen):
                    live = [bi for bi, (s, e) in enumerate(group)
                            if s + t < e]
                    idx = torch.tensor([group[bi][0] + t for bi in live])
                    lt = torch.tensor(live)
                    logits, value, (h2, c2) = self.net(
                        states[idx], cands[idx], masks[idx],
                        (h[lt], c[lt]))
                    h = h.clone(); c = c.clone()
                    h[lt] = h2; c[lt] = c2
                    if (t + 1) % tbptt == 0:
                        h = h.detach(); c = c.detach()
                    dist = torch.distributions.Categorical(logits=logits)
                    logp = dist.log_prob(actions[idx])
                    ratio = torch.exp(logp - old_logp[idx])
                    a = adv[idx]
                    pg = -torch.min(ratio * a,
                                    torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a)
                    vloss = (value - ret[idx]) ** 2
                    ent = dist.entropy()
                    losses.append((pg + VAL_COEF * vloss
                                   - ENT_COEF * ent).sum())
                loss = torch.stack(losses).sum() / max(
                    1, sum(e - s for s, e in group))
                self.opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), 0.5)
                self.opt.step()
                h = c = None

    def _finish_update(self, n, phis):
        self.updates += 1
        wr = sum(1 for _, _, r in self.completed if r > 0) / len(self.completed)
        mean_abs_phi = sum(abs(p) for p in phis) / max(1, len(phis))
        line = (f"update={self.updates} episodes={self.episodes_seen} "
                f"batch_eps={len(self.completed)} steps={n} "
                f"batch_win_rate={wr:.3f} mean_abs_phi={mean_abs_phi:.3f}")
        print("TRAIN|" + line, flush=True)
        if self.log_path:
            with open(self.log_path, "a") as f:
                f.write(f"{time.time():.0f},{self.updates},{self.episodes_seen},"
                        f"{n},{wr:.4f}\n")
        self.buf = []
        self.completed = []
        self.ep_start = 0
        self.save()

    def save(self):
        if self.ckpt:
            # atomic: a SIGKILL mid-save must never corrupt the ckpt
            # (a truncated net.pt took down a league run once)
            tmp = self.ckpt + ".tmp"
            torch.save({"net": self.net.state_dict(),
                        "opt": self.opt.state_dict(),
                        "episodes": self.episodes_seen,
                        "updates": self.updates,
                        "arch": self.arch,
                        "dims": self.dims()}, tmp)
            os.replace(tmp, self.ckpt)


class Session:
    """Per-connection trajectory + LSTM memory (--threads > 1)."""

    def __init__(self):
        self.pending = []
        self.hidden = None


# Phase 12 instrumentation: the comment below claims one lock is plenty
# "because the engine work this serializes against is 87% of wall-clock".
# rl/PHASE12-PERF-SCOPE.md removed ~35% of that engine work, so the
# claim needs re-measuring rather than re-asserting. LOCK_WAIT is time
# blocked ACQUIRING the lock; LOCK_HELD is time inside it. Reported on
# shutdown and via the "stats" message. Enabled by -DRL_LOCK_STATS=1
# (env), off by default so the hot path stays untouched.
LOCK_STATS = os.environ.get("RL_LOCK_STATS", "0") == "1"
LOCK_WAIT = 0.0
LOCK_HELD = 0.0
LOCK_CALLS = 0
_stats_lock = threading.Lock()


def _record(wait, held):
    global LOCK_WAIT, LOCK_HELD, LOCK_CALLS
    with _stats_lock:
        LOCK_WAIT += wait
        LOCK_HELD += held
        LOCK_CALLS += 1
        n = LOCK_CALLS
        w, h = LOCK_WAIT, LOCK_HELD
    if n % 2000 == 0:
        print(f"RLLOCK|calls={n}|wait_s={w:.1f}|held_s={h:.1f}"
              f"|wait_per_call_ms={1000 * w / n:.2f}"
              f"|held_per_call_ms={1000 * h / n:.2f}"
              f"|wait_share={w / (w + h):.1%}", flush=True)


def check_hello(msg, trainer):
    """Reject a driver whose vectors mean something else. Loudly.

    ENCODER-V6-BUILD.md §4b: the failure this codebase keeps hitting is
    a handshake that SUCCEEDS while the meaning of the vectors has
    changed, after which the run mispredicts to completion and the
    numbers look like a result. So every meaning-carrying dim is
    checked here, and a mismatch raises rather than warns.

    Not checked for entattn: `sdim`. The flat state vector is not read
    by this arch, so enforcing its width would fail runs over a field
    that carries no meaning. cdim IS checked - the candidate path is
    untouched by v6 and still reads it.
    """
    hs, hc = msg.get("sdim"), msg.get("cdim")
    hg, he = msg.get("gdim"), msg.get("edim")
    hm, hr = msg.get("emax"), msg.get("rtypes")
    driver_v6 = any(x is not None for x in (hg, he, hm, hr))
    if trainer.entity and not driver_v6:
        raise RuntimeError(
            "HANDSHAKE MISMATCH: server is --arch entattn (entity "
            "tokens + relations) but the driver advertised no "
            "gdim/edim/emax/rtypes, i.e. it is emitting a flat v1-v5 "
            "state. Run the driver with -Drl.encoderV=6 or the server "
            "with --arch lstmattn.")
    if driver_v6 and not trainer.entity:
        raise RuntimeError(
            "HANDSHAKE MISMATCH: driver advertised v6 entity tokens "
            "(gdim=%s edim=%s emax=%s rtypes=%s) but the server is "
            "--arch %s, which reads a flat state vector. Start the "
            "server with --arch entattn." % (hg, he, hm, hr, trainer.arch))
    if not trainer.entity:
        if hs is not None and (hs != trainer.sdim or hc != trainer.cdim):
            raise RuntimeError(
                f"dim mismatch: driver {hs}/{hc} vs server "
                f"{trainer.sdim}/{trainer.cdim}")
        return
    missing = [k for k in ("gdim", "edim", "emax", "rtypes")
               if msg.get(k) is None]
    if missing:
        raise RuntimeError(
            "HANDSHAKE MISMATCH: v6 hello is missing %s - all four of "
            "gdim/edim/emax/rtypes are required so the server can "
            "prove the vectors mean what it thinks" % ", ".join(missing))
    bad = []
    if hg != trainer.gdim:
        bad.append(f"gdim: driver {hg} vs server {trainer.gdim}")
    if he != trainer.edim:
        bad.append(f"edim: driver {he} vs server {trainer.edim}")
    if hr != trainer.n_rtypes:
        bad.append(f"rtypes: driver {hr} vs server {trainer.n_rtypes} "
                   f"({', '.join(RTYPES)})")
    if hc is not None and hc != trainer.cdim:
        bad.append(f"cdim: driver {hc} vs server {trainer.cdim}")
    if hm > trainer.emax:
        # emax is a buffer, so this one is fixable without retraining -
        # say how, rather than just refusing
        bad.append(f"emax: driver emits up to {hm} entities, server "
                   f"buffer is {trainer.emax} - restart with "
                   f"--emax {hm} (buffer only, no weights change)")
    if bad:
        raise RuntimeError("HANDSHAKE MISMATCH:\n  " + "\n  ".join(bad))
    if hm < trainer.emax:
        print(f"note: driver emax={hm} < server buffer {trainer.emax} "
              f"(fine: padded slots are masked)", flush=True)
    if trainer.r0:
        print("note: arm R0 - relation edges are DROPPED on arrival",
              flush=True)


def consult_args(msg, trainer):
    """(state, cands, ent) for trainer.act, per arch."""
    if not trainer.entity:
        if "s" not in msg:
            raise RuntimeError(
                "consult carried no \"s\" field on a flat-state server")
        return msg["s"], msg["c"], None
    if "g" not in msg or "e" not in msg:
        raise RuntimeError(
            "consult carried no \"g\"/\"e\" fields on an entattn server "
            "- the driver switched encoder arms mid-connection")
    return None, msg["c"], (msg["g"], msg["e"], msg.get("r", []))


def handle(conn, trainer, lock, session):
    """One connection's message loop. lock is None on the single-threaded
    path, where it degenerates to the original inline loop."""
    import random as pyrandom
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    f = conn.makefile("rwb")
    mode = "train"
    try:
        for raw in f:
            msg = json.loads(raw)
            t = msg["t"]
            if t == "hello":
                mode = msg.get("mode", "train")
                try:
                    check_hello(msg, trainer)
                except RuntimeError as exc:
                    # tell the driver before dying, so the failure shows
                    # up in ITS log too rather than as a bare EOF
                    # COMPACT separators: the driver matches on the
                    # literal "ok":0 and json.dumps' default ", " / ": "
                    # spacing slipped past it, so the refusal arrived as
                    # a mid-consult stack trace instead of a clean
                    # "server refused the handshake"
                    f.write(json.dumps({"ok": 0, "err": str(exc)},
                                       separators=(",", ":")).encode()
                            + b"\n")
                    f.flush()
                    print("=" * 60 + f"\n{exc}\n" + "=" * 60, flush=True)
                    raise
                print(f"conn: mode={mode} episodes={msg.get('episodes')}",
                      flush=True)
                f.write(b'{"ok":1}\n')
            elif t == "consult":
                if mode == "random":
                    a = pyrandom.randrange(len(msg["c"]))
                else:
                    st, cd, ent = consult_args(msg, trainer)
                    if lock is None:
                        a = trainer.act(st, cd,
                                        sample=(mode == "train"),
                                        phi=msg.get("phi", 0.0), ent=ent)
                    elif LOCK_STATS:
                        _t0 = time.time()
                        with lock:
                            _t1 = time.time()
                            a = trainer.act(st, cd,
                                            sample=(mode == "train"),
                                            phi=msg.get("phi", 0.0),
                                            session=session, ent=ent)
                        _record(_t1 - _t0, time.time() - _t1)
                    else:
                        # torch inference and the trajectory buffers are
                        # the shared state; the engine work this
                        # serializes against is 87% of wall-clock, so one
                        # lock is plenty
                        with lock:
                            a = trainer.act(st, cd,
                                            sample=(mode == "train"),
                                            phi=msg.get("phi", 0.0),
                                            session=session, ent=ent)
                f.write(f'{{"a":{a}}}\n'.encode())
            elif t == "end":
                if lock is None:
                    trainer.end_episode(msg["r"], training=(mode == "train"))
                else:
                    with lock:
                        trainer.end_episode(msg["r"],
                                            training=(mode == "train"),
                                            session=session)
                f.write(b'{"ok":1}\n')
            f.flush()
    except (ConnectionResetError, BrokenPipeError, json.JSONDecodeError):
        pass
    finally:
        try:
            f.close()
            conn.close()
        except OSError:
            pass
        if mode == "train":
            if lock is None:
                trainer.save()
            else:
                with lock:
                    trainer.save()
        print("conn closed", flush=True)


def serve(port, trainer, threads=1):
    """threads=1 (default) keeps the original one-connection-at-a-time
    server, byte for byte. threads>1 accepts that many concurrent driver
    connections - one per game when the driver runs -Drl.concurrency=N -
    each with its own Session.

    Determinism note: with threads>1 in TRAIN mode, episodes still enter
    the PPO buffer whole and in order within themselves, but which
    episode lands first depends on the OS scheduler, so a training run is
    no longer bit-reproducible from its seed. Eval lanes must keep
    threads=1 (and the driver sequential) - Elo depends on it.
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(max(4, threads))
    print(f"policy server on :{port}"
          + (f" (threads={threads})" if threads > 1 else ""), flush=True)
    if threads <= 1:
        while True:
            conn, _ = srv.accept()
            handle(conn, trainer, None, None)
        return
    import threading
    lock = threading.Lock()
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle,
                         args=(conn, trainer, lock, Session()),
                         daemon=True).start()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7777)
    ap.add_argument("--threads", type=int, default=1,
                    help="concurrent driver connections "
                         "(1 = original sequential server)")
    ap.add_argument("--ckpt", default="/tmp/rl_e0.pt")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--log", default=None)
    ap.add_argument("--sdim", type=int, default=SDIM)
    ap.add_argument("--cdim", type=int, default=CDIM)
    ap.add_argument("--shape", type=float, default=0.0,
                    help="C2a shaping coefficient (0 = terminal-only)")
    ap.add_argument("--phi-scale", type=float, default=2000.0)
    ap.add_argument("--arch", default="e0",
                    choices=["e0", "attn", "lstmattn", "entattn"],
                    help="C6: net architecture (entattn = encoder v6)")
    ap.add_argument("--gdim", type=int, default=GDIM,
                    help="v6 globals width (meaning, not a buffer)")
    ap.add_argument("--edim", type=int, default=EDIM,
                    help="v6 entity token width (meaning, not a buffer)")
    ap.add_argument("--emax", type=int, default=EMAX,
                    help="v6 entity buffer; raising it changes no weights")
    ap.add_argument("--r0", action="store_true",
                    help="ablation arm R0: drop every relation edge, so "
                         "the entity encoder is plain self-attention")
    ap.add_argument("--lr", type=float, default=None,
                    help="override LR (default: LR constant; 3e-4 was "
                         "tuned for the 43k E0 net and is hot for the "
                         "C6 transformers)")
    ap.add_argument("--max-k", type=int, default=None,
                    help="candidate buffer; raise for joint assignment")
    ap.add_argument("--desperation", type=float, default=0.0,
                    help="C7: losing-state exploration temperature gain")
    args = ap.parse_args()
    # module scope (this is the __main__ block, not a function), so these
    # rebind the module globals directly - a `global` statement here is
    # both unnecessary and a SyntaxError after the earlier assignment
    if args.max_k is not None:
        MAX_K = args.max_k
    if args.lr is not None:
        LR = args.lr
    # Phase 12: 4 game threads + N server threads on 4 cores is heavily
    # oversubscribed; measured held-time per consult rose 3.40 -> 5.75 ms
    # from conc1 to conc4. Configurable so the trade can be measured.
    torch.set_num_threads(int(os.environ.get("RL_TORCH_THREADS", "2")))
    serve(args.port, Trainer(args.ckpt, args.seed, args.log,
                             args.sdim, args.cdim,
                             args.shape, args.phi_scale, args.arch,
                             args.desperation,
                             args.gdim, args.edim, args.emax,
                             len(RTYPES), args.r0), args.threads)
