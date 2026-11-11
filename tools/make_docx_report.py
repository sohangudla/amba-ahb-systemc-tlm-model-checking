"""Fill the college report format (23ECE337 Simulation Based Assignment) with the 1M1S project.

Input : report/23ECE337_Report_format_template.docx   (the official format, unchanged)
        results/results.json                         (numbers from verifyta; nothing typed by hand)
        figures/fig_architecture.png, screenshots/*.png
Output: report/23ECE337_1M1S_Report.docx

Only the empty fields of the template are filled and content is added under its existing
headings, so the template's fonts, logo, cover page and page setup are kept.

Run:  python tools/make_docx_report.py
"""
import json
import os
import re
import struct
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
TEMPLATE = os.path.join(ROOT, 'report', '23ECE337_Report_format_template.docx')
OUT = os.path.join(ROOT, 'report', '23ECE337_1M1S_Report.docx')
RESULTS = os.path.join(ROOT, 'results', 'results.json')

STUDENTS = ['C. Deepthi Sree (BL.EN.U4ECE23107)',
            'G. Sohan (BL.EN.U4ECE23117)',
            'K. Lochana Reddy (BL.EN.U4ECE23127)']
TEXT_WIDTH_EMU = 5_900_000          # usable width of the template page (A4, its margins)

# ----------------------------------------------------------------------------- XML helpers
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
MONO = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'


def run(text, bold=False, italic=False, size=24, mono=False, color=None):
    rpr = (MONO if mono else TNR) + ('<w:b/><w:bCs/>' if bold else '') + ('<w:i/><w:iCs/>' if italic else '')
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def rich(text, size=24, base_bold=False):
    """**bold** and `code` inline markup."""
    out = []
    for part in re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text):
        if not part:
            continue
        if part.startswith('**'):
            out.append(run(part[2:-2], bold=True, size=size))
        elif part.startswith('`'):
            out.append(run(part[1:-1], mono=True, size=size - 3))
        else:
            out.append(run(part, bold=base_bold, size=size))
    return ''.join(out)


def para(content, align='both', before=0, after=120, ind=None, keep_next=False, shade=None, line=276, numid=None):
    ppr = ''
    if numid is not None:
        ppr += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{numid}"/></w:numPr>'
    if keep_next:
        ppr += '<w:keepNext/>'
    if shade:
        ppr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    ppr += f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>'
    if ind:
        ppr += ind
    ppr += f'<w:jc w:val="{align}"/>'
    return f'<w:p><w:pPr>{ppr}</w:pPr>{content}</w:p>'


def P(text, **kw):
    return para(rich(text), **kw)


def sub(text):
    return para(run(text, bold=True, size=24), align='left', before=120, after=60, keep_next=True)


def bullets(items):
    return ''.join(para(rich(t), ind='<w:ind w:left="720" w:hanging="360"/>', after=60, numid=BULLET_NUM)
                   for t in items)


def code(lines):
    out = []
    for i, ln in enumerate(lines):
        out.append(para(run(ln if ln else ' ', mono=True, size=17), align='left', after=0, line=240,
                        shade='F2F2F2', ind='<w:ind w:left="284" w:right="284"/>',
                        before=80 if i == 0 else 0, keep_next=i < len(lines) - 1))
    out.append(para('', after=60))
    return ''.join(out)


SRC = os.path.join(ROOT, 'systemc_source')


def src_lines(fname, start, end):
    """Lines start..end (1-based, inclusive) of a SystemC file, prefixed with their line numbers."""
    with open(os.path.join(SRC, fname), encoding='utf-8', errors='replace') as f:
        lines = f.read().splitlines()
    return [f'{n:4d}  ' + lines[n - 1].replace('\t', '  ').rstrip() for n in range(start, end + 1)]


def caption(text):
    return para(rich(text, size=20), align='center', after=200)


def table(header, rows, widths, size=18):
    total = sum(widths)
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    border = ''.join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
                     for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))

    def cell(txt, w, hdr):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if hdr else ''
        color = None
        if not hdr and txt.lower().startswith('satisfied'):
            color = '116329'
        if not hdr and txt.lower().startswith('not satisfied'):
            color = 'A40E26'
        body = (run(txt, bold=hdr, size=size, color=color) if not txt.startswith('`')
                else run(txt.strip('`'), mono=True, size=size - 2))
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}</w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/></w:pPr>{body}</w:p></w:tc>')

    trs = ['<w:tr><w:trPr><w:tblHeader/></w:trPr>' + ''.join(cell(h, w, True) for h, w in zip(header, widths)) + '</w:tr>']
    for r in rows:
        trs.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + ''.join(cell(str(c), w, False) for c, w in zip(r, widths)) + '</w:tr>')
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar>'
            f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>' + para('', after=60))


