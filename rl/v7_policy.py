"""Phase 4g (v7 plan §2): the v7 policy as one module, with checkpoint I/O.

    net = V7Policy(card_emb="card_emb_v8", belief=True)
    logits, value, game_vec, state = net(batch, state)      # batch = v7_obs.collate([...]) on net's device
    net.save(path, episodes=n)                               # + dims record (refused by a server whose wire disagrees)
    net = V7Policy.load(path, device="cuda")

Everything behind `--arch v7` in the server goes through this class;
`e0` / `attn` / `lstmattn` / `entattn` are untouched.  `frozen=True`
detaches the card table AND every parameter (a probe must not be able to
write what it measures: `--frozen` in the plan).
"""
import os
import sys

import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v7_obs as V           # noqa: E402
import v7_net as N           # noqa: E402
import v7_encoder as E       # noqa: E402
import v7_heads as H         # noqa: E402
import v7_value as VT        # noqa: E402
import v7_belief as BL       # noqa: E402
import wire_validate as W    # noqa: E402


class V7Policy(nn.Module):
    def __init__(self, card_emb="card_emb_v8", d=256, layers=6, heads=8, value_layers=4, belief=True,
                 random_table=False, frozen=False):
        super().__init__()
        self.table = N.CardTable(card_emb, random=random_table)
        self.build = N.TokenBuilders(self.table, d=d)
        self.enc = E.StateGraphEncoder(d=d, heads=heads, layers=layers)
        self.heads = H.V7Heads(d=d)
        self.critic = VT.ValueTrunk(self.table, d=d, layers=value_layers)
        self.belief = BL.BeliefModule(d=d, heads=heads, off=not belief)
        self.config = dict(arch="v7", card_emb=self.table.version, d=d, layers=layers, heads=heads,
                           value_layers=value_layers, belief=belief)
        self.frozen = frozen
        if frozen:
            for p in self.parameters():
                p.requires_grad_(False)

    def policy_parameters(self):
        """Parameters the PPO optimiser owns: everything except the belief module (its own
        optimiser) and the frozen card table rows (a buffer; the adapter is trainable)."""
        skip = {id(p) for p in self.belief.parameters()}
        return [p for p in self.parameters() if id(p) not in skip and p.requires_grad]

    def forward(self, batch, state=None, oe_rows=None, true_hand_ids=None, ctx=None, D_me=None, D_opp=None,
                with_value=True):
        toks = self.build(batch, ctx=ctx, D_me=D_me, D_opp=D_opp)
        bel = self.belief(toks)
        toks = self.belief.attach(toks, bel)
        enc = self.enc(toks, ent_raw=batch["ent"])
        logits, game_vec, state = self.heads(enc, state)
        value = self.critic(batch, oe_rows, true_hand_ids, ctx=ctx, D_me=D_me, D_opp=D_opp) if with_value else None
        self.last_belief = bel
        return logits, value, game_vec, state

    # --- checkpoints ---------------------------------------------------------------
    def dims(self, hello=None):
        h = hello or {"card_emb": self.table.version, "d_c": self.table.adapter.out_features}
        return V.dims_record(h)

    def save(self, path, episodes=0, extra=None):
        torch.save({"arch": "v7", "config": self.config, "dims": self.dims(), "episodes": episodes,
                    "state_dict": self.state_dict(), **(extra or {})}, path)

    @classmethod
    def load(cls, path, device="cpu", frozen=False, hello=None):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        if ck.get("arch") != "v7":
            raise ValueError(f"{path}: arch {ck.get('arch')!r} is not v7")
        cfg = ck["config"]
        # refuse a disagreeing dims record BEFORE building anything (the wire is the contract)
        want = V.dims_record(hello or {"card_emb": cfg["card_emb"], "d_c": N.D_C})
        have = ck.get("dims", {})
        for k in ("wire", "v7_dims", "v7_rtypes", "v7_ctypes", "v7_zones", "card_emb", "d_c"):
            if have.get(k) != want.get(k):
                raise ValueError(f"{path}: dims record {k}={have.get(k)!r} disagrees with this server's {want.get(k)!r}")
        net = cls(card_emb=cfg["card_emb"], d=cfg["d"], layers=cfg["layers"], heads=cfg["heads"],
                  value_layers=cfg["value_layers"], belief=cfg["belief"], frozen=frozen,
                  random_table=(cfg["card_emb"] == "random"))
        net.load_state_dict(ck["state_dict"])
        return net.to(device)


def count_params(net):
    return {"total": sum(p.numel() for p in net.parameters()),
            "policy_trainable": sum(p.numel() for p in net.policy_parameters()),
            "belief": sum(p.numel() for p in net.belief.parameters()),
            "critic": sum(p.numel() for p in net.critic.parameters()),
            "card_table_rows": net.table.table.numel()}


if __name__ == "__main__":
    net = V7Policy(random_table=True)
    print({k: f"{v:,}" for k, v in count_params(net).items()})
