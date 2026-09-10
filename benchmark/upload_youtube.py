"""Upload a rendered replay to YouTube (port of mage-bench's uploader).

mage-bench records its JavaFX observer through FFmpeg and, once the game is
over, uploads `recording.mov` with the YouTube Data API v3 (OAuth installed
app flow, resumable upload, then a playlist insert). Nothing is streamed
live. We keep the same shape: a client-secrets JSON from Google Cloud
Console, a cached OAuth token, a resumable upload, an optional playlist.

Setup (once):
  1. Google Cloud Console -> create a project -> enable "YouTube Data API v3".
  2. OAuth consent screen (external, testing), add your Google account as a
     test user; add the scopes youtube.upload and youtube.
  3. Credentials -> OAuth client ID -> Desktop app -> download JSON to
     ~/.cardguru/youtube-client-secrets.json
  4. pip install google-api-python-client google-auth-oauthlib
The first upload opens a browser for consent and caches the token at
~/.cardguru/youtube-token.json; later uploads are non-interactive.

Usage:
  python3 benchmark/upload_youtube.py --video replay.webm \
      --row research/data/decks/izzet_mirror_search_s23/mirror.jsonl \
      [--title ...] [--description-file notes.txt] [--privacy unlisted] \
      [--playlist PLxxxx] [--replay-url https://...]
"""
import argparse
import importlib
import json
import os
import sys
from pathlib import Path

CONF_DIR = Path(os.environ.get("CARDGURU_HOME", Path.home() / ".cardguru"))
CLIENT_SECRETS_FILE = CONF_DIR / "youtube-client-secrets.json"
TOKEN_FILE = CONF_DIR / "youtube-token.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
MIME = {".webm": "video/webm", ".mp4": "video/mp4", ".mov": "video/quicktime",
        ".mkv": "video/x-matroska"}


def _google():
    try:
        return {
            "Request": importlib.import_module("google.auth.transport.requests").Request,
            "Credentials": importlib.import_module("google.oauth2.credentials").Credentials,
            "InstalledAppFlow": importlib.import_module("google_auth_oauthlib.flow").InstalledAppFlow,
            "build": importlib.import_module("googleapiclient.discovery").build,
            "HttpError": importlib.import_module("googleapiclient.errors").HttpError,
            "MediaFileUpload": importlib.import_module("googleapiclient.http").MediaFileUpload,
        }
    except ImportError as exc:
        raise SystemExit("pip install google-api-python-client google-auth-oauthlib") from exc


def service():
    g = _google()
    creds = None
    if TOKEN_FILE.exists():
        creds = g["Credentials"].from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(g["Request"]())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                raise SystemExit(f"missing {CLIENT_SECRETS_FILE}; see the docstring for setup")
            flow = g["InstalledAppFlow"].from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        CONF_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
    return g["build"]("youtube", "v3", credentials=creds)


def load_row(path, index):
    """A row of a run's mirror.jsonl (the per-game result record)."""
    if not path:
        return {}
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    return rows[index] if rows else {}


def pretty_deck(name):
    return (name or "").replace("_", " ").title() if name else ""


def build_title(row, override=None):
    if override:
        return override[:100]
    model = row.get("model") or row.get("pilot") or "LLM pilot"
    a = pretty_deck(row.get("deck_a")) or "Dimir Midrange"
    b = pretty_deck(row.get("deck_b")) or a
    res, turns = outcome(row)
    tail = f" — {res}" if res else ""
    if turns:
        tail += f" T{turns}"
    title = f"CardGuru: {model} ({a}) vs XMage MAD ({b}){tail}"
    return title if len(title) <= 100 else title[:97] + "..."


def outcome(row):
    """(WIN|LOSS|DRAW|'', turns) from a mirror.jsonl row; the pilot is player A."""
    r = row.get("result")
    if isinstance(r, dict):
        w = r.get("winner")
        res = "WIN" if w == "A" else "LOSS" if w == "B" else ("DRAW" if r.get("status") == "completed" else "")
        return res, r.get("turns")
    return (str(r).upper() if r else ""), row.get("turns")


def build_description(row, replay_url=None, extra=None):
    lines = ["An LLM pilots a real, rules-enforced game of Magic: The Gathering "
             "(XMage) against XMage's built-in MAD AI, with a search over simulated "
             "lines scored by the model. The right panel shows every decision as "
             "a tree: candidate lines, simulated opponent responses, and the "
             "pilot's score for each leaf.", ""]
    res, turns = outcome(row)
    facts = [("Pilot", row.get("model")), ("Pilot deck", pretty_deck(row.get("deck_a"))),
             ("Opponent deck", pretty_deck(row.get("deck_b"))), ("Seed", row.get("seed")),
             ("Search", row.get("search")), ("Driver props", row.get("driver_props")),
             ("Result", f"{res} on turn {turns}" if res and turns else res or None),
             ("Pilot calls", (row.get("sources") or {}).get("llm")),
             ("Wall clock", f"{row['wall_s'] / 60:.0f} min" if row.get("wall_s") else None)]
    lines += [f"{k}: {v}" for k, v in facts if v not in (None, "")]
    if replay_url:
        lines += ["", "Interactive replay:", replay_url]
    if extra:
        lines += ["", extra]
    return "\n".join(lines)


def upload(video, title, description, privacy, playlist, tags):
    g = _google()
    yt = service()
    body = {
        "snippet": {"title": title, "description": description, "tags": tags,
                    "categoryId": "20"},          # Gaming
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = g["MediaFileUpload"](str(video), mimetype=MIME.get(video.suffix.lower(), "video/*"),
                                 resumable=True, chunksize=10 * 1024 * 1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"\r  upload {int(status.progress() * 100)}%", end="", flush=True)
    vid = resp["id"]
    url = f"https://youtu.be/{vid}"
    print(f"\r  uploaded {url}      ")
    if playlist:
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": playlist,
                "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            print("  added to playlist")
        except g["HttpError"] as e:
            print(f"  playlist insert failed: {e}")
    return url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--row", help="mirror.jsonl of the run (title/description from its row)")
    ap.add_argument("--row-index", type=int, default=0)
    ap.add_argument("--title")
    ap.add_argument("--description-file")
    ap.add_argument("--replay-url")
    ap.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"])
    ap.add_argument("--playlist", default=os.environ.get("YOUTUBE_PLAYLIST_ID"))
    ap.add_argument("--tags", default="cardguru,magic-the-gathering,xmage,ai,llm,claude")
    ap.add_argument("--dry-run", action="store_true", help="print title/description only")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        raise SystemExit(f"no such video: {video}")
    row = load_row(args.row, args.row_index)
    title = build_title(row, args.title)
    extra = open(args.description_file, encoding="utf-8").read() if args.description_file else None
    desc = build_description(row, args.replay_url, extra)
    print(f"title: {title}\n---\n{desc}\n---")
    if args.dry_run:
        return
    url = upload(video, title, desc, args.privacy, args.playlist,
                 [t.strip() for t in args.tags.split(",") if t.strip()])
    if args.row:
        # remember the URL next to the run, like mage-bench writes it into game_meta.json
        side = Path(args.row).with_name("youtube.json")
        data = json.loads(side.read_text()) if side.exists() else {}
        data[str(args.row_index)] = {"url": url, "title": title, "video": str(video)}
        side.write_text(json.dumps(data, indent=2) + "\n")
        print(f"  saved to {side}")
    print(url)


if __name__ == "__main__":
    sys.exit(main())
