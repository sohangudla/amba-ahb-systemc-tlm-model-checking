"""Run every 1M1S check with verifyta and write the results and the report.

Nothing in the results or the report is typed by hand: every "ours" number comes from
the verifyta output saved in results/raw/.

Usage (from the project folder):
    python tools/run_all.py --uppaal "C:/path/to/uppaal"       # folder or verifyta.exe
    python tools/run_all.py                                   # uses uppaal_path.txt or UPPAAL_VERIFYTA
    python tools/run_all.py --render-only                     # rebuild report from results/results.json

Before running: python tools/make_models.py and python tools/make_figures.py
(run_all.py calls both automatically).

If verifyta cannot run (for example UPPAAL 4.1.26-1 failing its start-up check with an
HTTP 301 page), the script stops and prints verifyta's own output. It does not patch or
bypass anything.
"""
import argparse
import datetime
import html
import json
import os
import platform
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
MODEL = os.path.join(ROOT, 'model')
RESULTS = os.path.join(ROOT, 'results')
RAW = os.path.join(RESULTS, 'raw')
REPORT_TEMPLATE = os.path.join(ROOT, 'report', 'report_template.html')
REPORT_OUT = os.path.join(ROOT, 'report', '1M1S_Report.html')
JSON_OUT = os.path.join(RESULTS, 'results.json')
MD_OUT = os.path.join(RESULTS, 'results.md')
TIMED_Q = os.path.join(ROOT, 'queries', '1M1S_TIMED_QUERIES.q')

ORIG = 'amba_AHB_1M1S.uppaal.xml'
TIMED = 'amba_AHB_1M1S_timed.uppaal.xml'
NORESET = 'amba_AHB_1M1S_timed_noreset.uppaal.xml'
FIFO = 'test_fifo.uppaal.xml'
CLOCK_PERIOD = 20  # clk$ctor(20, ...) in the model: one bus clock period = 20 model time units

# Paper Table II, 1M1S column (Pockrandt, Herber, Glesner, ESTIMedia 2011)
PAPER = {
    'deadlock': ('0:07', '74,345'),
    'only_one_master': ('-', '-'),
    'grant_m1': ('0:05', '74,345'),
    'grant_m2': ('-', '-'),
    'comm_in_time': ('0:17', '74,345'),
}

CHECKS = [
    # id, group, title, model, query, expected
    ('deadlock', 'paper', 'Deadlock freedom', ORIG, 'A[] not deadlock', True),
    ('grant_m1', 'paper', 'Bus granted to M1 (leads-to)', ORIG,
     'AHB_M1$m_bus_req_pending --> AHB_M1$m_bus_granted', True),
    ('grant_m1_reach', 'extra', 'M1 can be granted the bus (reachability only)', ORIG,
     'E<> AHB_M1$m_bus_granted', True),
    ('m2_never', 'extra', 'Arbiter never grants the unused master-2 slot', ORIG,
     'A[] AHB_Bus$m_InService_Register != 2', True),
    ('reg_range', 'extra', 'Arbiter grant register only 0 or 1', ORIG,
     'A[] AHB_Bus$m_InService_Register <= 1', True),
    ('mem_access', 'extra', 'No invalid memory access', ORIG, 'A[] not MEM_ERR_ACCESS_FAIL', True),
    ('mem_double_free', 'extra', 'No double free', ORIG, 'A[] not MEM_ERR_DOUBLE_FREE', True),
    ('mem_out', 'extra', 'No out-of-memory', ORIG, 'A[] not MEM_ERR_NOT_ENOUGH_MEM', True),
    ('timed_deadlock', 'instrument', 'Timed model: deadlock freedom (instrumentation sanity check)', TIMED,
     'A[] not deadlock', True),
    ('timed_grant_reach', 'instrument', 'Timed model: communication starts', TIMED,
     'E<> M1_isCommunicating', True),
    ('txn_completes', 'bug', 'With reset: every started transfer completes', TIMED,
     'M1_isCommunicating --> !M1_isCommunicating', True),
    ('noreset_deadlock', 'bug', 'Without reset: deadlock freedom', NORESET, 'A[] not deadlock', None),
    ('noreset_completes', 'bug', 'Without reset: every started transfer completes', NORESET,
     'M1_isCommunicating --> !M1_isCommunicating', None),
    ('fifo_deadlock', 'fifo', 'FIFO: deadlock freedom', FIFO, 'A[] not deadlock', True),
    ('fifo_mem_access', 'fifo', 'FIFO: no invalid memory access', FIFO, 'A[] not MEM_ERR_ACCESS_FAIL', True),
    ('fifo_mem_corrupt', 'fifo', 'FIFO: no memory corruption', FIFO, 'A[] not MEM_ERR_CORRUPTED_MEM', True),
]


