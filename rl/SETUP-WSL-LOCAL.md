# Local environment — WSL2 Ubuntu on the Windows desktop (2026-09-10)

The cloud containers that ran Phases 0–12 are gone. This is the first
local environment, and every lane path in `rl/` still resolves against
`/home/user/CardGuru` and `/home/user/mage`, so the layout below
recreates that with symlinks rather than editing the scripts.

## Layout

| path | what | notes |
|---|---|---|
| `C:\Users\sutanto4\Documents\CardGuru` | the repo (`main`) | the only checkout; Claude Code sessions open here |
| `/home/user/CardGuru` → `/mnt/c/Users/sutanto4/Documents/CardGuru` | symlink | so `RL=/home/user/CardGuru/rl` in the lanes resolves |
| `/home/miketanto/mage` | XMage pin `7554968c` + `phase9-engine.patch` + overlays | WSL-native ext4; never put this on `/mnt/c` (9P is far too slow for Maven) |
| `/home/user/mage` → `/home/miketanto/mage` | symlink | `.rl_ready` marker present after build |
| `~/tools/jdk-21.0.12.1+1` | Temurin 21 | matches the JDK the cloud runs used |
| `~/tools/apache-maven-3.9.9` | Maven | `MAVEN_OPTS=-Xmx4g` |
| `~/engine_setup.log` | build log | last build 2026-09-10, `ENGINE|READY|7554968c` |

`~/.profile` and `~/.bashrc` export `JAVA_HOME`, `M2_HOME`, `PATH`. Python
is the system 3.10 with torch 2.7.1 (CUDA build, CPU used), numpy 2.2.6,
scikit-learn 1.7.0 (`--user`).

## Machine

Ryzen 7 5800X (16 threads), 16 GB RAM, ASUS TUF X570-PRO. WSL2 is capped
by `C:\Users\sutanto4\.wslconfig` at **12 GB RAM + 8 GB swap** (default
was 7 GB, below the driver JVM's `-Xmx4500m` plus the policy server's
5–6 GB peak). SVM had to be enabled in the BIOS before WSL2 would start.

## Rebuild recipe

`rl/setup_engine.sh` hardcodes the cloud paths; the local equivalent
(same steps, `$HOME` paths, `-T 2`) is what produced this build:

```
cd ~/mage && git checkout -f 7554968c && git clean -fdx -e '*/target'
git apply rl/engine-patches/phase9-engine.patch          # 3 files
cp rl/xmage-src/*.java   Mage.Tests/src/test/java/org/mage/test/benchmark/rl/
cp benchmark/xmage/src/*.java Mage.Tests/src/test/java/org/mage/test/benchmark/
cp rl/*.dck benchmark/xmage/*.dck Mage.Tests/   # setup_engine.sh copies only rl/*.dck;
                                                 # BenchBurn/BenchDimir live in benchmark/xmage/
mvn -q -T 2 -DskipTests -Dmaven.javadoc.skip=true install  # ~3 min here
```

## Verified 2026-09-10

Both smoke tests passed on this layout; their outputs are n=4 and carry
no information about play, only about plumbing.

1. Engine path: `run_driver.sh` with `-Drl.agent=heuristic
   -Drl.opponent=heuristic`, 4 games of `BenchBurn` mirror, persistent
   driver JVM autostarted, ~2.6 games/s.
2. RL path: `R0_ENCODER_V=6 R0_EVAL_G=4 R0_CP7_G=0 R0_EVERY=64
   R0_CHUNK=32 bash rl/rung0_lane.sh B0Base B0Twin 64 0` ran init net →
   ck_0 battery (D0/D1/TWIN) → 64 training episodes → one `TRAIN|` row in
   `train.csv` → ck_64 battery → `R0_DONE`, in 2 min 7 s wall clock.

The lane leaves the driver JVM running by design; `pkill -f
"[R]LDriverServer"` before switching encoder arms.

## Throughput — what this machine is and is not

Measured in `THROUGHPUT-LOCAL.md` (rung-0 lane, single runs). The
engine runs at the same per-game speed as the old 4-core container
(2.6 vs 2.7 games/s on the scripted BenchBurn mirror). Training
throughput at conc4 is 0.535 episodes/s on CPU and 1.12 on `--device
cuda`; more game threads are a regression because the PPO update is
single-threaded and holds the consult lock. What changed versus the
cloud is availability, not speed: no session recycling, checkpoints
that survive, and a GPU. Five-seed rung-0 runs are an overnight job,
not a fast one.

## Gotchas specific to this machine

- **Driving WSL from Git Bash:** MSYS rewrites `/mnt/c/...` arguments
  into Windows paths before `wsl.exe` sees them, and `$VAR` / `$(...)`
  inside the command string are unreliable. Put anything non-trivial in
  a script file and run `wsl.exe -d Ubuntu -- bash -c 'bash /mnt/c/.../x.sh'`.
- `unzip` is not installed in the distro; use `python3 -m zipfile`.
- Treat `/tmp` inside WSL as disposable, same rule as the containers —
  anything that matters goes to `rl/artifacts/`.
- The repo lives on `/mnt/c`. Python imports and deck copies from there
  are fine; do not point Maven or `/tmp/rl_*` outputs at it.
