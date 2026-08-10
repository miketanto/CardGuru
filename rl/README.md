# RL measurement system — episodes to competence

Goal: ONE number — episodes to beat `HeuristicPlayer` on a burn mirror
(Task B). Not an agent. Build spec gates and results: RESULTS.md, VERDICT.md.

## Milestone 1 — consults/game convention (reconciliation)

**Convention: every number under `rl/` is AGENT-SEAT consults per
episode.** The Phase 1 (495 windows/game) and Phase 2 (216 windows/game)
numbers both summed BOTH seats through shared static counters; they
differ from each other because Phase 1's B3 games were accidentally
hellbent (50-turn topdeck games — see Phase 2 erratum) while Phase 2
games were real 9-turn games. Nothing was per-seat until now. Comparable
chain on identical burn mirrors: Phase 2 both-seat no-gate 216/game ->
agent-seat ~108 -> with k=0 gate + phantom-land filter + yields, the
driver measures **~42 agent consults/episode** (priority + target +
combat consults; combat callbacks were never counted in Phase 1/2
priority-window numbers).

## Architecture

- Java (in the XMage checkout, `org.mage.test.benchmark.rl`, copies in
  `rl/xmage-src/`): `RLPlayer` (policy-delegated decisions, wrapper
  filters, Phase 2 yields, canonical ordering + shuffle seeding),
  `StateEncoder` (E0 fixed vectors: state 24-d, candidate 38-d,
  16-bucket name-hash identity), `RLEpisodeDriver` (episode loop,
  win/loss/stall accounting, agent-seat metrics), `SocketPolicyClient`
  (IPC V1: newline-delimited JSON over localhost TCP) /
  `RandomPolicyClient` (in-process).
- Python: `policy_server.py` — E0 candidate-scoring MLP + PPO
  (terminal-only reward, per-CONSULT discounting gamma 0.997, GAE 0.95,
  clip 0.2, update every 32 episodes). Connection modes: train
  (sample+learn), eval (argmax, no learning), random (throughput probe).
- Orchestration: `task_a.sh` (Task A gate loop). Eval always uses fixed
  seeds (900000+) disjoint from training seeds (1e6+), argmax mode.

## Engine bugs handled (all five from the spec, plus two new)

1. Canonical shuffle: sort-by-name + reseed per (seed, player,
   shuffle-index) inside `shuffleLibrary`.
2. Canonical name-sorted action/target ordering everywhere.
3. Phantom land drop filtered outside own-main/empty-stack.
4. ComputerPlayer used ONLY as mana-payment solver (documented deviation:
   every decision callback is overridden; bench pools make payment
   tie-break-inert; any heuristic callback that fires is counted in
   `fallbacks=` and reported).
5. `GameOptions.testMode=false` (real opening hands) +
   `player.setTestMode(true)` (skip mulligan decisions).
6. NEW: finished games mark players lost/left and the flags survive
   object reuse -> fresh player objects every episode.
7. NEW: `Combat.getAttackablePlayers` spins forever when no live
   opponent remains (reachable under random policies). Local bounded-scan
   patch in the checkout (`LOCAL BENCH PATCH` comment) — upstreamable.

## Reward (decided explicitly)

Terminal only: +1 win, -1 loss, **0 for draw/stall** (stall = turn-60
bound; a stall is better than losing, worse than winning — burn mirrors
essentially never stall; revisit before Task C). Discounting per consult.
No dense shaping in headline runs.

## Milestone gates so far

| Gate | Result |
|---|---|
| M2: driver + random policy reproduces engine throughput | 3.01 games/sec in-process (Phase 2 burn per-window 3.76 with heuristic-vs-heuristic; here agent-vs-RandomPlayer, longer 13-turn games) |
| M3: IPC throughput delta | 2.81 games/sec over socket = **6.6% drop** — V1 synchronous IPC confirmed, no V2 needed |

## How to run

```bash
# policy server (standalone)
python3 rl/policy_server.py --port 7777 --ckpt /tmp/e0.pt --log /tmp/train.csv

# episodes (from the XMage checkout)
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' -DfailIfNoTests=false \
  -Drl.episodes=512 -Drl.opponent=random|heuristic -Drl.policy=socket|random \
  -Drl.port=7777 -Drl.mode=train|eval|random -Drl.seed=N -Drl.out=/tmp/results.txt

# Task A end-to-end
bash rl/task_a.sh <seed> <budget_episodes> <port>
```
Pin: XMage `7554968c` + the two local patches above. JDK 21, torch CPU.
