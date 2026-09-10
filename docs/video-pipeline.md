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
game ──driver (-Dcardguru.record)──▶ g1_record.jsonl.gz   (snapshots + game log)
     └─bridge──────────────────────▶ g1.jsonl              (decisions, searches, plans)
                    │
   replay_studio.py ┴──▶ g1_studio.html ──replay_video.js──▶ replay.webm ──upload_youtube.py──▶ YouTube
                            │
                            └── open in a browser: interactive replay (board + decision graph)
```

### 0. Recording — `GameRecorder` in `driver/CardGuruScenarioRunner.java`

The in-process game has no server or client, so there is nothing to screen
record. Instead the driver records the game itself when
`-Dcardguru.record=<path>` is set (run_mirror.py / llm_bridge.py `--record`
do this by default; `--no-record` turns it off):

- a **snapshot** at every decision request (stamped into the request as
  `snapshot_id`, so the bridge log links to it) and at every game-log
  line, deduplicated by state hash. A snapshot holds both players' life,
  library size, mana pool, counters, **hand** (both, face up), battlefield
  (per permanent: printing key `SET/NUM`, tapped, P/T, damage, counters,
  attachments, attacking / blocking, face-down, token, transformed), graveyard
  and exile, the **stack** bottom→top (spell or ability, source card, rules
  text, controller, resolved targets) and the combat groups.
- an **event** per game-log line (`PlayerA casts Shock targeting PlayerB`,
  triggers, damage, draws…), bound to its snapshot.
- a **card** record per printing (set, collector number, image file name,
  mana cost, type line, rules, P/T, back face) the first time it is seen.
- `meta` and `end` records. Simulation copies never reach the recorder
  (XMage does not fire log events from simulations and copies get a fresh
  event source), so search rollouts do not pollute the record.

A 10-turn game is ~0.3 MB plain (183 snapshots); run_mirror gzips it to
`g{n}_record.jsonl.gz` next to the log.

### 1. `benchmark/replay_studio.py` — record + log → replay page

`--log g1.jsonl --record g1_record.jsonl.gz --out g1_studio.html`. One frame
per kept snapshot: every decision, plus game-log snapshots when the board
changed or the step ended (`--event-frames all|step|none`). Each frame
carries the board, the events since the previous frame, and the decision
(tree, why, plan, options, answer) when there was one.

The page (template `replay_studio_template.html` + `replay_studio.js`,
inlined so the output is one file):

- **Board** (XMage layout): opponent panel (life, library, hand count, mana
  pool, counters, active/priority marks), their hand (face up; `h` hides
  it), their nonlands, their lands, our lands, our nonlands, our hand;
  cards are real art (Scryfall, see below) with P/T and damage, counter
  badges, loyalty, summoning-sick mark, tapped = rotated, auras/equipment
  tucked behind their host; graveyard / exile piles (click to open);
  the **stack** column (top of stack first: card art + name + cost + rules,
  abilities as darkened source art with the ability text, "→ targets");
  SVG **arrows** from stack items to their targets (gold), attackers to the
  defender (red), blockers to attackers (blue); a **game log** panel that
  scrolls with the replay (click a line to jump); hover any card for a big
  preview with rules text.
- **Decision graph** below the board: a timeline strip with one dot per
  decision (color by kind, brightness by score; click to jump), the search
  tree (candidates → sampled opponent turns → scored leaves, chosen path in
  gold, animated reveal) with **pan/zoom** (wheel, drag, double-click to
  fit), **click a candidate** to fold/unfold its subtree, **click a leaf**
  for its projected board, life and score, hover for the full line; the
  detail panel shows the pilot's why / plan / options / answer.
  Turn plans render as trees of candidate lines, steps, holds and rules.
- Keys: `←/→` frame, `[`/`]` previous/next decision, space play, `f` fit,
  `+/-` zoom, `e` toggle game-log frames, `h` hide their hand.
- Old logs without a record still export (`--log` only): board from the
  v1 snapshots, names only, art looked up by name, no stack targets or log.

`?present=1` is the 1920×1080 presentation layout; `window.__replay`
(`total`, `index()`, `goto(i, animate)`, `next()`, `duration(i)`,
`frame(i)`, `ready()`) is the capture API.

### Card images

Cards are identified by set code + collector number, the same scheme
XMage's own image downloader uses, and rendered from Scryfall:
`https://api.scryfall.com/cards/<set>/<number>?format=image&version=small`
(name lookup as a fallback, then a drawn placeholder). For offline use
and for video capture, prefetch once:

```
python3 benchmark/fetch_card_images.py --record research/data/x/g1_record.jsonl.gz \
    --images-dir research/data/card_images          # small + normal, ~100 ms/request
python3 benchmark/replay_studio.py ... --images-dir research/data/card_images [--embed-images]
```

`--images-dir` makes the page reference the cached files (relative paths);
`--embed-images` inlines them as data URIs (self-contained, larger).
`--image-stub` draws placeholders only (used for tests where Scryfall is
unreachable).

### 2. `benchmark/replay_video.js` — page → WebM

Headless Chromium (Playwright) opens the page in presentation mode with a
1920×1080 viewport and records the tab. The script steps
`window.__replay.next()`, waits for the board's images (`ready()`), then
waits the page's own per-frame duration (searches and plans linger,
auto-passes are skipped, game-log frames are short), so the video is the
same thing a viewer would see clicking through.

```
npm install playwright            # once; browser download not needed if you pass --chromium
NODE_PATH=./node_modules node benchmark/replay_video.js \
    --html replay.html --out replay.webm [--speed 1] [--max-frames N] \
    [--chromium /path/to/chrome]
```

Output is VP8 WebM at 25 fps, which YouTube accepts directly. Export the
page with `--images-dir` or `--embed-images` first so the capture does
not depend on Scryfall. For MP4, run
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
    --replay-url https://…/g1_studio.html --privacy unlisted [--playlist PL…] [--dry-run]
```

Title and description are built from the run's `mirror.jsonl` row (model,
decks, seed, result, turns, calls, wall clock); `--title` and
`--description-file` override. The uploaded URL is saved next to the run
in `youtube.json`. Uploads default to *unlisted*.

## Notes

- The record is the driver's view of the real game object, read at the
  moment of each request / log line. Per-object serialization is guarded,
  and the `end` record counts any errors (0 in the test games).
- Games logged before recording existed still render through the v1 path
  (names only). Re-run them to get art by printing, stack targets and the
  game log.
- Trees for games with the leaf-value cache show only the leaves actually
  sent to the pilot in that request; cached leaves are folded into the
  candidate aggregate.
