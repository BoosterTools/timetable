from __future__ import annotations

from pathlib import Path

from app.ui.canvas import TimetableCanvas


def export_canvas_to_image(
    canvas: TimetableCanvas, path: Path | str, width: int = 1600, quality: int = 92
) -> bool:
    """Renders the timetable at high resolution and saves it as JPG or PNG
    (inferred from the file extension; defaults to JPG). Returns False on
    any I/O failure rather than raising, so the caller can show a friendly
    message."""
    path = Path(path)
    height = canvas.natural_height_for_width(width)
    image = canvas.render_to_image(width=width, height=height)

    suffix = path.suffix.lower()
    if suffix == ".png":
        fmt, save_quality = "PNG", -1
    else:
        fmt, save_quality = "JPG", quality

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return bool(image.save(str(path), fmt, save_quality))
    except OSError:
        return False