# ----------------------------------------------------------------------------- verifyta
def find_verifyta(arg):
    cands = []
    if arg:
        cands.append(arg)
    if os.environ.get('UPPAAL_VERIFYTA'):
        cands.append(os.environ['UPPAAL_VERIFYTA'])
    cfg = os.path.join(ROOT, 'uppaal_path.txt')
    if os.path.exists(cfg):
        with open(cfg, encoding='utf-8') as f:
            line = f.read().strip()
            if line:
                cands.append(line)
    cands.append(os.path.join(ROOT, 'uppaal'))     # UPPAAL unzipped into the project folder itself
    exe = 'verifyta.exe' if os.name == 'nt' else 'verifyta'
    for c in cands:
        c = os.path.expandvars(os.path.expanduser(c.strip().strip('"')))
        if not os.path.isabs(c):
            c = os.path.join(ROOT, c)                  # relative paths are relative to the project folder
        for p in (c, os.path.join(c, exe), os.path.join(c, 'bin-Windows', exe), os.path.join(c, 'bin', exe),
                  os.path.join(c, 'bin-Linux', exe)):
            if os.path.isfile(p):
                return os.path.abspath(p)
    sys.exit('verifyta not found. Do one of these: write your UPPAAL folder into uppaal_path.txt '
             '(absolute, or relative to the project folder); unzip UPPAAL into a folder named "uppaal" inside the '
             'project; or pass --uppaal <folder or verifyta.exe>.')


def run_verifyta(verifyta, model, query, tag, timeout):
    os.makedirs(RAW, exist_ok=True)
    qfile = os.path.join(RAW, tag + '.q')
    with open(qfile, 'w', encoding='ascii') as f:
        f.write(query + '\n')
    cmd = [verifyta, '-u', '-q', os.path.join(MODEL, model), qfile]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=os.path.dirname(verifyta), encoding='utf-8', errors='replace')
        out, err, code, timed_out = p.stdout, p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b'').decode('utf-8', 'replace') if isinstance(e.stdout, bytes) else (e.stdout or '')
        err, code, timed_out = '', None, True
    wall = time.time() - t0
    with open(os.path.join(RAW, tag + '.txt'), 'w', encoding='utf-8') as f:
        f.write('COMMAND: ' + ' '.join(f'"{c}"' for c in cmd) + '\n')
        f.write(f'EXIT CODE: {code}   WALL TIME: {wall:.2f} s   TIMED OUT: {timed_out}\n')
        f.write('--- stdout ---\n' + out + '\n--- stderr ---\n' + err + '\n')
    text = out + '\n' + err
    clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)
    res = {'command': cmd, 'exit_code': code, 'wall_s': round(wall, 2), 'timed_out': timed_out, 'raw': f'results/raw/{tag}.txt'}
    if re.search(r'Formula is NOT satisfied', clean):
        res['satisfied'] = False
    elif re.search(r'Formula is satisfied', clean):
        res['satisfied'] = True
    elif re.search(r'Formula (?:may|might) be', clean):
        res['satisfied'] = 'maybe'
    else:
        res['satisfied'] = None
    for key, pat in (('states_stored', r'States stored\s*:\s*(\d+)'), ('states_explored', r'States explored\s*:\s*(\d+)'),
                     ('cpu_ms', r'CPU user time used\s*:\s*(\d+)\s*ms'), ('resident_kib', r'Resident memory used\s*:\s*(\d+)'),
                     ('virtual_kib', r'Virtual memory used\s*:\s*(\d+)')):
        m = re.findall(pat, clean)
        res[key] = int(m[-1]) if m else None
    if res['satisfied'] is None:
        res['error'] = clean.strip()[:2000] or 'no output'
    return res


def check_runs(verifyta):
    """Stop early with verifyta's own message if it cannot verify a trivial query."""
    r = run_verifyta(verifyta, FIFO, 'E<> true', '_smoke_test', 120)
    if r['satisfied'] is not True:
        print('\nverifyta could not run a trivial query. Its output was:\n')
        print(r.get('error', ''))
        print('\nStopping here. Install a working, licensed UPPAAL and run again (nothing was patched or bypassed).')
        sys.exit(2)