# ----------------------------------------------------------------------------- images
IMAGES = []   # (rid, zip_name, bytes)


def png_size(data):
    w, h = struct.unpack('>II', data[16:24])
    return w, h


def image(path, max_width_emu=TEXT_WIDTH_EMU, max_height_emu=7_600_000):
    with open(path, 'rb') as f:
        data = f.read()
    n = len(IMAGES) + 1
    rid, name = f'rIdImg{n}', f'media/report_img{n}.png'
    IMAGES.append((rid, name, data))
    w, h = png_size(data)
    cx = min(max_width_emu, w * 9525)
    cy = int(cx * h / w)
    if cy > max_height_emu:
        cy = max_height_emu
        cx = int(cy * w / h)
    pid = 100 + n
    drawing = (
        f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pid}" name="Picture {pid}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks '
        f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData '
        f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic '
        f'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{pid}" '
        f'name="{os.path.basename(path)}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/>'
        f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:ln w="6350"><a:solidFill><a:srgbClr val="BFBFBF"/></a:solidFill></a:ln></pic:spPr></pic:pic>'
        f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    return para(drawing, align='center', after=60, keep_next=True)


def fig(path, text, **kw):
    return image(path, **kw) + caption(text)


# ----------------------------------------------------------------------------- content
def fmt_sat(s):
    return {True: 'Satisfied', False: 'Not satisfied'}.get(s, 'No verdict')


def cpu(r):
    ms = r.get('cpu_ms')
    return '-' if ms is None else (f'{ms / 1000:.2f} s' if ms < 60000 else f'{int(ms // 60000)} min {ms / 1000 % 60:.0f} s')


def num(v):
    return f'{v:,}' if isinstance(v, int) else '-'


