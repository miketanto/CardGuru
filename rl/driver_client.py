"""Client for the Phase 9 persistent driver JVM (RLDriverServer).

Drop-in replacement for one `mvn -pl Mage.Tests surefire:test
-Dtest='RLEpisodeDriver' ...` invocation: pass the same -Drl.* flags,
get the same stdout (progress lines, RL|summary, RL|ipc) and the same
-Drl.out file, minus the JVM boot.

    python3 rl/driver_client.py --port 7910 -Drl.episodes=64 -Drl.agent=rl ...

Exit code mirrors the job's rc, so callers can `|| exit 1` as they do
with mvn. --start/--stop manage the server itself.
"""
import argparse
import socket
import sys


def send(port, line, timeout=None):
    """Send one command, stream the reply until RLJOB|done / RLJOB|bye."""
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        s.settimeout(timeout)
        s.sendall((line + "\n").encode())
        f = s.makefile("r", encoding="utf-8")
        rc = 0
        for reply in f:
            reply = reply.rstrip("\n")
            if reply.startswith("RLJOB|done"):
                for part in reply.split("|"):
                    if part.startswith("rc="):
                        rc = int(part[3:])
                return rc
            if reply.startswith("RLJOB|bye") or reply.startswith("RLJOB|pong"):
                print(reply, flush=True)
                return 0
            print(reply, flush=True)
        return 1        # connection closed without a done marker


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--port", type=int, default=7910)
    ap.add_argument("--ping", action="store_true")
    ap.add_argument("--shutdown", action="store_true")
    ap.add_argument("--timeout", type=float, default=None,
                    help="seconds to wait for the job (default: no limit)")
    args, rest = ap.parse_known_args()

    if args.shutdown:
        sys.exit(send(args.port, "shutdown"))
    if args.ping:
        sys.exit(send(args.port, "ping"))
    job = " ".join(t for t in rest if t.startswith("-D"))
    if not job:
        print("no -D flags given: nothing to run", file=sys.stderr)
        sys.exit(2)
    sys.exit(send(args.port, job, args.timeout))


if __name__ == "__main__":
    main()