def search_bound(verifyta, timeout, max_n):
    """Smallest N with A[] M1_isCommunicating imply x <= N, by doubling then binary search."""
    probes = []

    def probe(n):
        r = run_verifyta(verifyta, TIMED, f'A[] M1_isCommunicating imply x <= {n}', f'comm_N{n}', timeout)
        r['N'] = n
        probes.append(r)
        print(f'    N = {n:>6}: {fmt_sat(r["satisfied"])}  ({r["wall_s"]} s)')
        if r['satisfied'] not in (True, False):
            raise RuntimeError(f'verifyta gave no verdict for N={n}; see {r["raw"]}')
        return r['satisfied']

    lo, hi = None, None
    n = CLOCK_PERIOD
    while n <= max_n:
        if probe(n):
            hi = n
            break
        lo = n
        n *= 2
    if hi is None:
        return {'found': False, 'max_tested': max_n, 'probes': probes}
    lo = lo if lo is not None else -1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if probe(mid):
            hi = mid
        else:
            lo = mid
    best = next(p for p in probes if p['N'] == hi)
    below = next((p for p in probes if p['N'] == hi - 1), None)
    return {'found': True, 'N': hi, 'result': best, 'N_minus_1': below, 'probes': probes}


def fmt_sat(s):
    return {True: 'satisfied', False: 'NOT satisfied', 'maybe': 'maybe satisfied'}.get(s, 'no verdict')


# ----------------------------------------------------------------------------- reporting
def num(v):
    return f'{v:,}' if isinstance(v, int) else '—'


def mmss(ms):
    if ms is None:
        return '—'
    s = ms / 1000
    return f'{int(s // 60)}:{s % 60:04.1f}' if s >= 60 else f'{s:.2f} s'


def verdict_html(r):
    if not r:
        return '<span class="pending">not run</span>'
    s = r.get('satisfied')
    if s is True:
        return '<span class="ok">Satisfied</span>'
    if s is False:
        return '<span class="bad">Not satisfied</span>'
    return f'<span class="pending">{"timed out" if r.get("timed_out") else "no verdict"}</span>'


def build_tables(data):
    res = data.get('checks', {})
    rows = []
    paper_rows = [
        ('deadlock', 'Deadlock freedom', 'A[] not deadlock', res.get('deadlock')),
        ('only_one_master', 'Only one master granted', 'A[] M1#busgranted + M2#busgranted &lt;= 1', None),
        ('grant_m1', 'Bus granted to M1', html.escape('AHB_M1$m_bus_req_pending --> AHB_M1$m_bus_granted'), res.get('grant_m1')),
        ('grant_m2', 'Bus granted to M2', 'M2#busrequest --&gt; M2#busgranted', None),
        ('comm_in_time', 'Communication in time',
         html.escape(f'A[] M1_isCommunicating imply x <= {data["comm"]["N"]}' if data.get('comm', {}).get('found')
                     else 'A[] M1_isCommunicating imply x <= N'),
         data.get('comm', {}).get('result')),
    ]
    for pid, name, q, r in paper_rows:
        pt, ps = PAPER[pid]
        if pid in ('only_one_master', 'grant_m2'):
            rows.append(f'<tr><td>{name}</td><td><code>{q}</code></td><td>{pt}</td><td>{ps}</td>'
                        f'<td colspan="3" class="na">Not applicable: 1M1S has no second master</td></tr>')
            continue
        rows.append(f'<tr><td>{name}</td><td><code>{q}</code></td><td>{pt}</td><td>{ps}</td>'
                    f'<td>{mmss(r.get("cpu_ms")) if r else "—"}</td>'
                    f'<td>{num(r.get("states_explored")) if r else "—"}<br><small>stored {num(r.get("states_stored")) if r else "—"}</small></td>'
                    f'<td>{verdict_html(r)}</td></tr>')
    table_paper = '\n'.join(rows)

    def simple(group):
        out = []
        for cid, g, title, model, query, expected in CHECKS:
            if g != group:
                continue
            r = res.get(cid)
            out.append(f'<tr><td>{html.escape(title)}</td><td><code>{html.escape(query)}</code></td>'
                       f'<td><small>{html.escape(model)}</small></td>'
                       f'<td>{num(r.get("states_explored")) if r else "—"}</td><td>{mmss(r.get("cpu_ms")) if r else "—"}</td>'
                       f'<td>{verdict_html(r)}</td></tr>')
        return '\n'.join(out)
    return table_paper, simple('extra') + '\n' + simple('instrument'), simple('bug'), simple('fifo')


