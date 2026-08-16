#!/usr/bin/env python3
"""tools/status_guard.py — keep the world website online, no VPN needed.

Supervises (self-healing, runs forever):
  1. the world-status server (tools/world_status_server.py) on 0.0.0.0:8765
  2. a Cloudflare quick tunnel -> https://....trycloudflare.com (status page)
  3. when the full Sanctuary UI (Streamlit, port 8501) is running, a second
     Cloudflare quick tunnel -> public URL for the complete interface; it is
     also embedded on the status site's /app subpage.

Every few seconds it writes world_runtime/status_urls.txt (status public,
UI public, then LAN URLs), world_runtime/ui_url.txt (public UI URL for the
/app iframe) and world_runtime/status_urls.json (structured), so any terminal
can pick a reachable URL. Terminals on the same LAN can just use the LAN URLs
(no Internet, no VPN). For regions where Cloudflare is blocked, open the ports
on the router for direct access, or point any tunnel service at
http://127.0.0.1:8765 / :8501 and add it to the tunnels below.

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
PORT = 8765          # world-status website
UI_PORT = 8501       # full Sanctuary UI (Streamlit)
URLS_TXT = ROOT / "world_runtime" / "status_urls.txt"
URLS_JSON = ROOT / "world_runtime" / "status_urls.json"
UI_URL_TXT = ROOT / "world_runtime" / "ui_url.txt"
CF = ROOT / "world_runtime" / "cloudflared.exe"
GHIO_CFG = ROOT / "world_runtime" / "ghio_config.json"
GHIO_DIR = ROOT / "world_runtime" / "ghio"
FRONTDOOR_TPL = ROOT / "tools" / "frontdoor_template.html"

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


def lan_urls(port):
    out = []
    # mDNS form is CONSTANT across IP changes on the same LAN (e.g.
    # http://Lambda.local:8765) — put it first so it is the preferred LAN URL.
    try:
        host = socket.gethostname()
        if host:
            out.append(f"http://{host}.local:{port}")
    except Exception:
        pass
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-NetIPAddress -AddressFamily IPv4 | "
                            "Where-Object { $_.IPAddress -notmatch '^127|^169|^192\\.168\\.(60|254)\\.' } | "
                            "Select-Object -ExpandProperty IPAddress"],
                           capture_output=True, text=True, timeout=20)
        for ip in (r.stdout or "").split():
            ip = ip.strip()
            if ip:
                out.append(f"http://{ip}:{port}")
    except Exception:
        pass
    return out or [f"http://127.0.0.1:{port}"]


def write_urls(status_tunnels, ui_tunnels):
    pub_status = [t.url for t in status_tunnels if t.url]
    pub_ui = [t.url for t in ui_tunnels if t.url]
    lan = lan_urls(PORT)
    lan_ui = lan_urls(UI_PORT)
    data = {
        "updated": now(),
        "status": {"port": PORT, "server_up": port_open(PORT),
                   "public": pub_status, "lan": lan},
        "ui": {"port": UI_PORT, "server_up": port_open(UI_PORT),
               "public": pub_ui, "lan": lan_ui},
    }
    try:
        txt_lines = pub_status + pub_ui
        txt_lines += [f"(LAN: {u})" for u in lan]
        txt_lines += [f"(UI LAN: {u})" for u in lan_ui]
        URLS_TXT.write_text("\n".join(txt_lines), encoding="utf-8")
        UI_URL_TXT.write_text("\n".join(pub_ui), encoding="utf-8")
        URLS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    except Exception as e:
        print(f"[guard] {now()} write failed: {e}")


def make_cloudflare(cf, port, name):
    return Tunnel(name,
                  [str(cf), "tunnel", "--no-autoupdate", "--url",
                   f"http://127.0.0.1:{port}"],
                  re.compile(r"https://([a-z0-9-]+\.trycloudflare\.com)"))


class FrontDoor:
    """Keeps the eternal github.io page pointing at the live tunnel.

    Reads world_runtime/ghio_config.json (gitignored): {enabled, repo}.
    When the public URLs change, it regenerates config.js + index.html in a
    local clone of the github.io repo and pushes (in a background thread).
    """

    def __init__(self):
        self.enabled = False
        self.repo = None
        self.last = None
        try:
            cfg = json.loads(GHIO_CFG.read_text(encoding="utf-8"))
            if cfg.get("enabled") and cfg.get("repo"):
                self.repo = cfg["repo"]
                self.enabled = True
        except Exception:
            pass

    def ensure_clone(self):
        if (GHIO_DIR / ".git").exists():
            return True
        try:
            GHIO_DIR.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", self.repo, str(GHIO_DIR)],
                           capture_output=True, text=True, timeout=180,
                           cwd=str(ROOT))
            return (GHIO_DIR / ".git").exists()
        except Exception as e:
            print(f"[guard] {now()} ghio clone failed: {e}")
            return False

    def update(self, status_url, ui_url):
        if not self.enabled or not (status_url and ui_url):
            return
        key = (status_url, ui_url)
        if key == self.last:
            return
        self.last = key
        threading.Thread(target=self._push, args=key, daemon=True).start()

    def _push(self, status_url, ui_url):
        try:
            if not self.ensure_clone():
                return
            cfg_js = {"status": status_url, "ui": ui_url, "updated": now()}
            (GHIO_DIR / "config.js").write_text(
                "window.AMPHOREUS = " +
                json.dumps(cfg_js, ensure_ascii=False) + ";\n",
                encoding="utf-8")
            if FRONTDOOR_TPL.exists():
                (GHIO_DIR / "index.html").write_text(
                    FRONTDOOR_TPL.read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=str(GHIO_DIR),
                           capture_output=True, text=True, timeout=60)
            subprocess.run(["git", "-c", "user.email=guard@amphoreus.local",
                            "-c", "user.name=Amphoreus Guard",
                            "commit", "-m", f"front door -> {status_url}"],
                           cwd=str(GHIO_DIR), capture_output=True, text=True,
                           timeout=60)
            for _ in range(3):
                r = subprocess.run(["git", "push", "origin", "main"],
                                   cwd=str(GHIO_DIR), capture_output=True,
                                   text=True, timeout=180)
                if r.returncode == 0:
                    print(f"[guard] {now()} front door updated ({status_url})")
                    return
                time.sleep(8)
            print(f"[guard] {now()} front door push failed")
        except Exception as e:
            print(f"[guard] {now()} ghio update failed: {e}")


def main():
    print(f"[guard] {now()} world website guard up (status {PORT}, UI {UI_PORT})")
    cf = ensure_cloudflared()
    status_tunnels = []
    ui_tunnels = []
    if cf:
        status_tunnels.append(make_cloudflare(cf, PORT, "cloudflared-status"))
    front = FrontDoor()
    if front.enabled:
        print(f"[guard] {now()} eternal front door enabled ({front.repo})")

    for t in status_tunnels:
        t.ensure()

    try:
        while True:
            ensure_server()
            for t in status_tunnels:
                t.ensure()
            if port_open(UI_PORT):
                if cf and not ui_tunnels:
                    print(f"[guard] {now()} UI (port {UI_PORT}) is up; "
                          "opening a tunnel for it")
                    ui_tunnels.append(make_cloudflare(cf, UI_PORT, "cloudflared-ui"))
                for t in ui_tunnels:
                    t.ensure()
            elif ui_tunnels:
                print(f"[guard] {now()} UI (port {UI_PORT}) is down; "
                      "its tunnel stays but is not advertised")
            write_urls(status_tunnels, ui_tunnels)
            pub_status = ""
            pub_ui = ""
            try:
                lines = URLS_TXT.read_text(encoding="utf-8").splitlines()
                pub_status = next((l.strip() for l in lines
                                   if l.strip().startswith("https")), "")
                ui_lines = UI_URL_TXT.read_text(encoding="utf-8").splitlines()
                pub_ui = next((l.strip() for l in ui_lines
                               if l.strip().startswith("https")), "")
            except Exception:
                pass
            front.update(pub_status, pub_ui)
            time.sleep(15)
    except KeyboardInterrupt:
        print("[guard] stopping")


if __name__ == "__main__":
    main()
