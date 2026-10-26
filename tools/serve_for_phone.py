# -*- coding: utf-8 -*-
"""Serve the Sanctuary to a phone on the same network.

    python tools/serve_for_phone.py
    python tools/serve_for_phone.py --port 8501 --no-launch

Starts the ordinary Streamlit UI (`src/ui_app.py`) bound to every interface
instead of localhost, then prints the address the phone app asks for. The app is
a window onto this server, so everything the network UI has — Visit, Walk the
Land, the Gazette, the Map, the Galgame view, An Eternal Page, the Admin Console
and the Control Panel — is exactly what the phone gets.

LAN only, by design: no tunnel, no port-forward, nothing published. The login
gate in `src/ui_gate.py` still applies, with the operator account for the full
Console and Control Panel and the read-only visitor account for guests.
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "src" / "ui_app.py"


def lan_ip() -> str:
    """This machine's address on the local network (no packets are sent)."""
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("10.255.255.255", 1))
            return probe.getsockname()[0]
        finally:
            probe.close()
    except Exception:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Serve the Sanctuary to a phone.")
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--no-launch", action="store_true",
                    help="only print the address; do not start Streamlit")
    args = ap.parse_args(argv)

    if not APP.is_file():
        print(f"cannot find {APP}")
        return 1

    ip = lan_ip()
    url = f"http://{ip}:{args.port}"
    print()
    print("  Project Amphoreus — for the phone")
    print("  ------------------------------------------------")
    print(f"  Open on the phone:  {url}")
    print("  In the app, type exactly that address.")
    print()
    print("  The phone must be on the same Wi-Fi/LAN as this computer.")
    print("  First run may ask Windows to allow Python through the firewall —")
    print("  allow it for private networks. If it was blocked, as administrator:")
    print(f'    netsh advfirewall firewall add rule name="Amphoreus" '
          f"dir=in action=allow protocol=TCP localport={args.port}")
    print()
    print("  The login gate still applies: the operator account has the Admin")
    print("  Console and Control Panel; the visitor account is read-only.")
    print("  Nothing is published to the internet. Stop with Ctrl+C.")
    print()

    if args.no_launch:
        return 0

    cmd = [
        sys.executable, "-m", "streamlit", "run", str(APP),
        "--server.address", "0.0.0.0",
        "--server.port", str(args.port),
        "--server.headless", "true",
    ]
    try:
        return subprocess.call(cmd, cwd=str(ROOT))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
