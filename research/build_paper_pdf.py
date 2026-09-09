"""
build_paper_pdf.py — render RESEARCH_PAPER.md to a clean, academic-styled PDF.
Converts the Markdown to HTML, wraps it in a print stylesheet, and shells out to
headless Chrome (--print-to-pdf). Run:  .venv/bin/python research/build_paper_pdf.py
"""
import os, subprocess, markdown

HERE = os.path.dirname(__file__)
MD = os.path.join(HERE, "RESEARCH_PAPER.md")
HTML = os.path.join(HERE, "paper.html")
PDF = os.path.join(HERE, "RESEARCH_PAPER.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

body = markdown.markdown(
    open(MD).read(),
    extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"],
)

CSS = """
@page { size: Letter; margin: 0.9in 0.85in; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.8pt;
       line-height: 1.5; color: #1a1a1a; max-width: 46rem; margin: 0 auto; }
h1 { font-size: 21pt; line-height: 1.2; text-align: center; margin: 0 0 .2em;
     border: none; }
h1 + p, body > p:first-of-type { text-align: center; }
h2 { font-size: 14pt; margin: 1.6em 0 .5em; padding-bottom: .15em;
     border-bottom: 1.5px solid #333; page-break-after: avoid; }
h3 { font-size: 11.6pt; margin: 1.2em 0 .3em; page-break-after: avoid; }
p, li { text-align: justify; hyphens: auto; }
strong { color: #000; }
a { color: #14427a; text-decoration: none; }
code { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 9.2pt;
       background: #f4f4f6; padding: .05em .3em; border-radius: 3px; }
pre { background: #f4f4f6; border: 1px solid #e2e2e8; border-radius: 5px;
      padding: .7em .9em; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; line-height: 1.4; }
table { border-collapse: collapse; width: 100%; margin: .8em 0; font-size: 9.6pt;
        page-break-inside: auto; }
th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left;
         vertical-align: top; }
th { background: #ecebef; font-family: Georgia, serif; }
tr { page-break-inside: avoid; }
blockquote { border-left: 3px solid #c7c7d0; margin: .8em 0; padding: .2em 1em;
             color: #444; }
hr { border: none; border-top: 1px solid #ddd; margin: 1.6em 0; }
h2, h3 { break-after: avoid; }
"""

html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Risk Gate — Research Paper</title><style>{CSS}</style></head>
<body>{body}</body></html>"""

open(HTML, "w").write(html)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={PDF}", HTML],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("wrote", PDF)
