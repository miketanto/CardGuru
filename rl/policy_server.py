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

Run: python3 rl/policy_server.py --port 7777 --ckpt /tmp/rl_e0.pt \
        [--seed 0] [--log /tmp/rl_train.csv]
"""
import argparse
import json
import os
import socket
import time

import torch
import torch.nn as nn

SDIM, CDIM = 24, 38          # defaults; --sdim/--cdim override (E2 uses a wider cdim)
GAMMA, LAM, CLIP, LR = 0.997, 0.95, 0.2, 3e-4
EPOCHS, ENT_COEF, VAL_COEF = 4, 0.01, 0.5
UPDATE_EPISODES = 32
MAX_K = 40


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
        s = self.state_in(state)                            # (B,d)
        new_hidden = None
        if self.cell is not None:
            if hidden is None:
                hidden = self.initial_hidden(state.size(0))
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


def build_net(arch, sdim, cdim):
    if arch == "e0":
        return E0Policy(sdim, cdim)
    if arch == "attn":
        return AttnPolicy(sdim, cdim, lstm=False)
    if arch == "lstmattn":
        return AttnPolicy(sdim, cdim, lstm=True)
    raise ValueError(f"unknown arch {arch}")


class Trainer:
    def __init__(self, ckpt, seed, log_path, sdim=SDIM, cdim=CDIM,
                 shape=0.0, phi_scale=2000.0, arch="e0",
                 desperation=0.0):
        torch.manual_seed(seed)
        self.sdim, self.cdim = sdim, cdim
        # C2a potential-based shaping: r'_t = r_t + shape*(GAMMA*Φ_{t+1}-Φ_t)
        # with Φ = tanh(raw_phi/phi_scale) and Φ(terminal) = 0 (policy-
        # invariant, Ng et al. 1999). shape=0 reproduces Phase 3/4 exactly.
        self.shape, self.phi_scale = shape, phi_scale
        self.arch = arch
        self.recurrent = (arch == "lstmattn")
        self.hidden = None          # rollout hidden state (recurrent only)
        # C7 emergence: "I can't win now - try something." Training-time
        # sampling temperature scales with how LOSING the value head says
        # the state is: tau = 1 + desperation * max(0, -V), capped at 2.5.
        # logp is stored under the ACTUAL (tempered) sampling
        # distribution; PPO's ratio does the off-policy correction.
        self.desperation = desperation
        self.net = build_net(arch, sdim, cdim)
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

    def act(self, state, cands, sample, phi=0.0):
        with torch.no_grad():
            s = torch.tensor(state).unsqueeze(0)
            k = len(cands)
            c = torch.zeros(1, MAX_K, self.cdim)
            c[0, :k] = torch.tensor(cands)
            m = torch.zeros(1, MAX_K, dtype=torch.bool)
            m[0, :k] = True
            if self.recurrent:
                hin = self.hidden if self.hidden is not None \
                    else self.net.initial_hidden(1)
                logits, value, self.hidden = self.net(s, c, m, hin)
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
                self.buf.append((s[0], c[0], m[0], a,
                                 float(dist.log_prob(torch.tensor(a))),
                                 float(value[0]),
                                 math.tanh(phi / self.phi_scale),
                                 (hin[0][0].clone(), hin[1][0].clone())
                                 if self.recurrent else None))
            else:
                a = int(torch.argmax(logits[0]))
            return a

    def end_episode(self, reward, training):
        self.hidden = None          # memory never crosses episodes
        if not training:
            return
        self.completed.append((self.ep_start, len(self.buf), reward))
        self.ep_start = len(self.buf)
        self.episodes_seen += 1
        if len(self.completed) >= UPDATE_EPISODES:
            self.update()

    def update(self):
        if not self.buf:
            self.completed = []
            return
        states = torch.stack([b[0] for b in self.buf])
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

        n = len(self.buf)
        idx = torch.arange(n)
        for _ in range(EPOCHS):
            perm = idx[torch.randperm(n)]
            for mb in perm.split(256):
                if self.recurrent:
                    logits, value, _ = self.net(states[mb], cands[mb],
                                                masks[mb],
                                                (hid_h[mb], hid_c[mb]))
                else:
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
            torch.save({"net": self.net.state_dict(),
                        "opt": self.opt.state_dict(),
                        "episodes": self.episodes_seen,
                        "updates": self.updates,
                        "arch": self.arch}, self.ckpt)


def serve(port, trainer):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(4)
    print(f"policy server on :{port}", flush=True)
    import random as pyrandom
    while True:
        conn, _ = srv.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        f = conn.makefile("rwb")
        mode = "train"
        try:
            for raw in f:
                msg = json.loads(raw)
                t = msg["t"]
                if t == "hello":
                    mode = msg.get("mode", "train")
                    hs, hc = msg.get("sdim"), msg.get("cdim")
                    if hs is not None and (hs != trainer.sdim or hc != trainer.cdim):
                        raise RuntimeError(
                            f"dim mismatch: driver {hs}/{hc} vs server "
                            f"{trainer.sdim}/{trainer.cdim}")
                    print(f"conn: mode={mode} episodes={msg.get('episodes')}",
                          flush=True)
                    f.write(b'{"ok":1}\n')
                elif t == "consult":
                    if mode == "random":
                        a = pyrandom.randrange(len(msg["c"]))
                    else:
                        a = trainer.act(msg["s"], msg["c"],
                                        sample=(mode == "train"),
                                        phi=msg.get("phi", 0.0))
                    f.write(f'{{"a":{a}}}\n'.encode())
                elif t == "end":
                    trainer.end_episode(msg["r"], training=(mode == "train"))
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
                trainer.save()
            print("conn closed", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7777)
    ap.add_argument("--ckpt", default="/tmp/rl_e0.pt")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--log", default=None)
    ap.add_argument("--sdim", type=int, default=SDIM)
    ap.add_argument("--cdim", type=int, default=CDIM)
    ap.add_argument("--shape", type=float, default=0.0,
                    help="C2a shaping coefficient (0 = terminal-only)")
    ap.add_argument("--phi-scale", type=float, default=2000.0)
    ap.add_argument("--arch", default="e0",
                    choices=["e0", "attn", "lstmattn"],
                    help="C6: net architecture")
    ap.add_argument("--lr", type=float, default=None,
                    help="override LR (default: LR constant; 3e-4 was "
                         "tuned for the 43k E0 net and is hot for the "
                         "C6 transformers)")
    ap.add_argument("--desperation", type=float, default=0.0,
                    help="C7: losing-state exploration temperature gain")
    args = ap.parse_args()
    if args.lr is not None:
        LR = args.lr
    torch.set_num_threads(2)
    serve(args.port, Trainer(args.ckpt, args.seed, args.log,
                             args.sdim, args.cdim,
                             args.shape, args.phi_scale, args.arch,
                             args.desperation))
