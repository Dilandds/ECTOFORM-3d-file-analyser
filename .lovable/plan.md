

# Plan: Arrow Manipulator Control Panel

## Overview

Replace the current "click-to-place + drag-to-rotate" arrow behavior with a proper control panel workflow. Users click on the model surface to place an arrow, then use a dedicated control panel (similar to the annotation panel) to select, rotate, resize, and move arrows using buttons. Free-space clicks allow normal camera orbit.

## Design

### Arrow Control Panel (`ui/arrow_panel.py` — New File)

A right-side panel (like `AnnotationPanel`) that appears when arrow mode is active. Contains:

- **Arrow list**: Scrollable list of placed arrows (Arrow 1, Arrow 2, ...) with select/delete buttons per row
- **Selected arrow controls** (enabled when an arrow is selected):
  - **Rotation**: 6 buttons — Rotate Left/Right (around Y), Rotate Up/Down (around X), Tilt CW/CCW (around Z). Each click rotates by a fixed increment (e.g. 15°).
  - **Size**: Two buttons — Lengthen (+) / Shorten (−). Each click scales by ~10%.
  - **Move**: 6 buttons — Move along X+/X−, Y+/Y−, Z+/Z− (move the arrow base position in world space by a small increment relative to model size).
  - **Color picker**: Small color swatch button to change selected arrow's color.
- **Bottom actions**: "Clear All" and "Undo Last" buttons.

### Changes to `viewer_widget_pygfx.py`

- **Remove drag-to-orient on place**: After placing an arrow, don't capture drag. Arrow is placed with surface normal direction, user adjusts via panel buttons.
- **Add methods**: `rotate_arrow(arrow_id, axis, angle_deg)`, `scale_arrow(arrow_id, factor)`, `move_arrow(arrow_id, dx, dy, dz)`, `set_arrow_color(arrow_id, color)`, `get_arrow_list()` (returns list of {id, point, direction, length_factor}).
- Keep existing `remove_arrow`, `clear_all_arrows`, `undo_last_arrow`.

### Changes to `stl_viewer.py`

- Import and instantiate `ArrowPanel` per tab (similar to `AnnotationPanel`).
- Add `ArrowPanel` to a stack in `right_panel_stack` (or reuse `annotation_stack` pattern).
- When arrow mode is toggled on, show the arrow panel; when toggled off, hide it.
- Wire panel signals to viewer methods.
- Add `arrow_panel` to `TabState`.

### Changes to `ui/toolbar.py`

- No structural changes needed. The existing dropdown menu item "3D Arrow" continues to toggle arrow mode.

## Files

| Action | File |
|--------|------|
| Create | `ui/arrow_panel.py` |
| Modify | `viewer_widget_pygfx.py` — add manipulation methods, remove drag-to-orient |
| Modify | `stl_viewer.py` — wire arrow panel into tab system |

