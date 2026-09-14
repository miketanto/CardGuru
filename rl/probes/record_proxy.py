#!/usr/bin/env python3
"""Phase 9: record a v7 policy's OWN play.  A line proxy between the driver
and a real policy server: every line the driver sends (hello / consult / end)
is forwarded to the upstream server and its reply is sent back unchanged;
both are appended byte for byte to --out, so the file reads like a
wire_echo_server recording except that the {"a":k} replies are the
policy's choices.  Nothing here is a policy.

  python3 rl/probes/record_proxy.py --port 7948 --upstream 7947 --out REC.jsonl --max-conns 1
"""
import argparse
import socket


def serve(port, upstream, out, max_conns):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(4)
    print(f"record proxy on :{port} -> :{upstream} -> {out}", flush=True)
    conns = 0
    with open(out, "ab") as f:
        while max_conns <= 0 or conns < max_conns:
            c, _ = srv.accept()
            conns += 1
            up = socket.create_connection(("127.0.0.1", upstream))
            up_rd = up.makefile("rb")
            rd = c.makefile("rb")
            n = 0
            for raw in rd:
                if not raw.strip():
                    continue
                f.write(raw)
                up.sendall(raw)
                rep = up_rd.readline()
                if not rep:
                    print("upstream closed", flush=True)
                    break
                f.write(rep)
                f.flush()
                c.sendall(rep)
                n += 1
            try:
                up.close()
            except OSError:
                pass
            c.close()
            print(f"connection {conns} closed after {n} lines", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--upstream", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-conns", type=int, default=0)
    a = ap.parse_args()
    serve(a.port, a.upstream, a.out, a.max_conns)
