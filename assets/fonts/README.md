# Fonts

No custom font files are bundled with this project. The UI relies on the Windows system
font stack (Segoe UI, with Tk's own fallback to a default sans-serif font if Segoe UI is
unavailable, e.g. on a non-Windows development machine).

See `src/fbcollector/ui/fonts.py` for the fallback resolution logic and
`src/fbcollector/ui/theme.py` for where the font family is applied.

If you want a custom brand font later, drop the `.ttf`/`.otf` files here, register them at
startup (e.g. via a small `ctypes.windll.gdi32.AddFontResourceExW` call on Windows), and
update `FONT_FAMILY` in `ui/theme.py`.
