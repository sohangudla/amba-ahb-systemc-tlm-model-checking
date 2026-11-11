"""Draw selected automata straight from the UPPAAL model file as SVG figures.

Positions, location names and edge labels (guard / synchronisation / assignment) are read
from the model XML; only the "comments" labels (source-line annotations) are left out so
the drawing stays readable. Nothing is redrawn by hand.

Run:  python tools/make_figures.py
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
MODEL = os.path.join(ROOT, 'model', 'amba_AHB_1M1S.uppaal.xml')
OUT = os.path.join(ROOT, 'figures')

FIGURES = [
    ('peq_element$data', 'fig_peq_element.svg'),
    ('peq_fetch$data', 'fig_peq_fetch.svg'),
    ('ahb_simple_bus$arbitrate', 'fig_arbitrate.svg'),
]
SCALE = 1.9
COLORS = {'guard': '#1a7f37', 'synchronisation': '#0b6aa2', 'assignment': '#6b3fa0',
          'invariant': '#b4232c', 'select': '#8a6d00'}


def esc(s):
    return html.escape(s, quote=True)


def template_block(text, name):
    for m in re.finditer(r'<template>(.*?)</template>', text, re.S):
        n = re.search(r'<name[^>]*>\s*([^<]*?)\s*</name>', m.group(1)).group(1)
        if n == name:
            return m.group(1)
    raise SystemExit(f'template {name} not found')


def parse(block):
    locs = {}
    for m in re.finditer(r'<location id="(\w+)" x="(-?\d+)" y="(-?\d+)">(.*?)</location>', block, re.S):
        body = m.group(4)
        nm = re.search(r'<name[^>]*>\s*([^<]*?)\s*</name>', body)
        inv = re.search(r'<label kind="invariant"[^>]*>([^<]*)</label>', body)
        locs[m.group(1)] = {
            'x': int(m.group(2)) * SCALE, 'y': int(m.group(3)) * SCALE,
            'name': nm.group(1) if nm else '',
            'urgent': '<urgent/>' in body, 'committed': '<committed/>' in body,
            'inv': ' '.join(html.unescape(inv.group(1)).split()) if inv else ''}
    init = re.search(r'<init ref="(\w+)"/>', block).group(1)
    edges = []
    for m in re.finditer(r'<transition>(.*?)</transition>', block, re.S):
        t = m.group(1)
        src = re.search(r'<source ref="(\w+)"/>', t).group(1)
        dst = re.search(r'<target ref="(\w+)"/>', t).group(1)
        nails = [(int(a) * SCALE, int(b) * SCALE) for a, b in re.findall(r'<nail x="(-?\d+)" y="(-?\d+)"/>', t)]
        labels = [(k, ' '.join(html.unescape(v).split()))
                  for k, v in re.findall(r'<label kind="(\w+)"[^>]*>([^<]*)</label>', t)
                  if k != 'comments' and v.strip()]
        edges.append({'src': src, 'dst': dst, 'nails': nails, 'labels': labels})
    return locs, init, edges


def wrap(text, width=34):
    out, line = [], ''
    for part in re.split(r'(?<=,) ', text):
        if line and len(line) + len(part) + 1 > width:
            out.append(line)
            line = part
        else:
            line = (line + ' ' + part).strip()
    if line:
        out.append(line)
    return out


def draw(name, fname):
    with open(MODEL, encoding='utf-8-sig') as f:
        locs, init, edges = parse(template_block(f.read(), name))
    xs = [l['x'] for l in locs.values()]
    ys = [l['y'] for l in locs.values()]
    pad = 130
    minx, miny = min(xs) - pad, min(ys) - pad
    w, h = max(xs) - minx + pad + 120, max(ys) - miny + pad + 40
    r = 13
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.0f} {miny:.0f} {w:.0f} {h:.0f}" '
             f'font-family="Helvetica, Arial, sans-serif" font-size="11" role="img" '
             f'aria-label="UPPAAL template {esc(name)}">',
             '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
             'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker></defs>',
             f'<rect x="{minx:.0f}" y="{miny:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#fff"/>']
    seen = {}
    label_parts = []
    for e in edges:
        a, b = locs[e['src']], locs[e['dst']]
        pts = [(a['x'], a['y'])] + e['nails'] + [(b['x'], b['y'])]
        key = tuple(sorted((e['src'], e['dst'])))
        k = seen.get(key, 0)
        seen[key] = k + 1
        bend = 0
        if len(pts) == 2:
            # curve the edge if it is a parallel duplicate or would pass through another location
            ax, ay, bx, by = a['x'], a['y'], b['x'], b['y']
            seg2 = max((bx - ax) ** 2 + (by - ay) ** 2, 1)
            blocked = False
            for oid, o in locs.items():
                if oid in (e['src'], e['dst']):
                    continue
                t = ((o['x'] - ax) * (bx - ax) + (o['y'] - ay) * (by - ay)) / seg2
                if 0 < t < 1:
                    px, py = ax + t * (bx - ax), ay + t * (by - ay)
                    if (px - o['x']) ** 2 + (py - o['y']) ** 2 < (r + 10) ** 2:
                        blocked = True
            if k or blocked:
                bend = (60 + 45 * (k // 2)) * (1 if (k + blocked) % 2 else -1)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        dx, dy = x1 - x0, y1 - y0
        d = max((dx * dx + dy * dy) ** 0.5, 1)
        ex, ey = x1 - dx / d * (r + 2), y1 - dy / d * (r + 2)
        sx0, sy0 = pts[0]
        dx0, dy0 = pts[1][0] - sx0, pts[1][1] - sy0
        d0 = max((dx0 * dx0 + dy0 * dy0) ** 0.5, 1)
        sx, sy = sx0 + dx0 / d0 * r, sy0 + dy0 / d0 * r
        if len(pts) == 2 and bend:
            mx, my = (sx + ex) / 2 - dy / d * bend, (sy + ey) / 2 + dx / d * bend
            path = f'M{sx:.1f},{sy:.1f} Q{mx:.1f},{my:.1f} {ex:.1f},{ey:.1f}'
            lx, ly = 0.25 * sx + 0.5 * mx + 0.25 * ex, 0.25 * sy + 0.5 * my + 0.25 * ey
        else:
            mid = ' '.join(f'L{x:.1f},{y:.1f}' for x, y in pts[1:-1])
            path = f'M{sx:.1f},{sy:.1f} {mid} L{ex:.1f},{ey:.1f}'
            seg = len(pts) // 2
            lx = (pts[seg - 1][0] + pts[seg][0]) / 2
            ly = (pts[seg - 1][1] + pts[seg][1]) / 2
        parts.append(f'<path d="{path}" fill="none" stroke="#333" stroke-width="1.3" marker-end="url(#ah)"/>')
        lines = []
        for kind, text in e['labels']:
            lines += [(kind, ln) for ln in wrap(text)]
        if lines:
            ty = ly - 7 * (len(lines) - 1) + 4
            bw = max(len(t) for _, t in lines) * 6.2 + 8
            label_parts.append(f'<rect x="{lx + 6:.1f}" y="{ty - 11:.1f}" width="{bw:.1f}" height="{14 * len(lines) + 2}" '
                               f'fill="#fff" fill-opacity="0.75" rx="3"/>')
            for i, (kind, text) in enumerate(lines):
                label_parts.append(f'<text x="{lx + 10:.1f}" y="{ty + 14 * i:.1f}" fill="{COLORS.get(kind, "#333")}">{esc(text)}</text>')
    parts += label_parts
    for lid, l in locs.items():
        fill = '#fde2e1' if l['committed'] else ('#fff3cd' if l['urgent'] else '#e8eef7')
        parts.append(f'<circle cx="{l["x"]:.1f}" cy="{l["y"]:.1f}" r="{r}" fill="{fill}" stroke="#223" stroke-width="1.5"/>')
        if lid == init:
            parts.append(f'<circle cx="{l["x"]:.1f}" cy="{l["y"]:.1f}" r="{r - 4}" fill="none" stroke="#223" stroke-width="1.2"/>')
        tag = 'C' if l['committed'] else ('U' if l['urgent'] else '')
        if tag:
            parts.append(f'<text x="{l["x"]:.1f}" y="{l["y"] + 4:.1f}" text-anchor="middle" font-weight="bold" fill="#7a4b00">{tag}</text>')
        label = l['name'] + (f'  [{l["inv"]}]' if l['inv'] else '')
        if label.strip():
            parts.append(f'<text x="{l["x"]:.1f}" y="{l["y"] - r - 6:.1f}" text-anchor="middle" font-weight="bold" fill="#222">{esc(label)}</text>')
    parts.append('</svg>')
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    print(f'wrote figures/{fname}: {len(locs)} locations, {len(edges)} edges')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for n, f in FIGURES:
        draw(n, f)
