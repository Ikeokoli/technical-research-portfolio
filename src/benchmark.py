"""Measure real loopback HTTP calls against deliberately configured fault profiles."""
import argparse
import hashlib
import http.client
import json
import platform
import random
import socket
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PROFILES = {
    "fast_fragile": {"usable": 80, "empty": 5, "http_error": 5, "timeout": 10,
                     "delay_s": 0.002},
    "steady": {"usable": 98, "empty": 0, "http_error": 2, "timeout": 0,
               "delay_s": 0.008},
}
TIMEOUT_S = 0.15
DEADLINE_MS = 120.0


def planned_outcome(profile, slot):
    cursor = 0
    for outcome in ("usable", "empty", "http_error", "timeout"):
        cursor += PROFILES[profile][outcome]
        if slot < cursor:
            return outcome
    raise ValueError("slot must be between 0 and 99")


def is_usable(payload):
    if not isinstance(payload, dict):
        return False
    rows = payload.get("organic_results")
    return isinstance(rows, list) and any(
        isinstance(row, dict)
        and isinstance(row.get("title"), str) and row["title"].strip()
        and isinstance(row.get("link"), str)
        and row["link"].startswith("https://example.org/")
        for row in rows
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        query = parse_qs(urlsplit(self.path).query)
        profile, slot = query["profile"][0], int(query["slot"][0])
        outcome = planned_outcome(profile, slot)
        time.sleep(0.30 if outcome == "timeout" else PROFILES[profile]["delay_s"])
        payload = {"organic_results": [{"title": "Fixture result",
                    "link": "https://example.org/result"}]}
        if outcome == "empty":
            payload = {"organic_results": []}
        elif outcome == "http_error":
            payload = {"error": "injected upstream failure"}
        body = json.dumps(payload).encode()
        try:
            self.send_response(503 if outcome == "http_error" else 200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # The client deliberately stops waiting for timeout fixtures.


def measure(port, block, profile, slot, sequence):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=TIMEOUT_S)
    status, usable, byte_count, error = None, False, 0, None
    started = time.perf_counter_ns()
    try:
        conn.request("GET", f"/?profile={profile}&slot={slot}")
        response = conn.getresponse()
        status = response.status
        body = response.read()
        byte_count = len(body)
        if status != 200:
            error = "http_error"
        else:
            try:
                usable = bool(is_usable(json.loads(body)))
                if not usable:
                    error = "unusable_payload"
            except (ValueError, UnicodeDecodeError):
                error = "invalid_json"
    except (TimeoutError, socket.timeout):
        error = "timeout"
    except (OSError, http.client.HTTPException):
        error = "transport_error"
    finally:
        elapsed_ns = time.perf_counter_ns() - started
        conn.close()
    return {"block": block, "sequence": sequence, "profile": profile, "slot": slot,
            "planned_outcome": planned_outcome(profile, slot), "status": status,
            "usable": usable, "error": error, "bytes": byte_count,
            "elapsed_ns": elapsed_ns,
            "usable_within_deadline": usable and elapsed_ns <= DEADLINE_MS * 1e6}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blocks", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260912)
    args = parser.parse_args()
    if args.blocks < 1:
        parser.error("--blocks must be positive")
    args.out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    rng = random.Random(args.seed)
    try:
        # Warmups exercise each profile's success path; excluded from published rows.
        for profile in PROFILES:
            for index in range(5):
                measure(server.server_port, 0, profile, 0, index)
        with (args.out / "attempts.jsonl").open("w", encoding="utf-8", newline="\n") as f:
            sequence = 0
            for block in range(1, args.blocks + 1):
                jobs = [(profile, slot) for profile in PROFILES for slot in range(100)]
                rng.shuffle(jobs)
                for profile, slot in jobs:
                    row = measure(server.server_port, block, profile, slot, sequence)
                    f.write(json.dumps(row, sort_keys=True) + "\n")
                    sequence += 1
                print(f"Completed block {block}: 200 measured requests", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    manifest = {"started_at_utc": started,
                "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                "experiment": "controlled loopback HTTP; injected faults, no external provider",
                "python": platform.python_version(), "os": platform.system(),
                "os_release": platform.release(), "architecture": platform.machine(),
                "profiles": PROFILES, "seed": args.seed, "blocks": args.blocks,
                "requests_per_profile_per_block": 100, "warmups_per_profile": 5,
                "client_concurrency": 1, "connection_policy": "new TCP connection per attempt",
                "retries": 0, "socket_timeout_s": TIMEOUT_S,
                "useful_result_deadline_ms": DEADLINE_MS,
                "clock": time.get_clock_info("perf_counter").implementation,
                "benchmark_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "raw_sha256": hashlib.sha256((args.out / "attempts.jsonl").read_bytes()).hexdigest()}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
