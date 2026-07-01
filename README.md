# Facebook Live Collector Pro — Enterprise Edition

A Windows desktop app that attaches to a Chrome tab showing a Facebook Live video,
captures comments in real time, shows them in a live dashboard, exports CSV files
(raw comments / unique users / employee IDs), and includes a full-screen animated
Lucky Wheel for prize draws.

## ⚠️ Important caveat: Facebook selector accuracy

Facebook's Live-comment DOM is obfuscated and changes without notice, and this project
was built without access to a live Facebook page to verify against. All DOM selectors
used to locate comments live in **`config/selectors.json`** (seeded from
`config/selectors.default.json` on first run) and are **hot-reloadable from
Settings → Selectors** — no app restart required.

**If comment detection stops working:**
1. Open your Facebook Live page in Chrome, press F12 to open DevTools.
2. Inspect a comment element and note its structure (container, username link, text).
3. Open Settings → Selectors in the app, edit the JSON, click **Reload Selectors**.

The rest of the pipeline (storage, dashboard, CSV export, reconnect, Lucky Wheel) does
not depend on Facebook's markup and is unaffected by DOM drift.

## Requirements

- Windows 10/11
- Python 3.12+
- Google Chrome installed
- (Dev only) [Playwright](https://playwright.dev/python/) — no `playwright install` is
  required for normal use, since the app only ever attaches to a real installed Chrome
  via CDP (`connect_over_cdp`), never launches Playwright's own bundled browser.

## Getting started (development)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python main.py
```

## How it works

1. Press **CONNECT**. The app launches its own managed Chrome window (a dedicated
   temporary profile, so it won't conflict with your everyday Chrome session).
2. Open/keep your Facebook Live video in that window.
3. The app attaches via Playwright's Chrome DevTools Protocol connection, detects the
   page, and starts polling for new comments every 300ms.
4. Comments stream into the dashboard, get deduplicated, and are auto-saved to CSV every
   5 seconds (configurable).
5. Use **Lucky Wheel** to import `UniqueUsers.csv` or `EmployeeIDs.csv` and run a prize
   draw with winner history.

See `master-prompt.md` for the full original specification this app implements.

## Project layout

```
main.py                    entry point
src/fbcollector/
  app.py                   bootstrap: wires QueueBus, services, MainWindow
  core/                    queues, events, thread_manager, session (service layer)
  services/
    facebook/               Chrome manager, CDP connector, selectors, extractor, collector
    storage/                SQLite connection, models, repositories, writer thread
    export/                 CSV writer (autosave, atomic writes), export thread
    wheel/                  wheel physics, confetti, wheel session/worker
    settings_service.py
  ui/                       CustomTkinter main window + components, wheel window
  utils/                    hashing, employee ID regex extraction, logging, paths, perf
config/                     default settings.json / selectors.json (seeded on first run)
assets/                     generated icons, font/sound placeholder notes
scripts/                    generate_assets.py, build_exe.py
packaging/                  fbcollector.spec (PyInstaller), installer.iss (Inno Setup)
samples/                    example CSV outputs
tests/                      pytest suite (no live Chrome/Facebook required, except one
                             optional test that needs a local Playwright Chromium)
```

## Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

All tests run without a live Chrome/Facebook connection. One test
(`tests/test_comment_extractor.py`) additionally exercises the DOM-parsing logic against
a hand-written static HTML fixture using a real (headless) Chromium instance if
Playwright's browser is installed (`playwright install chromium`); it skips automatically
if that browser isn't available.

## Building the EXE

```bash
pip install -r requirements-dev.txt
python scripts/build_exe.py
```

Produces `dist/FBLiveCollectorPro.exe` (onefile). Then, optionally, build the installer
with [Inno Setup](https://jrsoftware.org/isinfo.php):

```bash
ISCC.exe packaging\installer.iss
```

Produces `dist/installer/FBLiveCollectorPro-Setup.exe`.

## Settings

Available from the gear icon in the top navigation bar:

- **General** — theme, language, animation speed
- **Collector** — employee ID regex (with a live test box), default `\b\d{4,10}\b`
- **Storage** — CSV export folder, autosave interval
- **Selectors** — the Facebook DOM selector JSON (see caveat above), with Reset/Reload

## Known limitations

- Facebook selector accuracy is unverified against a live page (see caveat above).
- The 100,000+ comment performance target is validated via synthetic load (a virtualized,
  fixed-size recycled widget pool in the live feed, batched SQLite writes), not an actual
  100k-comment live broadcast.
- No custom brand icon/font/sound assets were supplied; placeholders are generated
  programmatically (`scripts/generate_assets.py`) and can be swapped later.
