#!/usr/bin/env python3
"""tools/status_guard.py — keep the world-status website online, no VPN needed.

Supervises (self-healing, runs forever):
  1. the world-status server (tools/world_status_server.py) on 0.0.0.0:8765
  2. a Cloudflare quick tunnel -> https://....trycloudflare.com (public URL)

Every few seconds it writes world_runtime/status_urls.txt (public URL first,
then the LAN URL) and world_runtime/status_urls.json (structured), so any
terminal can pick a reachable URL. Terminals on the same LAN can just use the
LAN URL (no Internet, no VPN). For regions where Cloudflare is blocked, open
port 8765 on the router for direct access, or point any tunnel service at
http://127.0.0.1:8765 and add it to the `tunnels` list below.

Usage:  python tools/status_guard.py
"""

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
URLS_TXT = ROOT / "world_runtime" / "status_urls.txt"
URLS_JSON = ROOT / "world_runtime" / "status_urls.json"
CF = ROOT / "world_runtime" / "cloudflared.exe"

CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def now():
    return datetime.now().isoformat(timespec="seconds")


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def ensure_server():
    if port_open(PORT):
        return True
    try:
        subprocess.Popen(
            [sys.executable, str(ROOT / "tools" / "world_status_server.py"),
             "--port", str(PORT), "--no-banner"],
            cwd=str(ROOT), creationflags=CREATION_FLAGS)
        print(f"[guard] {now()} restarted the status server")
        time.sleep(3)
        return port_open(PORT)
    except Exception as e:
        print(f"[guard] {now()} could not start the server: {e}")
        return False


def ensure_cloudflared():
    if CF.exists():
        return CF
    try:
        print("[guard] downloading cloudflared...")
        urllib.request.urlretrieve(
            "https://gh-proxy.com/https://github.com/cloudflare/cloudflared/"
            "releases/latest/download/cloudflared-windows-amd64.exe", CF)
        return CF
    except Exception as e:
        print(f"[guard] cloudflared download failed: {e}")
        return None


class Tunnel:
    """One persistent public tunnel; restarts itself when it dies."""

    def __init__(self, name, args, url_re):
        self.name = name
        self.args = args
        self.url_re = url_re
        self.proc = None
        self.url = None
        self._lock = threading.Lock()

    def start(self):
        self.proc = subprocess.Popen(
            self.args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            creationflags=CREATION_FLAGS)
        print(f"[guard] {now()} started {self.name} (pid {self.proc.pid})")
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while self.proc is not None:
            try:
                line = self.proc.stdout.readline()
            except Exception:
                break
            if not line:
                break
            m = self.url_re.search(line)
            if m:
                url = "https://" + m.group(1)
                with self._lock:
                    if url != self.url:
                        self.url = url
                        print(f"[guard] {now()} {self.name} URL: {url}")

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def ensure(self):
        if self.alive():
            return
        if self.proc is not None:
            print(f"[guard] {now()} {self.name} died; restarting")
        try:
            self.start()
        except Exception as e:
            print(f"[guard] {now()} {self.name} failed to start: {e}")
            self.proc = None


def lan_urls():
    out = []
    try:
        import subprocess as sp
        r = sp.run(["powershell", "-NoProfile", "-Command",
                    "Get-NetIPAddress -AddressFamily IPv4 | "
                    "Where-Object { $_.IPAddress -notmatch '^127|^169|^192\\.168\\.(60|254)\\.' } | "
                    "Select-Object -ExpandProperty IPAddress"],
                   capture_output=True, text=True, timeout=20)
        for ip in (r.stdout or "").split():
            ip = ip.strip()
            if ip:
                out.append(f"http://{ip}:{PORT}")
    except Exception:
        pass
    return out or [f"http://127.0.0.1:{PORT}"]


def write_urls(tunnels):
    public = [t.url for t in tunnels if t.url]
    data = {
        "updated": now(),
        "port": PORT,
        "server_up": port_open(PORT),
        "public": public,
        "lan": lan_urls(),
    }
    try:
        URLS_TXT.write_text(
            "\n".join(public + [f"(LAN: {u})" for u in data["lan"]]),
            encoding="utf-8")
        URLS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    except Exception as e:
        print(f"[guard] {now()} write failed: {e}")


def main():
    print(f"[guard] {now()} world-status guard up (port {PORT})")
    cf = ensure_cloudflared()
    tunnels = []
    if cf:
        tunnels.append(Tunnel(
            "cloudflared",
            [str(cf), "tunnel", "--no-autoupdate", "--url",
             f"http://127.0.0.1:{PORT}"],
            re.compile(r"https://([a-z0-9-]+\.trycloudflare\.com)")))

    for t in tunnels:
        t.ensure()

    try:
        while True:
            ensure_server()
            for t in tunnels:
                t.ensure()
            write_urls(tunnels)
            time.sleep(15)
    except KeyboardInterrupt:
        print("[guard] stopping")


if __name__ == "__main__":
    main()
