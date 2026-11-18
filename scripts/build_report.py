#!/usr/bin/env python3
"""Assemble the single technical report PDF (Deliverables PDF, sections 2-7).

    python3 scripts/build_report.py            # -> report/PathSnap_Technical_Report.pdf
    python3 scripts/build_report.py --html     # HTML only (for quick review)

Sections are concatenated in a fixed order. A missing section or a `PENDING:` marker is shown
in red in the output and listed on stdout. Placeholders are never filled with invented content.
Requires Python-Markdown and the `weasyprint` command-line tool.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "report"
SECTIONS = [
    ("front.md", "B/team"),
    ("science.md", "A"),     # Deliverables 2.2-5: EDA, models, HPO, HMM
    ("system.md", "B"),      # Deliverables 6-7: Folium, API/UI/deployment
    ("integrity.md", "team"),
]
REQUIRED_HEADINGS = [
    "Dataset Understanding", "Model Experimentation", "Bayesian Hyperparameter Optimisation",
    "HMM and Viterbi", "Geographical Visualisation", "API, UI and Deployment",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm; @bottom-right { content: counter(page); font-size: 9pt; color: #56616b; } }
body { font-family: 'IBM Plex Sans', 'DejaVu Sans', sans-serif; font-size: 10.5pt; line-height: 1.45; color: #20262b; }
h1 { font-size: 20pt; margin: 0 0 6pt; } h2 { font-size: 14pt; margin-top: 18pt; border-bottom: 1px solid #d3d9dd; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin-top: 12pt; }
h2 { page-break-after: avoid; } h3 { page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 8pt 0; font-variant-numeric: tabular-nums; }
th, td { border: 1px solid #d3d9dd; padding: 3pt 5pt; vertical-align: top; } th { background: #eef1f2; text-align: left; }
tr, img, pre, figure { break-inside: avoid; page-break-inside: avoid; } thead { display: table-header-group; }
img { max-width: 100%; display: block; margin: 6pt auto; border: 1px solid #d3d9dd; }
code { font-family: 'IBM Plex Mono', 'DejaVu Sans Mono', monospace; font-size: 9pt; }
pre { background: #f4f6f7; padding: 6pt; font-size: 8pt; white-space: pre; overflow: hidden; }
code.language-log { white-space: pre-wrap; overflow-wrap: anywhere; }  /* long log lines wrap; diagrams keep white-space: pre */
.pending { color: #b42318; font-weight: 600; }
.missing { color: #b42318; border: 1px dashed #b42318; padding: 8pt; }
figcaption, .caption { font-size: 9pt; color: #56616b; text-align: center; }
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true", help="write HTML only")
    args = ap.parse_args()
    try:
        import markdown  # noqa: PLC0415
    except ImportError:
        print("Python-Markdown is missing: pip install -r requirements.lock.txt", file=sys.stderr)
        return 2

    parts, problems = [], []
    for name, owner in SECTIONS:
        path = REPORT / "sections" / name
        if not path.is_file():
            problems.append(f"missing section {name} (owner {owner})")
            parts.append(f'<div class="missing">Section <code>{name}</code> not written yet (owner: {owner}).</div>')
            continue
        text = path.read_text("utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if "PENDING:" in line:
                problems.append(f"{name}:{i}: {line.strip()[:120]}")
        html = markdown.markdown(text, extensions=["tables", "fenced_code", "attr_list", "toc"])
        html = re.sub(r"(PENDING:[^<]*)", r'<span class="pending">\1</span>', html)
        parts.append(html)

    body = "\n".join(parts)
    headings = " | ".join(re.sub("<[^>]+>", "", h) for h in re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", body)).lower()
    for h in REQUIRED_HEADINGS:
        if h.lower() not in headings:
            problems.append(f"required heading not found: {h}")
    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>PathSnap technical report</title>"
           f"<style>{CSS}</style></head><body>{body}"
           f"<p class='caption'>Built {date.today().isoformat()} from repository sources.</p></body></html>")
    html_path = REPORT / "build" / "report.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(doc, "utf-8")
    print(f"wrote {html_path.relative_to(ROOT)}")
    if not args.html:
        exe = shutil.which("weasyprint")
        if not exe:
            print("weasyprint command not found; install it or use --html", file=sys.stderr)
            return 2
        pdf = REPORT / "PathSnap_Technical_Report.pdf"
        subprocess.run([exe, "--base-url", str(ROOT), str(html_path), str(pdf)], check=True)
        print(f"wrote {pdf.relative_to(ROOT)}")
    if problems:
        print("\nOPEN ITEMS (shown in red in the output):")
        for p in problems:
            print(f"  - {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
