#!/usr/bin/env python3
"""Build the team presentation guide PDF from docs/team/presentation-guide.md.

    python3 scripts/build_guide.py      # -> docs/team/PathSnap_Presentation_Guide.pdf

Uses the same styling and tools as scripts/build_report.py (Python-Markdown + weasyprint).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_report import CSS, ROOT  # noqa: E402

SRC = ROOT / "docs" / "team" / "presentation-guide.md"
PDF = ROOT / "docs" / "team" / "PathSnap_Presentation_Guide.pdf"
EXTRA_CSS = """
body { font-size: 10pt; line-height: 1.45; }
h1 { font-size: 22pt; } h2 { margin-top: 16pt; } p, li { margin: 3pt 0; }
td:first-child { white-space: nowrap; }
"""


def main() -> int:
    import markdown  # noqa: PLC0415
    html = markdown.markdown(SRC.read_text("utf-8"), extensions=["tables", "fenced_code", "attr_list"])
    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>PathSnap presentation guide</title>"
           f"<style>{CSS}{EXTRA_CSS}</style></head><body>{html}</body></html>")
    out = ROOT / "report" / "build" / "guide.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, "utf-8")
    exe = shutil.which("weasyprint")
    if not exe:
        print("weasyprint command not found", file=sys.stderr)
        return 2
    subprocess.run([exe, "--base-url", str(ROOT), str(out), str(PDF)], check=True)
    print(f"wrote {PDF.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
