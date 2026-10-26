# Amphoreus on the phone

A small Android shell that opens the Sanctuary's own server on your local network.
It is **a window, not a second copy of the world**: every screen and every
administrator command the network UI has is available unchanged — Visit, Walk the
Land, the Gazette, the Map of Amphoreus, the Galgame view, An Eternal Page, the
**Admin Console** and the **Control Panel** — because the app loads the real
Streamlit UI. Nothing is reimplemented, nothing is cached, and no character data
lives on the phone.

```
android/
  app/                     the app: one Activity, a manifest, a strings file, an icon
  build_apk.ps1            builds and signs dist/Amphoreus.apk (no Gradle)
  make_icon.py             redraws the launcher icon from the project's palette
  dist/Amphoreus.apk       build output (gitignored)
```

## Build it

Needs a JDK 17+ and Windows PowerShell. Nothing else — the script fetches the
three SDK pieces it needs (aapt2, d8, apksigner, android.jar) into `android/.sdk`
on first run.

```powershell
pwsh -File android/build_apk.ps1
# → android/dist/Amphoreus.apk   (~29 KB)
```

`-Clean` rebuilds from scratch; the SDK download is kept.

## Install it

```powershell
adb install -r android\dist\Amphoreus.apk
```

Or copy `dist\Amphoreus.apk` to the phone (USB, cloud, chat) and open it, allowing
"install unknown apps" for whatever app you opened it from. The APK is signed with
a local key in `android/.keys/` — self-signed, which is all a side-loaded app
needs.

## Serve the world

On the computer, on the same Wi-Fi/LAN:

```powershell
python tools/serve_for_phone.py
```

It binds Streamlit to every interface and prints the address to type into the app,
for example `http://10.207.118.84:8501`. On first run Windows may ask whether to
allow Python through the firewall — allow it for **private** networks. If it was
already blocked, run the `netsh` line the script prints, as administrator.

## Use it

1. Open **Amphoreus**. The first screen asks for the address — the one the script
   printed. It is remembered.
2. Sign in with the operator account for the full Console and Control Panel, or
   the visitor account for the read-only view. The gate is the server's own
   (`world_runtime/ui_auth.json`); the app stores no credentials.
3. Everything behaves as in a browser, plus what a phone needs:
   - **back** steps through the app's history, then leaves;
   - **⚙** (top-right) reloads, changes the server address, or opens the same page
     in the system browser;
   - the **file picker** hands pictures, music and video to the senses;
   - the **microphone** button is granted the first time, so the Heirs can hear;
   - if the server is not answering, a plain screen says so and offers *Try again*
     or *Change the address* — no blank page.

## What it is not

- **Not a public app.** LAN only. No tunnel, no port-forward, and the app talks to
  exactly one address you give it.
- **Not a data collector.** No analytics, no accounts, no background service. The
  app holds one setting: the server address.
- **Not a distinct experience.** If a tab is added to the UI, it appears here with
  no app change; if the UI is unreachable, the app says so.

## Security notes worth knowing

- `android:usesCleartextTraffic="true"` is deliberate: the server is plain
  `http://` on a private network, and Android would otherwise refuse it. Anything
  sensitive is still behind the login gate; keep the app on trusted networks.
- Permissions are only what the job needs: `INTERNET` (a LAN socket needs it),
  `ACCESS_NETWORK_STATE`, `RECORD_AUDIO` for speech. Nothing else is requested,
  and nothing is read from the phone's storage beyond the file you pick.
- The signing key is local and gitignored. Losing it only means uninstalling
  before installing a build signed with a new one.

## Build notes (for whoever touches this next)

- **No Gradle.** The build is `aapt2 → javac → d8 → zipalign → apksigner`, which
  keeps it reproducible with just a JDK and three SDK archives.
- **build-tools 36.1 is pinned on purpose.** D8 from build-tools 34 (R8 8.2.2)
  crashes with `NullPointerException: String.length()` on *any* anonymous inner
  class produced by a JDK 24 `javac` — and a `WebViewClient` subclass is exactly
  that. Upgrading the JDK is not the fix; keeping a current build-tools is.
- The app is framework-only (no AndroidX), so there is no dependency resolution
  and the dex stays tiny.
- `minSdkVersion 24` (Android 7), `targetSdkVersion 34`.

## How this was checked

- `aapt2 dump badging` on the built APK: package `com.amphoreus.sanctuary`, the
  launcher activity, the three permissions, the icon, minSdk 24 / target 34.
- `apksigner verify`: v2 and v3 signatures valid.
- The server side the app talks to was driven for real over the **LAN address**
  (not localhost) with Chromium: `tools/validate_live_page.py --url
  http://<lan-ip>:<port>` — 10 checks, including that the **Admin Console** and
  **Control Panel** open in the same session.
- Not yet run on a physical handset (no device or emulator on this machine), so
  the first install is yours; the manifest and the server it loads are verified.
