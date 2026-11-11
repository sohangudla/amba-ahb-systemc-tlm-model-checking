"""Make demo copies of the models for the UPPAAL 5 GUI.

Two cosmetic changes, neither of which changes behaviour:
  1. The grey "comments" boxes (the transformation's "Guard: nodeID ... line ..." notes)
     are removed, so the editor is readable.
  2. Every "$" in identifiers is replaced by "__". The generated names such as
     ahb_simple_bus$arbitrate work in verifyta, but the UPPAAL 5.0 GUI drops the "$"
     when it matches processes to templates and stops with
     'Template "ahb_simple_busarbitrate" not found'. The script checks that no new
     name collides with an existing one.

Outputs (for the GUI demo only; the reported results were computed on the full models):
    model/demo_view/amba_AHB_1M1S_clean.uppaal.xml
    model/demo_view/amba_AHB_1M1S_timed_clean.uppaal.xml
    model/demo_view/amba_AHB_1M1S_timed_noreset_clean.uppaal.xml
    queries/demo_view/*.q   (the same queries with "$" replaced)

Run:  python tools/make_clean_view.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
MODEL = os.path.join(ROOT, 'model')
OUT = os.path.join(MODEL, 'demo_view')
QIN = os.path.join(ROOT, 'queries')
QOUT = os.path.join(QIN, 'demo_view')
PAIRS = [('amba_AHB_1M1S.uppaal.xml', 'amba_AHB_1M1S_clean.uppaal.xml'),
         ('amba_AHB_1M1S_timed.uppaal.xml', 'amba_AHB_1M1S_timed_clean.uppaal.xml'),
         ('amba_AHB_1M1S_timed_noreset.uppaal.xml', 'amba_AHB_1M1S_timed_noreset_clean.uppaal.xml')]
QUERIES = ['1M1S_QUERIES.q', '1M1S_TIMED_QUERIES.q', 'BUG_STUDY_NORESET.q']
COMMENT = re.compile(r'[ \t]*<label kind="comments"[^>]*>[^<]*</label>\r?\n?')
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_$]*')
SEP = '__'


def rename(text):
    return text.replace('$', SEP)


def check_collisions(text):
    names = set(IDENT.findall(text))
    for n in names:
        if '$' in n and n.replace('$', SEP) in names:
            sys.exit(f'name collision: {n} -> {n.replace("$", SEP)} already exists')


os.makedirs(OUT, exist_ok=True)
os.makedirs(QOUT, exist_ok=True)
for src, dst in PAIRS:
    with open(os.path.join(MODEL, src), encoding='utf-8-sig') as f:
        text = f.read()
    check_collisions(text)
    clean, n = COMMENT.subn('', text)
    clean = rename(clean)
    with open(os.path.join(OUT, dst), 'w', encoding='utf-8', newline='\n') as f:
        f.write(clean)
    print(f'wrote model/demo_view/{dst}: removed {n} comment labels, replaced "$" with "{SEP}"')
for q in QUERIES:
    with open(os.path.join(QIN, q), encoding='ascii') as f:
        text = f.read()
    with open(os.path.join(QOUT, q), 'w', encoding='ascii', newline='\n') as f:
        f.write(rename(text))
    print(f'wrote queries/demo_view/{q}')
