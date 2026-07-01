# Sounds

No winning-sound audio asset is bundled (per project scope decision - placeholder/no-op
sound hook rather than a real audio file). `ui/wheel_window.py` does not attempt to play
audio; the visual confetti/particle celebration (see
`src/fbcollector/services/wheel/confetti.py`) stands in for it.

To add a real winning sound later:
1. Drop a `.wav` file here (e.g. `win.wav`).
2. In `WheelWindow._on_spin_complete`, call `winsound.PlaySound(str(path), winsound.SND_ASYNC)`
   (stdlib `winsound`, Windows-only, non-blocking) guarded by a `try/except` in case the
   file is missing, so a missing asset never crashes the draw.
