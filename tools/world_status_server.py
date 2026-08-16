"""tools/world_status_server.py — a read-only world-status website.

Serves a clean status page (and JSON API) on 0.0.0.0, so other terminals on
the LAN can open it; with --tunnel it also opens a Cloudflare quick tunnel,
giving a public https:// URL that works from anywhere on the Internet.

Endpoints:
  /            HTML status page (auto-refreshes every 30 s)
  /api/status  JSON snapshot
  /healthz     ok

Usage:
  python tools/world_status_server.py [--port 8765] [--tunnel]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.world_status import world_status, status_html, ui_page, public_ui_url  # noqa: E402

PORT = 8765
STATUS_URL_FILE = ROOT / "world_runtime" / "status_url.txt"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            self._send(200, "text/plain; charset=utf-8", "ok")
        elif path == "/api/status":
            st = world_status()
            body = json.dumps(st, ensure_ascii=False, indent=2)
            self._send(200, "application/json; charset=utf-8", body)
        elif path in ("/app", "/ui"):
            host = (self.headers.get("Host") or "").split(":")[0]
            if host and not host.startswith(("trycloudflare", "localhost", "127.")):
                lan = f"http://{host}:8501"
            else:
                lan = ""
            self._send(200, "text/html; charset=utf-8",
                       ui_page(public_ui_url(), lan))
        else:
            try:
                body = status_html(world_status())
            except Exception as e:
                body = f"<pre>status unavailable: {e}</pre>"
            self._send(200, "text/html; charset=utf-8", body)

    def _send(self, code: int, ctype: str, body: str):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(data)
        except Exception:
            pass

    def log_message(self, *args):
        pass


def cloudflared_path() -> Path:
    p = ROOT / "world_runtime" / "cloudflared.exe"
    if p.exists():
        return p
    return Path(os.environ.get("CLOUDFLARED", "cloudflared"))


def download_cloudflared() -> Path:
    """Fetch the Windows amd64 cloudflared (via gh-proxy fast path)."""
    dest = ROOT / "world_runtime" / "cloudflared.exe"
    if dest.exists():
        return dest
    urls = [
        "https://gh-proxy.com/https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    ]
    import urllib.request
    for url in urls:
        try:
            print(f"  downloading cloudflared from {url[:60]}...")
            urllib.request.urlretrieve(url, dest)
            if dest.stat().st_size > 1_000_000:
                print(f"  ok ({dest.stat().st_size // 1_000_000} MB)")
                return dest
        except Exception as e:
            print(f"  ! {e}")
    raise RuntimeError("could not download cloudflared")


def run_tunnel(port: int):
    """Open a Cloudflare quick tunnel; write the public URL to a file."""
    try:
        exe = download_cloudflared()
    except Exception as e:
        print(f"TUNNEL FAILED: {e}")
        return
    print("  starting Cloudflare quick tunnel...")
    proc = subprocess.Popen(
        [str(exe), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        errors="replace",
    )
    url = None
    deadline = time.time() + 60
    # the URL line looks like: https://xxxx.trycloudflare.com
    while time.time() < deadline and url is None:
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.2)
            continue
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            url = m.group(0)
        if "trycloudflare" in line:
            print(f"  {line.strip()}")
    if url:
        STATUS_URL_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_URL_FILE.write_text(url + "\n", encoding="utf-8")
        print(f"  PUBLIC URL: {url}")
        print(f"  saved to: {STATUS_URL_FILE}")
        print("  (keep this process running; Ctrl+C to close the tunnel)")
    else:
        print("  tunnel started but the public URL did not appear in time; "
              "see world_runtime/status_url.txt after a moment.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--tunnel", action="store_true",
                    help="also open a public Cloudflare quick tunnel")
    ap.add_argument("--no-banner", action="store_true")
    args = ap.parse_args()

    if not args.no_banner:
        print(f"World-status server on http://0.0.0.0:{args.port} "
              "(localhost: http://127.0.0.1:{args.port})")

    if args.tunnel:
        threading.Thread(target=run_tunnel, args=(args.port,), daemon=True).start()

    srv = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