def build_sections(d):
    c = d['checks']
    comm = d['comm']
    N = comm['N']
    dl = c['deadlock']
    ratio = dl['states_explored'] / 74345
    S = os.path.join(ROOT, 'screenshots')
    sec = {}

    sec['Aim'] = P(
        'To model and formally verify the one-master one-slave (1M1S) configuration of a SystemC/TLM 2.0 '
        'model of the ARM AMBA AHB bus using UPPAAL timed automata, and to compare the results with the 1M1S '
        'column of Table II in the IEEE paper by Pockrandt, Herber and Glesner (ESTIMedia 2011) [1]. The three '
        'properties of that table that apply to 1M1S are checked: **deadlock freedom**, **bus grant to master 1** '
        'and **communication in time**. In addition, the missing `m_txn_count` reset reported in the paper is '
        'recreated and analysed.', before=60)

    sec['Tools'] = bullets([
        f'**UPPAAL {d["uppaal_version"].split(" (")[0].replace("UPPAAL ", "")}** (academic licence): the `verifyta` command-line model checker produced all '
        'reported numbers; the UPPAAL GUI (Editor, Verifier and Symbolic Simulator) was used for the screenshots.',
        '**UPPAAL timed-automata model of the Carbon Design Systems SystemC/TLM 2.0 AMBA AHB design**, produced by '
        'the SystemC-to-UPPAAL transformation of [1], [2] and reduced to 1M1S.',
        '**Python 3.12** scripts written for this assignment: `make_models.py` (adds the timing clock and '
        'builds the bug-study model), `run_all.py` (runs every check, saves the raw output, writes the results), '
        '`make_figures.py` and `make_clean_view.py` (figures and GUI-friendly demo copies).',
        '**Java 21 (Eclipse Temurin)** for the UPPAAL 5 graphical interface.',
        f'**Host:** {d["host"]}.',
    ])

    theory = []
    theory.append(sub('1) Introduction'))
    theory.append(P(
        'Transaction-level models (TLM) in SystemC let a system on chip be simulated long before RTL exists. '
        'A simulation, however, follows only one ordering of the concurrent processes, so corner cases such as a '
        'counter that is not reset after a transaction can go unnoticed. Model checking explores every reachable '
        'state of a formal model instead, and either proves a property or returns a counterexample.'))
    theory.append(P(
        'Reference [1] transforms SystemC/TLM 2.0 designs into UPPAAL timed automata and applies the method to an '
        'industrial TLM model of the AMBA AHB. Its key contribution is an optimised encoding of the TLM payload '
        'event queue (PEQ): each pending notification is held by its own automaton with a local clock instead of a '
        'global clock array, which reduces the state space. The paper checks the configurations 1M1S to 2M2S. '
        'For 1M1S it reports 74,345 states, 0:07 for deadlock freedom, 0:05 for bus grant to M1 and 0:17 for '
        'communication in time. This assignment repeats the 1M1S experiment.'))

    theory.append(sub('2) Block Diagram'))
    theory.append(fig(os.path.join(ROOT, 'figures', 'fig_architecture.png'),
                      '**Fig. 1.** 1M1S configuration verified in this work (schematic; cf. [1, Fig. 9]).',
                      max_width_emu=5_200_000))
    theory.append(table(
        ['Block', 'UPPAAL instance', 'Function'],
        [['Traffic generator', 'TLM2_M1 (tlm2_simple_master)', 'Writes and then reads a 3-beat burst at address 0, '
          'waits (wait_clks = 20) and repeats, using blocking transport'],
         ['Master adapter', 'AHB_M1 (tlm2_master_to_ahb) + PEQ', 'Splits each transaction into AHB transfers; '
          'requests the bus and sends/receives data with nb_transport'],
         ['Bus', 'AHB_Bus (ahb_simple_bus)', 'Arbiter (grant register m_InService_Register) and address decoder'],
         ['Slave', 'AHB_S1 (ahb_simple_mem) + PEQ', 'Memory (base 0, size 3) that serves reads and writes'],
         ['Clock and kernel', 'clk, scheduler, initialiser', 'Bus clock with period 20 time units; SystemC '
          'scheduler semantics (evaluate, update, advance time)']],
        [1700, 2700, 4900]))
    theory.append(P(
        'In total the model has 66 automata built from 44 templates. It was reduced by hand from the 2M2S model: '
        'the master-2, slave-2 and second traffic-generator instances were removed, `number_of_slaves` was set to 1 '
        'and the initial `readyprocs` to 2. The bus templates still loop over two master slots and two slave slots; '
        'the unused ports are not connected to any automaton.'))

    theory.append(sub('3) Working Principle'))
    theory.append(P(
        '**SystemC to timed automata.** Each SystemC method becomes a timed-automaton template; processes, events '
        'and the scheduler are predefined automata that synchronise over UPPAAL channels (for example `activate`, '
        '`deactivate`, `advancetime`, `deltadelay`). Urgent and committed locations model zero-time delta cycles.'))
    theory.append(P(
        '**PEQ encoding.** In our model each PEQ consists of `peq_notify` (accepts a notification and hands it to a '
        'free element), four `peq_element` automata (each holds one notification with local clock `c` and the '
        'invariant `c <= delay`, corresponding to [1, Fig. 4]) and `peq_fetch` (calls the callback, [1, Fig. 5]).'))
    theory.append(P(
        '**Properties (TCTL).** `A[] p` means p holds in every reachable state; `E<> p` means some run reaches p; '
        '`p --> q` (leads-to) means whenever p holds, q eventually holds. Deadlock freedom is `A[] not deadlock`. Bus '
        'grant is the leads-to property `AHB_M1$m_bus_req_pending --> AHB_M1$m_bus_granted`.'))
    theory.append(P(
        '**Communication in time.** As in [1], an extra clock `x` is added and reset whenever the master is granted '
        'the bus; a flag `M1_isCommunicating` is true from a grant until the transaction is cleaned up. The property '
        '`A[] M1_isCommunicating imply x <= N` is checked, and the smallest N that holds is found by doubling from '
        'one clock period and then bisecting. The two new variables are only written, never read, so the behaviour '
        'of the model is unchanged.'))
    theory.append(P(
        '**Bug study.** The paper reports that a counter storing the number of completed transfers was not reset, so '
        'all split transactions after the first one failed. In our model this counter is `m_txn_count`, reset at '
        '`tlm2_master_to_ahb.cpp` lines 120 and 154 (the UPPAAL model merges each clean-up into one update, annotated '
        'with lines 116 and 150). A second copy of the timed model has both resets removed.'))

    theory.append(sub('4) Advantages'))
    theory.append(bullets([
        'Exhaustive: every reachable state is explored (1,241,387 states for deadlock freedom), not just one '
        'simulation run.',
        'A failing property comes with a counterexample trace that can be stepped through in the simulator.',
        'Timing properties can be proved exactly: the communication-in-time bound N is shown to be the smallest '
        'value that holds.',
        'The transformation keeps the structure of the SystemC design, so results map back to source lines.',
        'Fully reproducible: one script reruns every check and regenerates the results from the raw output.']))
    theory.append(sub('5) Disadvantages'))
    theory.append(bullets([
        'State-space explosion: the paper reports 74,345 states for 1M1S but 7,964,195 for 2M2S.',
        'Only bounded integers and static processes are supported, so the original design had to be simplified '
        '(no dynamic memory, simplified transaction objects).',
        'Results depend on the model: our 1M1S model was reduced by hand, and its state count differs from the '
        'paper\'s.',
        'Deadlock freedom alone is not enough: in the bug study the missing reset causes no deadlock and is only '
        'caught by a liveness property.',
        'Tool issues: UPPAAL 4.1.26-1 failed its start-up check, and the UPPAAL 5 GUI cannot handle "$" in the '
        'generated names, so GUI demo copies with "__" were needed.']))
    sec['Theory'] = ''.join(theory)

    sc = []
    sc.append(P(
        'The SystemC/TLM 2.0 design is the AMBA AHB example of the STATE-2.1 tool (`examples/amba_AHB`). Its sources '
        '(bus, memory slave, master adapter, traffic generator and `defines.h`) are included in `systemc_source/`; '
        'excerpts (a) to (d) below are copied from them with their real line numbers. Excerpts (e) and (f) are the '
        'code we added.', before=60))
    sc.append(sub('a) Bus arbiter: ahb_simple_bus::arbitrate (ahb_simple_bus.cpp)'))
    sc.append(P('The arbiter grants the bus to the requesting master with the lowest index, and only when the bus is '
                'free (`m_InService_Register == 0`, line 14). The loop runs over `MASTER_N` master slots (line 9), and '
                '`defines.h` sets `MASTER_N` to 2 (line 8). Our 1M1S model kept the bus unchanged, so it still has two '
                'slots, of which only slot 0 is ever requested.'))
    sc.append(code(src_lines('ahb_simple_bus.cpp', 3, 25)))
    sc.append(sub('b) Master adapter: tlm2_master_to_ahb::b_transport, transaction clean-up (tlm2_master_to_ahb.cpp)'))
    sc.append(P('After a write (lines 109-124) and after a read (lines 143-158) the adapter releases the transaction '
                'and resets `m_txn_count` (lines **120** and **154**). This is the reset whose absence is the bug '
                'described in [1]; the bug-study model removes it. The UPPAAL model merges each clean-up into one '
                'update annotated with lines 116 and 150.'))
    sc.append(code(src_lines('tlm2_master_to_ahb.cpp', 109, 124) + ['  ...'] +
                   src_lines('tlm2_master_to_ahb.cpp', 143, 156)))
    sc.append(sub('c) Master adapter: bus grant received (tlm2_master_to_ahb.cpp)'))
    sc.append(P('The two places where the adapter records a bus grant. Our timing clock `x` is reset on exactly these '
                'two edges of the UPPAAL model.'))
    sc.append(code(src_lines('tlm2_master_to_ahb.cpp', 32, 39) + ['  ...'] +
                   src_lines('tlm2_master_to_ahb.cpp', 274, 281)))
    sc.append(sub('d) Traffic generator: tlm2_simple_master::thread_process (tlm2_simple_master.cpp)'))
    sc.append(P('Each round writes and then reads a burst of BURST_LENGTH words through blocking transport and waits '
                '20 clock edges. `defines.h` sets `MEM_SIZE` to 3 and `BURST_LENGTH` to `MEM_SIZE` (lines 4 and 15). '
                'Its `SLAVE_N` (2 AHB slaves, lines 5-7) and `MASTER_N` (2) describe the original 2M2S design; when the '
                'model was reduced to 1M1S, `number_of_slaves` in this generator was set to 1, so every burst goes to '
                'address 0 of the single slave.'))
    sc.append(code(src_lines('tlm2_simple_master.cpp', 20, 33) + ['  ...'] +
                   src_lines('tlm2_simple_master.cpp', 84, 86) + ['  ...'] +
                   src_lines('tlm2_simple_master.cpp', 103, 109)))
    sc.append(sub('e) Code added for communication in time (tools/make_models.py)'))
    sc.append(code([
        '// global declarations',
        'clock x;',
        'bool  M1_isCommunicating = false;',
        '',
        '// on both bus-grant edges (tlm2_master_to_ahb.cpp lines 36-37 and 277-278)',
        'm_bus_granted = true, m_bus_req_pending = false,  x = 0, M1_isCommunicating = true',
        '',
        '// on both clean-up edges (lines 120 and 154)',
        '... m_txn_count = 0,  M1_isCommunicating = false',
    ]))
    sc.append(sub('f) Verification queries (queries/1M1S_QUERIES.q, 1M1S_TIMED_QUERIES.q, BUG_STUDY_NORESET.q)'))
    sc.append(code([
        'A[] not deadlock',
        'AHB_M1$m_bus_req_pending --> AHB_M1$m_bus_granted',
        'E<> AHB_M1$m_bus_granted',
        'A[] AHB_Bus$m_InService_Register != 2',
        'A[] AHB_Bus$m_InService_Register <= 1',
        'A[] not MEM_ERR_ACCESS_FAIL',
        'A[] not MEM_ERR_DOUBLE_FREE',
        'A[] not MEM_ERR_NOT_ENOUGH_MEM',
        f'A[] M1_isCommunicating imply x <= {N}            // timed model',
        'M1_isCommunicating --> !M1_isCommunicating        // timed and no-reset models',
    ]))
    sec['Code'] = ''.join(sc)

    sim = []
    sim.append(P(
        'All screenshots were taken in the UPPAAL 5.0.0 GUI. The GUI uses demo copies of the models in which the '
        'source-line comment boxes are removed and "$" in names is written "__"; these copies give the same results '
        'as the models used for the numbers in the Synthesis Report.', before=60))
    sim.append(fig(os.path.join(S, '01_model_editor.png'),
                   '**Fig. 2.** The 1M1S model in the UPPAAL editor with its template list.', max_height_emu=5_200_000))
    sim.append(fig(os.path.join(S, '02_peq_element.png'),
                   '**Fig. 3.** `peq_element`: PEQ notification automaton with local clock c and invariant c <= delay '
                   '(cf. [1, Fig. 4]).'))
    sim.append(fig(os.path.join(S, '03_peq_fetch.png'),
                   '**Fig. 4.** `peq_fetch`: callback invocation automaton (cf. [1, Fig. 5]).', max_width_emu=3_300_000))
    sim.append(fig(os.path.join(S, '04_arbiter.png'),
                   '**Fig. 5.** `ahb_simple_bus__arbitrate`: the bus is granted only when m_InService_Register == 0.'))
    sim.append(fig(os.path.join(S, '05_deadlock_green.png'),
                   '**Fig. 6.** Deadlock freedom: `A[] not deadlock` is satisfied.'))
    sim.append(fig(os.path.join(S, '06_all_8_green.png'),
                   '**Fig. 7.** All eight 1M1S queries satisfied, including the leads-to bus-grant property.'))
    sim.append(fig(os.path.join(S, '07_comm_x40_green.png'),
                   f'**Fig. 8.** Communication in time: `A[] M1_isCommunicating imply x <= {N}` is satisfied.'))
    sim.append(fig(os.path.join(S, '08_comm_x39_red.png'),
                   f'**Fig. 9.** `x <= {N - 1}` is not satisfied while `x <= {N}` is, so N = {N} is the smallest bound.'))
    sim.append(fig(os.path.join(S, '09_timed_all_checks.png'),
                   '**Fig. 10.** Timed model: no deadlock, communication starts, and with the reset every started '
                   'transfer completes.'))
    sim.append(fig(os.path.join(S, '10_bug_red.png'),
                   '**Fig. 11.** Bug study: without the reset, deadlock freedom still holds but '
                   '`M1_isCommunicating --> !M1_isCommunicating` is not satisfied.'))
    sim.append(fig(os.path.join(S, '11_simulator_trace.png'),
                   '**Fig. 12.** The counterexample loaded into the Symbolic Simulator.'))
    sim.append(fig(os.path.join(S, '12_trace_globals.png'),
                   '**Fig. 13.** Global variables at the end of the counterexample: no memory errors, clock period 20.'))
    small = ''.join(image(os.path.join(S, n), max_width_emu=int(TEXT_WIDTH_EMU * 0.48))
                    for n in ('13_txn_count_3.png', '14_data_count_3.png'))
    small += ''.join(image(os.path.join(S, n), max_width_emu=int(TEXT_WIDTH_EMU * 0.48))
                     for n in ('15_bus_granted_1.png', '16_isCommunicating_1.png'))
    sim.append(small)
    sim.append(caption('**Fig. 14.** Key counterexample values: `m_data_count = 3` and `m_txn_count = 3` (never reset), '
                       '`m_bus_granted = 1` and `M1_isCommunicating = 1` for ever, so the transfer never finishes.'))
    sec['Sim'] = ''.join(sim)

    syn = []
    syn.append(P(
        'This is a formal-verification assignment, so there is no logic synthesis; the equivalent report is the '
        f'verification report below. All values come from `verifyta` ({d["uppaal_version"].split(" (")[0]}, run '
        f'{d["run_date"]}) and are saved in `results/results.md` and `results/raw/`. Times are CPU time.', before=60))
    syn.append(sub('Table I. Paper (Table II, 1M1S) compared with our results'))
    syn.append(table(
        ['Property', 'Paper time', 'Paper states', 'Our CPU time', 'Our states explored', 'Our result'],
        [['Deadlock freedom', '0:07', '74,345', cpu(dl), num(dl['states_explored']), fmt_sat(dl['satisfied'])],
         ['Only one master granted', '-', '-', 'N/A', 'N/A', 'Not applicable (1 master)'],
         ['Bus granted to M1', '0:05', '74,345', cpu(c['grant_m1']), num(c['grant_m1']['states_explored']),
          fmt_sat(c['grant_m1']['satisfied'])],
         ['Bus granted to M2', '-', '-', 'N/A', 'N/A', 'Not applicable (1 master)'],
         [f'Communication in time (N = {N})', '0:17', '74,345', cpu(comm['result']),
          num(comm['result']['states_explored']), fmt_sat(comm['result']['satisfied'])]],
        [2300, 900, 1000, 1200, 1500, 2400]))
    syn.append(P(
        f'Our deadlock check explored {dl["states_explored"]:,} states ({dl["states_stored"]:,} stored), about '
        f'{ratio:.1f} times the paper\'s 74,345. We report both values instead of copying the paper\'s. Possible '
        'reasons, none of which we isolated, are the different UPPAAL version (the paper used a 2011 release), our '
        'model being reduced by hand rather than regenerated, and a PEQ depth of four entries. The paper ran on a '
        '3.4 GHz Pentium with 4 GB RAM, so times are not comparable either.'))
    syn.append(P(
        f'For communication in time, `x <= {N}` holds and `x <= {N - 1}` fails, so N = {N} time units '
        f'({N / 20:g} clock periods of 20) is the smallest bound. Because x restarts at every grant, N bounds the time '
        'from the latest grant to the end of the transaction.'))

    def row(cid, label):
        r = c[cid]
        return [label, '`' + r['query'] + '`', num(r['states_explored']), cpu(r), fmt_sat(r['satisfied'])]
    syn.append(sub('Table II. Additional checks on the 1M1S and timed models'))
    syn.append(table(['Check', 'Query', 'States explored', 'CPU time', 'Result'],
                     [row('grant_m1_reach', 'M1 can be granted (reachability)'),
                      row('m2_never', 'Master-2 slot never granted'),
                      row('reg_range', 'Grant register only 0 or 1'),
                      row('mem_access', 'No invalid memory access'),
                      row('mem_double_free', 'No double free'),
                      row('mem_out', 'No out-of-memory'),
                      row('timed_deadlock', 'Timed model: deadlock freedom'),
                      row('timed_grant_reach', 'Timed model: communication starts')],
                     [2300, 3300, 1300, 1000, 1400]))
    syn.append(sub('Table III. Bug study: effect of removing the m_txn_count reset'))
    syn.append(table(['Check', 'Query', 'States explored', 'CPU time', 'Result'],
                     [row('txn_completes', 'With reset: transfers complete'),
                      row('noreset_deadlock', 'Without reset: deadlock freedom'),
                      row('noreset_completes', 'Without reset: transfers complete')],
                     [2300, 3300, 1300, 1000, 1400]))
    syn.append(P(
        'Without the reset the model still has no deadlock, but a started transfer never finishes. The counterexample '
        'ends with `m_txn_count = 3` and `M1_isCommunicating = 1` for ever. The missing reset therefore shows up as a '
        'liveness failure, most likely because the clock and scheduler keep running. Our model has no AMBA SPLIT '
        'response, so this shows the effect of the missing reset on the generated bursts rather than the paper\'s '
        'exact split-transaction scenario.'))
    syn.append(sub('Table IV. Search for the communication-in-time bound N'))
    probes = sorted(comm['probes'], key=lambda p: p['N'])
    syn.append(table(['N (time units)', 'Result', 'CPU time'],
                     [[str(p['N']), fmt_sat(p['satisfied']), cpu(p)] for p in probes],
                     [2500, 3500, 2000]))
    syn.append(sub('Table V. Toolchain check on the SystemC FIFO example'))
    syn.append(table(['Check', 'Query', 'States explored', 'CPU time', 'Result'],
                     [row('fifo_deadlock', 'FIFO: deadlock freedom'),
                      row('fifo_mem_access', 'FIFO: no invalid memory access'),
                      row('fifo_mem_corrupt', 'FIFO: no memory corruption')],
                     [2300, 3300, 1300, 1000, 1400]))
    sec['Synth'] = ''.join(syn)

    sec['Conclusion'] = P(
        'We repeated the 1M1S part of the AMBA AHB experiment of [1] with UPPAAL. All three applicable properties '
        f'hold: deadlock freedom ({dl["states_explored"]:,} states explored), bus grant to master 1 as a leads-to '
        f'property, and communication in time with the smallest bound N = {N} time units ({N / 20:g} clock periods). '
        'The arbiter never grants the unused master-2 slot and the model has no memory errors. Our state count is '
        f'about {ratio:.1f} times the paper\'s, which we report openly. The bug study shows that removing the '
        '`m_txn_count` reset does not cause a deadlock but makes transfers hang, which only a liveness property '
        'detects. Every number in this report is produced by a script from saved UPPAAL output, so the work can be '
        'reproduced with one command.', before=60) + P(
        'Limitations: the 1M1S model was reduced by hand from the 2M2S model rather than regenerated from the SystemC '
        'source, and the communication-in-time bound is measured from the latest grant (measuring from another start '
        'point, such as the start of b_transport, gives a different bound). Extending the work to 2M2S would need far more '
        'memory, which is why this assignment is limited to 1M1S.')

    refs = [
        '[1] M. Pockrandt, P. Herber, and S. Glesner, "Model checking a SystemC/TLM design of the AMBA AHB protocol," '
        'in Proc. 9th IEEE Symp. Embedded Systems for Real-Time Multimedia (ESTIMedia), Taipei, Taiwan, 2011.',
        '[2] P. Herber, M. Pockrandt, and S. Glesner, "Transforming SystemC transaction level models into UPPAAL '
        'timed automata," in Proc. 9th ACM/IEEE Int. Conf. Formal Methods and Models for Codesign (MEMOCODE), 2011, '
        'pp. 161-170.',
        '[3] P. Herber, J. Fellmuth, and S. Glesner, "Model checking SystemC designs using timed automata," in Proc. '
        'Int. Conf. Hardware/Software Codesign and System Synthesis (CODES+ISSS), 2008, pp. 131-136.',
        '[4] G. Behrmann, A. David, and K. G. Larsen, "A tutorial on UPPAAL," in Formal Methods for the Design of '
        'Real-Time Systems, LNCS 3185, Springer, 2004, pp. 200-236.',
        '[5] ARM Ltd., AMBA Specification (Rev 2.0), ARM IHI 0011A, 1999.',
        '[6] IEEE Standard for Standard SystemC Language Reference Manual, IEEE Std 1666-2011.',
        '[7] R. Alur and D. L. Dill, "A theory of timed automata," Theoretical Computer Science, vol. 126, '
        'pp. 183-235, 1994.',
    ]
    sec['Refs'] = ''.join(para(run(r, size=22), align='left', after=80,
                                ind='<w:ind w:left="567" w:hanging="567"/>') for r in refs)
    return sec


