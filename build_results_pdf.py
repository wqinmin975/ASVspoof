# -*- coding: utf-8 -*-
"""Build RESULTS.pdf from RESULTS.md (read-only on the source).

v1.1 changes vs the first build:
  * wider Delta column + nowrap so no table cell wraps (the v1.0 table split
    "853 [665, 1,036]" across two lines, which read like a truncated sentence);
  * cost units moved out of the header into the table notes in RESULTS.md;
  * footer/metadata carry the version number;
  * verification no longer imports PyMuPDF (DLL-incompatible on this host);
    it uses pypdf, which is available, and adds a machine-checkable assertion
    that the Delta interval appears as one continuous string in the text layer.
"""
import os, re, html, io, subprocess, tempfile, pathlib

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "RESULTS.md")
FINAL = os.path.join(ROOT, "RESULTS.pdf")
VERSION = "v1.1"
DATE = "2026-11-14"
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Times New Roman", "Microsoft YaHei", "SimSun", serif;
  font-size: 10.5pt; line-height: 1.45; color: #16191d; margin: 0;
}
h1 { font-size: 17pt; line-height: 1.25; color: #17365d; margin: 0 0 6pt;
     padding-bottom: 6pt; border-bottom: 1.6pt solid #2e5c8a; }
h2 { font-size: 12.5pt; color: #1f3864; margin: 15pt 0 7pt;
     break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 7pt; text-align: left; }
blockquote { background: #f3f6fa; border-left: 3pt solid #4a6fa5;
  padding: 7pt 10pt; margin: 0 0 11pt; font-size: 9.2pt; line-height: 1.4;
  color: #2b3140; break-inside: avoid; page-break-inside: avoid; }
table { width: auto; max-width: 100%; border-collapse: collapse; table-layout: auto;
  font-size: 8pt; margin: 9pt 0 11pt; break-inside: avoid; page-break-inside: avoid; }
th, td { border: 0.6pt solid #aab6c4; padding: 4pt 5pt; text-align: center;
  vertical-align: middle; white-space: nowrap; }
/* Auto layout + nowrap keeps every value and its SD, and the Delta point
   estimate plus its CI, on ONE line. Wrapped cells were being read as
   truncated sentences when the PDF text layer was copied. */
th { background: #e8eef6; font-weight: bold; font-size: 7.6pt; color: #1f3864; }
th:first-child, td:first-child { text-align: left; padding-left: 5pt; }
tbody tr:nth-child(even) { background: #fafbfc; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.90em;
  background: #f1f3f5; padding: 0 1.5pt; }
ol { margin: 0 0 8pt; padding-left: 19pt; }
li { margin: 0 0 5pt; padding-left: 2pt; }
li::marker { color: #2e5c8a; font-weight: bold; }
strong { font-weight: bold; }
"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', lambda m: "<code>" + m.group(1) + "</code>", s)
    s = re.sub(r'\*\*([^*]+)\*\*', r"<strong>\1</strong>", s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r"<em>\1</em>", s)
    return s


def is_sep(l):
    return l.startswith("|") and "-" in l and bool(re.match(r'^\|[\s:\-|]+\|?$', l))


# detector, AUPRC, AUROC, ECE, cost05, cost_rule, Delta, F1@0.5, F1@rule
WIDTHS9 = [11, 9, 9, 9, 12, 12, 18, 10, 10]


def convert(md):
    lines = md.splitlines()
    out, para, i = [], [], 0

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + inline(" ".join(x.strip() for x in para)) + "</p>")
            para = []

    while i < len(lines):
        l = lines[i]
        if not l.strip():
            flush(); i += 1; continue
        if l.startswith("# "):
            flush(); out.append("<h1>" + inline(l[2:].strip()) + "</h1>"); i += 1; continue
        if l.startswith("## "):
            flush(); out.append("<h2>" + inline(l[3:].strip()) + "</h2>"); i += 1; continue
        if l.startswith(">"):
            flush(); q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i][1:].strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(q)) + "</blockquote>")
            continue
        if l.startswith("|") and i + 1 < len(lines) and is_sep(lines[i + 1]):
            flush()
            head = [c.strip() for c in l.strip().strip("|").split("|")]
            i += 2
            body = []
            while i < len(lines) and lines[i].startswith("|"):
                body.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            # No <colgroup>: auto layout sizes columns to content so that
            # nowrap cells never overflow into their neighbours.
            t = ["<table>",
                "<thead><tr>" + "".join("<th>" + inline(c) + "</th>" for c in head) + "</tr></thead>",
                "<tbody>"]
            for r in body:
                t.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>")
            t += ["</tbody>", "</table>"]
            out.append("\n".join(t)); continue
        if re.match(r'^\d+\.\s+', l):
            flush(); items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                text = re.sub(r'^\d+\.\s+', "", lines[i]).strip(); i += 1
                while i < len(lines):
                    nx = lines[i]
                    if not nx.strip(): break
                    if (re.match(r'^\d+\.\s+', nx) or nx.startswith("#") or
                            nx.startswith(">") or nx.startswith("|")): break
                    if nx.startswith("   ") or nx.startswith("\t"):
                        text += " " + nx.strip(); i += 1
                    else:
                        break
                items.append(text)
                j = i
                while j < len(lines) and not lines[j].strip(): j += 1
                if j < len(lines) and re.match(r'^\d+\.\s+', lines[j]): i = j
                else: break
            out.append("<ol>" + "".join("<li>" + inline(t) + "</li>" for t in items) + "</ol>")
            continue
        para.append(l); i += 1
    flush()
    return "\n".join(out)


def main():
    md = open(SRC, encoding="utf-8").read()
    body = convert(md)
    doc = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
           '<title>ASVspoof5 real-data anchor - Results ' + VERSION + '</title><style>' + CSS +
           '</style></head><body>' + body + '</body></html>')

    tmp = tempfile.mkdtemp(prefix="asvspoof5_pdf_")
    html_path = os.path.join(tmp, "results.html")
    raw_pdf = os.path.join(tmp, "raw.pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)

    uri = pathlib.Path(html_path).as_uri()
    last = ""
    for exe in BROWSERS:
        if not os.path.exists(exe): continue
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-sandbox",
               "--no-first-run", "--no-default-browser-check",
               "--no-pdf-header-footer", "--virtual-time-budget=5000",
               "--user-data-dir=" + os.path.join(tmp, "profile"),
               "--print-to-pdf=" + raw_pdf, uri]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except Exception as e:
            last = "%s: %s" % (exe, e); continue
        if os.path.exists(raw_pdf) and os.path.getsize(raw_pdf) > 5000:
            print("renderer:", os.path.basename(exe), "rc=", r.returncode)
            break
        last = "%s rc=%s stderr=%s" % (exe, r.returncode, (r.stderr or "")[-400:])
    else:
        raise RuntimeError("headless PDF rendering failed: " + last)

    # Overlay footer + page numbers, set PDF metadata.
    from reportlab.pdfgen import canvas
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(raw_pdf)
    n = len(reader.pages)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    for idx, page in enumerate(reader.pages):
        w = float(page.mediabox.width); h = float(page.mediabox.height)
        c.setPageSize((w, h))
        c.setStrokeColorRGB(0.80, 0.83, 0.87); c.setLineWidth(0.4)
        c.line(46, 38, w - 46, 38)
        c.setFont("Helvetica", 7.4); c.setFillColorRGB(0.45, 0.48, 0.52)
        c.drawString(46, 26, "ASVspoof5 real-data anchor  |  RESULTS.md " + VERSION + "  |  " + DATE)
        c.drawRightString(w - 46, 26, "Page %d of %d" % (idx + 1, n))
        c.showPage()
    c.save(); buf.seek(0)
    overlay = PdfReader(buf)
    writer = PdfWriter()
    for idx, page in enumerate(reader.pages):
        try: page.merge_page(overlay.pages[idx])
        except AttributeError: page.mergePage(overlay.pages[idx])
        writer.add_page(page)
    writer.add_metadata({"/Title": "ASVspoof5 real-data anchor - Results " + VERSION,
                         "/Subject": "Decision layer vs 0.5 threshold, real-speech anchor",
                         "/Creator": "build_results_pdf.py (" + VERSION + ", " + DATE + ")"})
    with open(FINAL, "wb") as f:
        writer.write(f)

    # Verification with pypdf only (PyMuPDF's DLL is incompatible on this host).
    check = PdfReader(FINAL)
    text = "\n".join((p.extract_text() or "") for p in check.pages)
    flat = re.sub(r"\s+", " ", text)
    rect = check.pages[0].mediabox
    must = ["0.0772", "0.690", "2,860", "2,008", "3,886", "2,396",
            "29.8%", "38.3%", "785", "628", "140,950", "Appendix A",
            "v1.1", "E[cost]", "AUPRC baseline", "852 cost units"]
    # the Delta interval must survive as ONE continuous string => no cell wrap
    must.append("853 [665, 1036]")
    forbidden = ["0.087", "pending author", "TODO", "853[665"]
    missing = [s for s in must if s not in flat]
    found_bad = [s for s in forbidden if s in flat]
    print("pages:", len(check.pages), "| size pt: %.0f x %.0f" % (rect.width, rect.height))
    print("missing key strings:", missing)
    print("forbidden strings found:", found_bad)
    print("cjk path extracted:", "数据分析过程记录表" in flat)
    print("delta interval unwrapped:", "853 [665, 1036]" in flat)
    print("output:", FINAL, os.path.getsize(FINAL), "bytes")
    print("tmpdir:", tmp)
    if missing or found_bad:
        raise SystemExit("PDF verification failed: missing=%s forbidden=%s" % (missing, found_bad))


if __name__ == "__main__":
    main()
