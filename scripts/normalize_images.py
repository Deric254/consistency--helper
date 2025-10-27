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


def autofill_images(base_path='.', duplicate_last=True):
    """Automatically map existing numeric images to day1..day7.

    Rules:
    - Find numeric files (N.png, N.jpg, N.jpeg) in each intent folder.
    - Sort by numeric value and map the first file to day1, second to day2, etc.
    - If fewer than 7 files, duplicate the last available file to fill remaining days
      when `duplicate_last` is True. All operations are non-destructive (copy only).
    """
    base = Path(base_path)
    report = {"copied": [], "converted": [], "errors": [], "missing": {}}

    for intent, rel in INTENTS.items():
        folder = base / rel
        if not folder.exists():
            report["errors"].append(f"Missing folder: {folder}")
            report["missing"][intent] = [f"day{n}.png" for n in range(1, 8)]
            continue

        # collect numeric files
        numeric_files = []
        for p in folder.iterdir():
            if not p.is_file():
                continue
            m = re.match(r"^(\d+)\.(png|jpe?g)$", p.name, re.I)
            if m:
                numeric_files.append((int(m.group(1)), p))

        numeric_files.sort(key=lambda x: x[0])
        if not numeric_files:
            report["missing"][intent] = [f"day{n}.png" for n in range(1, 8)]
            continue

        # map existing files to day1..n
        mapped_targets = []
        for idx, (_, src) in enumerate(numeric_files[:7], start=1):
            target = folder / f"day{idx}.png"
            try:
                if src.suffix.lower() in ('.jpeg', '.jpg') and HAS_PILLOW:
                    img = Image.open(src)
                    img.save(target)
                    report['converted'].append(f"{src.name} -> {target.name}")
                else:
                    shutil.copy2(src, target)
                    report['copied'].append(f"{src.name} -> {target.name}")
                mapped_targets.append(target)
            except Exception as e:
                report['errors'].append(f"{src}: {e}")

        # if fewer than 7, duplicate the last mapped target to fill remaining
        if duplicate_last and mapped_targets:
            last = mapped_targets[-1]
            for idx in range(len(mapped_targets) + 1, 8):
                target = folder / f"day{idx}.png"
                try:
                    shutil.copy2(last, target)
                    report['copied'].append(f"{last.name} -> {target.name} (dup)")
                except Exception as e:
                    report['errors'].append(f"{last} -> {target}: {e}")

        # finally report missing (should be none if duplication used)
        missing = []
        for n in range(1, 8):
            if not (folder / f"day{n}.png").exists():
                missing.append(f"day{n}.png")
        report['missing'][intent] = missing

    return report


def pretty_print(summary):
    out = []
    out.append("Normalization summary:\n")
    # support reports from both normalize_images() and autofill_images()
    copied = summary.get("copied", [])
    converted = summary.get("converted", [])
    skipped = summary.get("skipped", [])
    errors = summary.get("errors", [])

    if copied:
        out.append("Copied files:")
        out.extend([f"  - {s}" for s in copied])
    if converted:
        out.append("Converted files (jpeg->png):")
        out.extend([f"  - {s}" for s in converted])
    if skipped:
        out.append("Skipped (targets already exist):")
        out.extend([f"  - {s}" for s in skipped])
    if errors:
        out.append("Errors:")
        out.extend([f"  - {s}" for s in errors])

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
    import argparse

    parser = argparse.ArgumentParser(description='Normalize outreach images')
    parser.add_argument('--autofill', action='store_true', help='Automatically map numeric images to day1..day7 and duplicate last to fill')
    parser.add_argument('--no-dup', action='store_true', help='When used with --autofill, do not duplicate last image to fill missing days')
    args = parser.parse_args()

    if args.autofill:
        report = autofill_images('.', duplicate_last=not args.no_dup)
        print(pretty_print(report))
        sys.exit(1 if report['errors'] else 0)
    else:
        summary = normalize_images('.')
        print(pretty_print(summary))
        # exit code non-zero if there are errors
        sys.exit(1 if summary["errors"] else 0)