def sentences(data):
    res = data.get('checks', {})
    s = {}
    d = res.get('deadlock')
    if d and d.get('states_explored'):
        ratio = d['states_explored'] / 74345
        ratio_s = f'{ratio:.1f}' if ratio >= 1 else f'{ratio:.2f}'
        s['STATE_SENTENCE'] = (
            f'Our deadlock-freedom check explored {d["states_explored"]:,} symbolic states '
            f'({d["states_stored"]:,} stored), about {ratio_s} times '
            'the 74,345 states reported in the paper. '
            'We do not try to match the paper\'s count. Possible reasons, none of which we have isolated, are a '
            'different UPPAAL version and search options (the paper used a 2011 release; we used the version listed '
            'in Section IV-A), our model being reduced by hand from the 2M2S model rather than regenerated, and a '
            'PEQ depth of four entries per queue.')
    else:
        s['STATE_SENTENCE'] = 'The state count will appear here after the checks are run.'
    c = data.get('comm', {})
    if c.get('found'):
        n = c['N']
        nm1 = c.get('N_minus_1')
        conf = (' The check with N &minus; 1 = {0} was not satisfied, so {1} is the smallest bound.'.format(n - 1, n)
                if nm1 and nm1.get('satisfied') is False else '')
        s['N_SENTENCE'] = (f'The smallest bound that holds is N = {n} time units, which is {n / CLOCK_PERIOD:g} '
                           f'bus clock periods of {CLOCK_PERIOD} time units each.' + conf)
    elif c:
        s['N_SENTENCE'] = f'No bound was found up to N = {c.get("max_tested")} time units.'
    else:
        s['N_SENTENCE'] = 'The bound N will appear here after the checks are run.'
    a, b, m = res.get('txn_completes'), res.get('noreset_completes'), res.get('noreset_deadlock')
    if a and b and m:
        s['BUG_SENTENCE'] = (
            f'With the reset in place, "every started transfer completes" is {fmt_sat(a["satisfied"])}. '
            f'With the reset removed, deadlock freedom is {fmt_sat(m["satisfied"])} and "every started transfer '
            f'completes" is {fmt_sat(b["satisfied"])}.')
        if m['satisfied'] is True and b['satisfied'] is False:
            s['BUG_SENTENCE'] += (' So in our model the missing reset shows up as a liveness failure (a transfer '
                                  'that never finishes) rather than as a UPPAAL deadlock, most likely because the '
                                  'clock and scheduler keep running, so the system as a whole is never stuck.')
    else:
        s['BUG_SENTENCE'] = 'The results of the bug study will appear here after the checks are run.'
    paper_ids = [('deadlock', 'deadlock freedom'), ('grant_m1', 'bus grant to M1')]
    if all(res.get(i) for i, _ in paper_ids) and c:
        parts = [f'{name} is {fmt_sat(res[i]["satisfied"])}' for i, name in paper_ids]
        parts.append(f'communication in time holds with N = {c["N"]}' if c.get('found')
                     else 'no communication-in-time bound was found in the tested range')
        s['CONCLUSION_SENTENCE'] = 'For the three properties of Table II that apply to 1M1S, ' + ', '.join(parts[:-1]) + \
            ', and ' + parts[-1] + '.'
    else:
        s['CONCLUSION_SENTENCE'] = 'The verdicts will be summarised here after the checks are run.'
    return s


def render(data):
    with open(REPORT_TEMPLATE, encoding='utf-8') as f:
        t = f.read()
    tp, te, tb, tf = build_tables(data)
    rep = {
        'TABLE_PAPER': tp, 'TABLE_EXTRA': te, 'TABLE_BUG': tb, 'TABLE_FIFO': tf,
        'UPPAAL_VERSION': html.escape(data.get('uppaal_version', 'not run yet')),
        'RUN_DATE': html.escape(data.get('run_date', 'not run yet')),
        'HOST': html.escape(data.get('host', 'not run yet')),
        'STATUS': ('' if data.get('complete') else
                   '<div class="draft">DRAFT &mdash; the result columns are empty because the checks have not been '
                   'run yet. Run <code>python tools/run_all.py</code> with a working UPPAAL to fill them.</div>'),
    }
    rep.update(sentences(data))
    for fig in ('fig_peq_element', 'fig_peq_fetch', 'fig_arbitrate'):
        p = os.path.join(ROOT, 'figures', fig + '.svg')
        rep[fig.upper()] = open(p, encoding='utf-8').read() if os.path.exists(p) else '<p>(figure missing)</p>'
    for k, v in rep.items():
        t = t.replace('{{' + k + '}}', v)
    left = re.findall(r'\{\{\w+\}\}', t)
    if left:
        sys.exit(f'unfilled placeholders in template: {sorted(set(left))}')
    with open(REPORT_OUT, 'w', encoding='utf-8') as f:
        f.write(t)
    print('wrote', os.path.relpath(REPORT_OUT, ROOT))


