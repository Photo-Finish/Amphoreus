# Amphoreus — website guide

How to reach the living Sanctuary from any device, what the addresses mean,
what happens when the network changes, and how to make the address permanent.

**Last updated:** 2026-08-16

---

## 1. The addresses

Two websites live on this computer:

| What | Address | Reachable from |
|---|---|---|
| **World-status page** (read-only) | published to `world_runtime/status_urls.txt` — a public `https://….trycloudflare.com` URL | anywhere with Internet |
| **The full Sanctuary UI** (all 7 tabs, can change the dialogue) | published to `world_runtime/status_urls.txt` and `world_runtime/ui_url.txt` — a **private** `https://….trycloudflare.com` URL | anywhere with Internet, **but only the operator knows it** (it is deliberately kept out of the GitHub repository) |
| Status page → full UI | same status page, path **`/app`** (embedded) | anywhere the status page is reachable |
| **LAN — status page** | `http://Lambda.local:8765` (constant) or `http://<current-ip>:8765` | same network, **no Internet / no VPN needed** |
| **LAN — full UI** | `http://Lambda.local:8501` (constant) or `http://<current-ip>:8501` | same network, no Internet / no VPN |

**The machine's hostname is `Lambda`**, so `Lambda.local` is the constant LAN
address that does not depend on the changing IP. Most phones/tablets/computers
resolve `Lambda.local` on the same Wi-Fi (mDNS); if one device cannot, use the
IP form instead (`http://192.168.1.15:8765` today).

> The current live URLs are always in `world_runtime/status_urls.txt`
> (gitignored — never committed). The status page also shows a **“Reach this
> world”** section listing the current public + LAN addresses.

## 2. What happens when the network changes or disconnects

### 2.1 Public URL (`….trycloudflare.com`)
- **Stable while the tunnel process is alive.** A brief Wi-Fi drop or a switch
  to another network does **NOT** change it — `cloudflared` reconnects to the
  *same* URL by itself.
- **It changes only when `cloudflared` is restarted**: computer reboot, a
  crash, or a manual restart. Then a **new random** URL is minted.
- Free quick tunnels always use random names (they cannot be named `amphoreus-…`).

### 2.2 LAN URL (`http://Lambda.local:…` / `http://192.168.1.15:…`)
- The **IP** form changes whenever the machine joins a different network
  (new IP). 
- The **`Lambda.local`** form stays the same on any network, as long as the
  device you view from is on the same LAN.

### 2.3 Disconnect from the Internet
- Nothing is reachable from outside while offline.
- On reconnection: if the tunnel process survived, the **same** public URL
  works again; if it died, the guard starts a fresh tunnel with a **new** URL
  (read it from `world_runtime/status_urls.txt` or via the LAN page).

### 2.4 What keeps it alive
`tools/status_guard.py` (runs hidden in the background) checks every 15
seconds and restarts anything that died — the status server, both tunnels,
and the URL files. It does **not** start or stop the Sanctuary UI itself.

## 3. How to use it

1. **Find the current public address** — open `world_runtime/status_urls.txt`
   on this computer (first line = status page, second = full UI), or open any
   LAN URL to see the “Reach this world” section.
2. **From any device with Internet** — open the public status URL. Click
   **“Enter the Sanctuary — the full interface”** (or go to `/app`) to use the
   complete UI embedded; or open the private UI URL directly in its own tab.
3. **From a device on the same Wi-Fi, without the Internet** — open
   `http://Lambda.local:8765` (status) or `http://Lambda.local:8501` (full UI).
4. **Use the UI** — the same tabs as on this computer: Visit an Heir, the
   Chronicle, the Map, the Galgame, Admin, Control Panel. Voice and RAG
   status show in the sidebar.

## 4. How to make the address permanent (recommended for a public world)

Free quick tunnels cannot keep a fixed name. To get a permanent, meaningful
address such as `amphoreus.yourdomain.com`:

1. Buy (or get free) any domain, and create a **free Cloudflare account** with
   that domain on it.
2. On this computer run `cloudflared tunnel login` (opens your browser once),
   then `cloudflared tunnel create amphoreus`.
3. Route a hostname: `cloudflared tunnel route dns amphoreus amphoreus.yourdomain.com`.
4. Replace the two quick tunnels in `tools/status_guard.py` with one named
   tunnel (`cloudflared tunnel run amphoreus` + an ingress rule forwarding
   `/app*` to 8765 and everything else to 8501 — the guard code is one edit
   away; ask the assistant to wire it).

From then on `https://amphoreus.yourdomain.com` is **constant for as long as
this computer is connected to the Internet**, across reboots and network
changes. (A cheap alternative on some ISPs: forward ports 8765/8501 on the
router — then `http://<your-public-ip>:8765` works directly.)

## 5. Security notes

- The **status page is read-only** — safe to share.
- The **full UI is not read-only**: whoever opens it can converse with the
  Heirs and use the Control Panel (change modes, the black tide, the mailbox).
  Its URL is random and unguessable, and it is **not published in the GitHub
  repository** — only the operator sees it. If you want a hard login so that
  *only you* can use the UI from anywhere, ask the assistant to add an access
  key to the app (it can be done).
- Where Cloudflare is blocked (some regions, e.g. parts of mainland China),
  the LAN URLs still work; for guaranteed public access there, use a local
  tunnel service (cpolar / natapp / openfrp — requires an account) pointed at
  `http://127.0.0.1:8765` / `:8501`.

## 6. Troubleshooting

| Symptom | What to do |
|---|---|
| The old public URL shows a Cloudflare error | Normal — the URL changed after a restart. Read the current one from `world_runtime/status_urls.txt`, or use the LAN URL. |
| `http://Lambda.local:…` does not load on a phone | The device lacks mDNS — use the IP form (`http://192.168.1.15:8765`). |
| The full UI shows “interface not running” | The Streamlit app (port 8501) is down — start it (the launcher, or ask the assistant) and the guard re-opens its tunnel. |
| The full UI loads but the chat won’t connect (WebSocket error) | Usually a first-load hiccup while the app boots — reload the page. |
| `Voice: Ready` but slow replies | gemma3:27b is the standard voice (~8 tok/s); switch to the fast voice in the Control Panel. |
| Nothing works from the Internet | The computer is offline, or Cloudflare is blocked in your region — use LAN, or see §4. |
