# Phase 5 C2a — BC-initialized PPO with potential-based shaping

## Question

C1 left two failure modes on the table: the BC student is off-policy
blind (covariate shift), and Phase 4's PPO was signal-starved (terminal
reward only). C2a fine-tunes the BC student with PPO and asks whether
densifying the reward with potential-based shaping
(Φ = tanh(GameStateEvaluator2/2000), r' = r + γΦ' − Φ, Φ(terminal)=0,
policy-invariant) buys anything beyond plain fine-tuning.

Gate (set in PHASE5-C1.md): >.45 vs D1 at 500g, decisively out of the
old plateau, plus a stall-rate cut.

## Arms (all v3 instruments, BC init = student_v3.pt, 1,280 episodes
## each vs D1 on the 4-deck pool, UPDATE_EPISODES=32, seeds 21M+)

- shape (coef 1.0) x 2 seeds, noshape (terminal-only control) x 1 seed.
- v2 partials (3,872 episodes across 4 runs, stopped at the v3
  instrument bump): shaped rolling .49-.54, unshaped .45-.50 - a
  suggestive edge that motivated keeping the control arm.

## Results

Rolling evals (100g @950000) sat at .47-.54 for every arm. The 500g
confirmations @960000 (the honest block - same block as the BC
baselines) told a tighter story:

| system | vs D0v3 | vs D1v3 | stalls (vs D1) |
|---|---|---|---|
| BC student v3 (baseline) | .428 | .396 | 8.6% |
| BC + PPO, no shaping (s0) | .442 | **.442** | 10.2% |
| BC + PPO + shaping (s0) | .476 | **.434** | 9.8% |
| BC + PPO + shaping (s1) | — | **.434** | 12.8% |
| teacher refs: D1v3 vs D0v3 .614 (Dimir); teacher mirror .504 (pool) | | | |

## Findings

1. **Fine-tuning works, modestly.** +.04-.05 over BC vs D1 (.396 ->
   .434-.442), consistent across all three runs and both reward
   variants. The 100g rolling numbers flattered every arm by ~.07 -
   the 500g CI gate caught it again.
2. **Shaping is a null result.** .434/.434 shaped vs .442 unshaped -
   the v2 hint did not replicate. Post-hoc this is intuitive: PBRS with
   a materialist potential teaches material preferences the BC init
   already has. The dense-signal hypothesis from PHASE4-VERDICT is now
   tested and dead at this Φ; a better Φ would need a better evaluator
   (the same wall as the depth ladder).
3. **The gate FAILED.** Point estimates .434-.442 sit under .45 (CI
   includes it; decisiveness does not), and stalls got WORSE (8.6% ->
   10-13%). PPO is optimizing win rate at the cost of liveness -
   pass-heavy safety is locally rewarded vs a punishing opponent.
4. **The v3 action surface did not reach the learned policy.**
   Transcript sampling of the best checkpoint: 100% of casts at main
   phase, zero ninjutsu, zero end-step flash across sampled games. The
   teacher itself only uses the new lines opportunistically (it taps
   out greedily, so flash mostly shifts to its own upkeep - the
   evaluator cannot price holding mana open), and 95% of demonstration
   labels are main-phase actions. Imitation + light PPO cannot
   discover timing lines the teacher barely demonstrates.
5. Ceiling arithmetic: the imitation-family ceiling is the teacher
   (~.50 mirror). We are at .44. Everything above ~.50 vs D1 requires
   surpassing the teacher, which neither BC, PPO-from-BC, nor this
   shaping can do by construction.

## BRANCH TAKEN: C3 = DAgger-style interactive imitation (priority
## windows), with a hard budget and a documented ceiling

Covariate shift remains the binding, attackable constraint: the
teacher's labels on the STUDENT's visited states are the one signal
this stack can still produce cheaply (SearchPlayer's scoring refactored
to label arbitrary states from the student's seat). Success criterion:
close most of the BC->teacher gap on-policy (~.48+ vs D1 at 500g)
without a stall regression. If DAgger lands under that, the C-track
concludes at "teacher-parity approached; ceiling = teacher," and the
path to actually BEATING D1 runs through better evaluators/self-play
(Track B territory), not more imitation.

Shaping infrastructure stays in the codebase (rl.phi, --shape) - it is
correct, cheap, and a better Φ may yet arrive; the null is recorded.