def write_md(data):
    res = data.get('checks', {})
    lines = [f'# 1M1S verification results', '',
             f'- UPPAAL: {data.get("uppaal_version")}', f'- Run: {data.get("run_date")} on {data.get("host")}', '',
             '| Check | Model | Query | Result | Explored | Stored | CPU | Raw output |',
             '|---|---|---|---|---|---|---|---|']
    for cid, g, title, model, query, expected in CHECKS:
        r = res.get(cid, {})
        lines.append(f'| {title} | {model} | `{query}` | {fmt_sat(r.get("satisfied"))} | {num(r.get("states_explored"))} | '
                     f'{num(r.get("states_stored"))} | {mmss(r.get("cpu_ms"))} | {r.get("raw", "")} |')
    c = data.get('comm', {})
    lines += ['', '## Communication in time (timed model)', '']
    if c.get('found'):
        r = c['result']
        lines.append(f'Smallest N: **{c["N"]}** time units ({c["N"] / CLOCK_PERIOD:g} clock periods). '
                     f'Explored {num(r.get("states_explored"))}, stored {num(r.get("states_stored"))}, CPU {mmss(r.get("cpu_ms"))}.')
    lines += ['', '| N | Result | Raw output |', '|---|---|---|']
    for p in c.get('probes', []):
        lines.append(f'| {p["N"]} | {fmt_sat(p["satisfied"])} | {p["raw"]} |')
    with open(MD_OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', os.path.relpath(MD_OUT, ROOT))


def write_timed_queries(n):
    with open(TIMED_Q, encoding='ascii') as f:
        q = f.read()
    q = re.sub(r'x <= \S+', f'x <= {n}', q)
    with open(TIMED_Q, 'w', encoding='ascii') as f:
        f.write(q)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--uppaal', help='UPPAAL folder or path to verifyta')
    ap.add_argument('--timeout', type=int, default=3600, help='seconds per query (default 3600)')
    ap.add_argument('--max-n', type=int, default=20 * 4096, help='largest N tried for communication in time')
    ap.add_argument('--render-only', action='store_true')
    args = ap.parse_args()

    for tool in ('make_models.py', 'make_figures.py'):
        subprocess.run([sys.executable, os.path.join(HERE, tool)], check=True)

    if args.render_only:
        data = {}
        if os.path.exists(JSON_OUT):
            with open(JSON_OUT, encoding='utf-8') as f:
                data = json.load(f)
        render(data)
        return

    verifyta = find_verifyta(args.uppaal)
    v = subprocess.run([verifyta, '-v'], capture_output=True, text=True, errors='replace')
    version = (v.stdout or v.stderr).strip().splitlines()[0] if (v.stdout or v.stderr).strip() else 'unknown'
    print('verifyta:', verifyta)
    print('version :', version)
    check_runs(verifyta)

    data = {'uppaal_version': version, 'verifyta': verifyta,
            'run_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'host': f'{platform.system()} {platform.release()}, {platform.processor() or platform.machine()}',
            'checks': {}, 'complete': False}
    for cid, g, title, model, query, expected in CHECKS:
        print(f'[{cid}] {title}')
        r = run_verifyta(verifyta, model, query, cid, args.timeout)
        r.update({'title': title, 'model': model, 'query': query, 'expected': expected})
        data['checks'][cid] = r
        print(f'    {fmt_sat(r["satisfied"])}  explored={num(r["states_explored"])}  cpu={mmss(r["cpu_ms"])}')
        if expected is not None and r['satisfied'] is not expected:
            print(f'    NOTE: expected {fmt_sat(expected)}; reporting the actual result.')
    print('[comm_in_time] searching smallest N')
    data['comm'] = search_bound(verifyta, args.timeout, args.max_n)
    if data['comm'].get('found'):
        write_timed_queries(data['comm']['N'])
    data['complete'] = True
    os.makedirs(RESULTS, exist_ok=True)
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print('wrote', os.path.relpath(JSON_OUT, ROOT))
    write_md(data)
    render(data)


if __name__ == '__main__':
    main()