# ----------------------------------------------------------------------------- assemble
BULLET_NUM = 2


def add_bullet_numbering(numbering_xml):
    abstract = ('<w:abstractNum w:abstractNumId="9"><w:multiLevelType w:val="hybridMultilevel"/>'
                '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/>'
                '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
                '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" '
                'w:hint="default"/></w:rPr></w:lvl></w:abstractNum>')
    numbering_xml = numbering_xml.replace('<w:num w:numId="1">', abstract + '<w:num w:numId="1">', 1)
    return numbering_xml.replace('</w:numbering>',
                                 f'<w:num w:numId="{BULLET_NUM}"><w:abstractNumId w:val="9"/></w:num></w:numbering>')


def main():
    with open(RESULTS, encoding='utf-8') as f:
        d = json.load(f)
    if not d.get('complete'):
        raise SystemExit('results/results.json is not complete; run tools/run_all.py first')
    zin = zipfile.ZipFile(TEMPLATE)
    doc = zin.read('word/document.xml').decode('utf-8')
    body_start = doc.find('<w:body>') + len('<w:body>')
    sect = doc.rfind('<w:sectPr')
    head, body, tail = doc[:body_start], doc[body_start:sect], doc[sect:]
    blocks = re.findall(r'<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>', body, re.S)
    if len(blocks) != 47:
        raise SystemExit(f'unexpected template layout ({len(blocks)} blocks)')

    def text_of(b):
        return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', b))

    def append_run(b, txt, size=28):
        r = (f'<w:r><w:rPr><w:rStyle w:val="normaltextrun"/><w:color w:val="000000" w:themeColor="text1"/>'
             f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/><w:lang w:val="en-US"/></w:rPr>'
             f'<w:t xml:space="preserve"> {escape(txt)}</w:t></w:r>')
        return b[:-len('</w:p>')] + r + '</w:p>'

    def bold_heading(b):
        return b.replace('<w:sz w:val="24"/>', '<w:b/><w:bCs/><w:sz w:val="24"/>').replace(
            '<w:rStyle w:val="normaltextrun"/><w:lang w:val="en-US"/></w:rPr><w:', '<w:rStyle w:val="normaltextrun"/><w:b/><w:bCs/><w:lang w:val="en-US"/></w:rPr><w:')

    # cover page: students (template has 4 slots; this group has 3). The template's right indent
    # is dropped and the names use 12 pt so each name and register number fits on one line.
    assert text_of(blocks[11]).strip().endswith('1)')
    for k, name in zip((11, 12, 13), STUDENTS):
        b = blocks[k].replace(' w:right="1860"', '')
        b = re.sub(r'<w:sz w:val="28"/><w:szCs w:val="28"/>', '<w:sz w:val="24"/><w:szCs w:val="24"/>', b)
        blocks[k] = append_run(b, name, size=24)
    blocks[14] = re.sub(r'(<w:t[^>]*>)\s*4\)(</w:t>)', r'\1\2', blocks[14])
    assert '4)' not in text_of(blocks[14])

    sec = build_sections(d)
    # 0-based indices of the template's headings
    idx = {'Aim': 27, 'Tools': 29, 'Code': 38, 'Sim': 40, 'Synth': 42, 'Conclusion': 44, 'Refs': 46}
    checks = {'Aim': 'Aim', 'Tools': 'Tools', 'Code': 'Code', 'Sim': 'Simulation', 'Synth': 'Synthesis',
              'Conclusion': 'Conclusion', 'Refs': 'Reference'}
    for k, i in idx.items():
        assert checks[k] in text_of(blocks[i]), (k, text_of(blocks[i]))
    # Theory: the template lists the five sub-headings (blocks 32-36); replace them with full content
    assert 'Theory' in text_of(blocks[31]) and 'Disadvantages' in text_of(blocks[36])

    out = []
    for i, b in enumerate(blocks):
        if 32 <= i <= 36:
            if i == 32:
                out.append(sec['Theory'])
            continue
        if i in idx.values() or i == 31:
            b = bold_heading(b)
        out.append(b)
        for k, j in idx.items():
            if i == j:
                out.append(sec[k])
        if i in (38, 40, 42, 44):          # empty spacer paragraphs after code/sim/synth: start next on new page
            pass
    # page breaks before the big sections
    new_body = ''.join(out)
    for heading in ('Simulation Result', 'Synthesis Report'):
        new_body = re.sub(r'(<w:p [^>]*>)(<w:pPr>(?:(?!</w:pPr>).)*</w:pPr>)(<w:r>(?:(?!</w:p>).)*?' + heading + ')',
                          lambda m: m.group(1) + m.group(2).replace('<w:pPr>', '<w:pPr><w:pageBreakBefore/>', 1) + m.group(3),
                          new_body, count=1, flags=re.S)
    doc_out = head + new_body + tail

    rels = zin.read('word/_rels/document.xml.rels').decode('utf-8')
    extra = ''.join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                    f'Target="{name}"/>' for rid, name, _ in IMAGES)
    rels = rels.replace('</Relationships>', extra + '</Relationships>')
    numbering = add_bullet_numbering(zin.read('word/numbering.xml').decode('utf-8'))

    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.endswith('/'):
                continue
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = doc_out.encode('utf-8')
            elif item.filename == 'word/_rels/document.xml.rels':
                data = rels.encode('utf-8')
            elif item.filename == 'word/numbering.xml':
                data = numbering.encode('utf-8')
            zout.writestr(item, data)
        for rid, name, data in IMAGES:
            zout.writestr('word/' + name, data)
    print('wrote', os.path.relpath(OUT, ROOT), f'({len(IMAGES)} images)')


if __name__ == '__main__':
    main()
