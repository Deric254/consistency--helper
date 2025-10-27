"""Normalize outreach images non-destructively.

Behaviors:
- Scans images/teaching_leads and images/analytics_leads for files named
  N.png, N.jpeg, N.jpg (numeric filenames).
- Copies numeric files to dayN.png (does not delete originals).
- If Pillow is available and a source is jpeg/jpg, also converts it to PNG
  and writes dayN.png while keeping the original jpeg.
- Reports actions and remaining missing day files.

This script is safe to run from the GUI or terminal.
"""
from pathlib import Path
import re
import shutil
import sys

try:
    from PIL import Image
    HAS_PILLOW = True
except Exception:
    HAS_PILLOW = False


INTENTS = {
    "teachingleads": "images/teaching_leads",
    "analyticsleads": "images/analytics_leads",
}


def normalize_images(base_path='.'):
    base = Path(base_path)
    summary = {"copied": [], "converted": [], "skipped": [], "errors": [], "missing": {}}

    for intent, rel in INTENTS.items():
        folder = (base / rel)
        if not folder.exists():
            summary["errors"].append(f"Missing folder: {folder}")
            # mark all days missing
            summary["missing"][intent] = [f"day{n}.png" for n in range(1, 8)]
            continue

        # find numeric files like 1.png, 2.jpeg, etc.
        for p in folder.iterdir():
            if not p.is_file():
                continue
            m = re.match(r"^(\d+)\.(png|jpe?g)$", p.name, re.I)
            if not m:
                continue

            n = int(m.group(1))
            ext = m.group(2).lower()
            target = folder / f"day{n}.png"

            if target.exists():
                summary["skipped"].append(str(target))
                continue

            try:
                if ext in ("jpeg", "jpg") and HAS_PILLOW:
                    # convert to PNG, keep original
                    img = Image.open(p)
                    img.save(target)
                    summary["converted"].append(f"{p.name} -> {target.name}")
                else:
                    # copy the file to the dayN name (keeps original extension if png)
                    shutil.copy2(p, target)
                    summary["copied"].append(f"{p.name} -> {target.name}")
            except Exception as e:
                summary["errors"].append(f"{p}: {e}")

        # after processing, list missing dayN.png files
        missing = []
        for n in range(1, 8):
            if not (folder / f"day{n}.png").exists():
                missing.append(f"day{n}.png")
        summary["missing"][intent] = missing

    return summary


def pretty_print(summary):
    out = []
    out.append("Normalization summary:\n")
    if summary["copied"]:
        out.append("Copied files:")
        out.extend([f"  - {s}" for s in summary["copied"]])
    if summary["converted"]:
        out.append("Converted files (jpeg->png):")
        out.extend([f"  - {s}" for s in summary["converted"]])
    if summary["skipped"]:
        out.append("Skipped (targets already exist):")
        out.extend([f"  - {s}" for s in summary["skipped"]])
    if summary["errors"]:
        out.append("Errors:")
        out.extend([f"  - {s}" for s in summary["errors"]])

    out.append("\nMissing day files by intent:")
    for intent, missing in summary["missing"].items():
        out.append(f"  {intent}:")
        if missing:
            out.extend([f"    - {m}" for m in missing])
        else:
            out.append("    - (none)")

    if not HAS_PILLOW:
        out.append("\nNote: Pillow not installed. JPEG files were copied but not converted.\nTo enable conversion: pip install Pillow")

    return "\n".join(out)


if __name__ == '__main__':
    summary = normalize_images('.')
    print(pretty_print(summary))
    # exit code non-zero if there are errors
    sys.exit(1 if summary["errors"] else 0)
