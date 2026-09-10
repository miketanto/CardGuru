# Replay visualization and video pipeline

Tools for turning a game log into an animated replay page, a 1080p video,
and a YouTube upload. Built for the write-up / video of the pilot research.

## How mage-bench does it (what we looked at)

mage-bench (GregorStocks/mage-bench) does **not** stream games live. Its
pipeline is record-then-upload:

- **Observer client.** A JavaFX observer (`Mage.Client.Observer`) joins the
  XMage table as a spectator and renders the normal Swing board.
- **Frame capture.** `FrameCaptureService` grabs the Swing frame at 30 fps
  and pipes raw RGB frames into FFmpeg
  (`-f rawvideo -pix_fmt rgb24 … -c:v libx264 -preset ultrafast -crf 23
  -pix_fmt yuv420p -fps_mode vfr`, `-use_wallclock_as_timestamps 1`) under
  `xvfb-run`; the result is `recording.mov` in the game's log directory.
- **Upload.** After the game, `src/magebench/common/youtube_upload.py`
  uploads the file with the YouTube Data API v3: OAuth installed-app flow
  (client secrets at `~/.mage-bench/youtube-client-secrets.json`, cached
  token), resumable `MediaFileUpload` in 10 MB chunks, then a playlist
  insert. Title is `mage-bench <Format>: <Name> (<Deck>) vs …`, description
  links the site replay; the URL is written back into `game_meta.json`.
- **Website replay.** A separate Astro site renders a step-through replay
  from an exported JSON (`game-export-v9`: snapshots, actions, LLM events,
  decisions). That is where the "what was the model thinking" view lives;
  the video is just the board.

Takeaway: the video is a screen recording of the client, and the reasoning
view is a web page. We do the same split but drive the video *from* the
web page, because our logs already carry everything the page needs.

## Our pipeline

```
g1.jsonl ──replay_studio.py──▶ replay.html ──replay_video.js──▶ replay.webm ──upload_youtube.py──▶ YouTube
                                    │
                                    └── open in a browser: interactive replay with the decision trees
```

### 1. `benchmark/replay_studio.py` — log → replay page

Every bridge-log row carries a full state snapshot; every search carries
its candidates, the simulated leaves (with `line` = the path
`candidate | opponent sample | our response`) and the pilot's scores; every
turn plan carries its candidate lines, steps, holds and rules. The exporter
turns those into frames:

- **Board column**: opponent side (life, battlefield with tapped / P/T /
  counters, hidden hand count, graveyard), the stack, our side with the hand.
  Creatures that are attacking or blocking are marked.
- **Decision panel**: an SVG tree for every search (`leaf_eval`) and every
  turn plan. Search trees are the driver's trie: root → candidate → sampled
  opponent turn → our response (leaf, with resulting life totals and the
  pilot's score). Candidate nodes show the aggregate the driver used (worst
  leaf, or mean over samples of the best response) and the chosen path is
  highlighted; the tree draws itself left-to-right when a frame is entered.
  Plan trees show candidate lines, steps, holds and if→then rules.
- Below the tree: the pilot's *why*, its running plan, the options it saw,
  and the raw answer.
- Frames are classified `pilot` / `auto` / `fallback` / `search` /
  `planning` / `plan` (plan-executed) so the transport can skip auto-passes.

```
python3 benchmark/replay_studio.py --log research/data/decks/izzet_mirror_search_s23/g1.jsonl \
    --out research/data/decks/izzet_mirror_search_s23/studio.html \
    --title "Sonnet 5 vs MAD — Izzet Spellementals mirror" --subtitle "search arm, seed 23" \
    --player-a "Sonnet 5 — Izzet" --player-b "MAD — Izzet"
```

The page is self-contained (no network). Keys: `←`/`→` step, space plays,
speed and "skip auto-passes" in the transport. `?present=1` switches to
the 1920×1080 presentation layout (no transport, larger tree) and exposes
`window.__replay` (`total`, `index`, `goto(i, animate)`, `next()`,
`duration(i)`, `frame(i)`) for scripting.

### 2. `benchmark/replay_video.js` — page → WebM

Headless Chromium (Playwright) opens the page in presentation mode with a
1920×1080 viewport and records the tab. The script steps
`window.__replay.next()` and waits the page's own per-frame duration
(searches and plans linger, auto-passes are short or skipped), so the
video is the same thing a viewer would see clicking through.

```
npm install playwright            # once; browser download not needed if you pass --chromium
NODE_PATH=./node_modules node benchmark/replay_video.js \
    --html replay.html --out replay.webm [--speed 1] [--max-frames N] \
    [--chromium /path/to/chrome]
```

Output is VP8 WebM at 25 fps, which YouTube accepts directly. Measured on
the Dimir search game: 20 frames → 83 s of video, ~8.6 MB, rendered in
about real time (Playwright's recorder encodes live). A full game (~175
frames, ~30 searches) is 10–15 minutes of video. For MP4, run
`ffmpeg -i replay.webm -c:v libx264 -crf 20 -pix_fmt yuv420p replay.mp4`
(needs a system ffmpeg with x264; Playwright's bundled ffmpeg only has
libvpx).

Voice-over / captions: the `why` text of every decision is in the page and
in the log, so a script can be generated from the same frames if you want
to narrate the decision trees.

### 3. `benchmark/upload_youtube.py` — WebM → YouTube

Port of mage-bench's uploader. Setup once: create a Google Cloud project,
enable YouTube Data API v3, create an OAuth "Desktop app" client, download
its JSON to `~/.cardguru/youtube-client-secrets.json` (override the
directory with `CARDGURU_HOME`), and
`pip install google-api-python-client google-auth-oauthlib`. The first run
opens a browser for consent and caches the token.

```
python3 benchmark/upload_youtube.py --video replay.webm \
    --row research/data/decks/izzet_mirror_search_s23/mirror.jsonl \
    --replay-url https://…/studio.html --privacy unlisted [--playlist PL…] [--dry-run]
```

Title and description are built from the run's `mirror.jsonl` row (model,
decks, seed, result, turns, calls, wall clock); `--title` and
`--description-file` override. The uploaded URL is saved next to the run
in `youtube.json`. Uploads default to *unlisted*.

## Notes

- The replay page reads only the bridge log; the daemon transcript is not
  needed. Games logged before the `attacking`/`blocking` fields were added
  still render, just without combat marks.
- Trees for games with the leaf-value cache show only the leaves actually
  sent to the pilot in that request; cached leaves are folded into the
  candidate aggregate.
- The layout scales the tree in presentation mode when it has room, and
  shrinks label columns (never the score/life columns) when it does not.
