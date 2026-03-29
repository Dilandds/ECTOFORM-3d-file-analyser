

## Plan: Add Defensive Logging to Visual Style Menu (Windows Crash Fix)

### Problem
Clicking "Visual Style" crashes on Windows with no error. The likely culprits are:
1. **`_menu_diamond_px()`** — `QFontMetrics.horizontalAdvance()` was added in Qt 5.11; older PyQt5 builds may not have it, causing a silent crash
2. **`_load_parts_menu_pixmap()`** — `QImage.convertToFormat()` on a scaled pixmap could fail on Windows GPU drivers
3. **`_PartsMenuRow`** — `pix_lbl.setFixedSize(pm.size())` with a null/zero pixmap crashes layout
4. **`QPainter` in fallback** — painting on a 0-size pixmap can segfault

### Changes

**`ui/toolbar.py`** — Add try/except guards and logging throughout the Visual Style menu pipeline:

1. **`_menu_diamond_px()`** — Wrap in try/except, fall back to `11` if `horizontalAdvance` fails. Add `logger.debug`.

2. **`_load_parts_menu_pixmap(path)`** — Wrap the entire function in try/except returning empty `QPixmap()` on failure. Log each step (load, scale, convert). Guard against zero-size pixmaps.

3. **`_parts_menu_pixmap_fallback(size)`** — Guard against `size <= 0`. Wrap `QPainter` block in try/except.

4. **`_PartsMenuRow.__init__`** — After getting pixmap, check `pm.isNull()` before `setFixedSize`. Log the pixmap state.

5. **`_show_render_mode_menu()`** — Wrap the entire method body in try/except with `logger.error(... exc_info=True)` so any crash is logged instead of silently killing the app.

### Technical Details
- All guards use `logger.warning/error` so issues appear in `app_debug.log`
- No functional changes — just defensive wrapping and logging
- The `horizontalAdvance` compatibility fix (fallback to `width()`) addresses a known PyQt5 version issue on some Windows installs

