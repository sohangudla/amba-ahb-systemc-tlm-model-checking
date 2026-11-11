"""Build the derived 1M1S models from the unchanged original.

Inputs : model/amba_AHB_1M1S.uppaal.xml            (original 1M1S model, never edited)
Outputs: model/amba_AHB_1M1S_timed.uppaal.xml      (adds clock x for "communication in time")
         model/amba_AHB_1M1S_timed_noreset.uppaal.xml (same, with the m_txn_count reset removed,
                                                      used only to study the paper's bug)

What the timed model adds (nothing else changes):
  * global  clock x;  bool M1_isCommunicating = false;
  * on both edges where the master adapter records a bus grant
    (m_bus_granted = true, tlm2_master_to_ahb.cpp lines 36-37 and 277-278):
        x = 0, M1_isCommunicating = true
    This follows the paper: "x is an extra clock, which is reset whenever a master is
    granted the bus".
  * on both transaction clean-up edges in b_transport
    (tlm2_master_to_ahb.cpp lines 120 and 154, where m_txn_count = 0;
    see systemc_source/; the model annotates each merged clean-up update with lines 116 and 150):
        M1_isCommunicating = false
The added variables are only written, never read by the model, so the behaviour of the
original automata is unchanged; the extra clock does enlarge the symbolic state space.

Run:  python tools/make_models.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, '..', 'model')
SRC = os.path.join(MODEL_DIR, 'amba_AHB_1M1S.uppaal.xml')
TIMED = os.path.join(MODEL_DIR, 'amba_AHB_1M1S_timed.uppaal.xml')
NORESET = os.path.join(MODEL_DIR, 'amba_AHB_1M1S_timed_noreset.uppaal.xml')

GLOBAL_ADDITION = (
    '\n// ---- Added for the 1M1S report (communication-in-time property) ----\n'
    '// x is reset whenever master 1 is granted the bus; M1_isCommunicating is true from a\n'
    '// grant until the current b_transport transaction is cleaned up.\n'
    'clock x;\n'
    'bool M1_isCommunicating = false;\n'
)

GRANT_RE = re.compile(r'(<label kind="assignment"[^>]*>)(m_bus_granted = true,\s*m_bus_req_pending = false)(</label>)')
CLEANUP_RE = re.compile(
    r'(<label kind="assignment"[^>]*>)(delete_dynamic_data\(current_trans\),\s*current_trans = NULL,\s*'
    r'current_DataLength = 0,\s*m_txn_count = 0)(</label>)')


def fail(msg):
    sys.exit('make_models.py: ' + msg)


def build_timed(src_text):
    if re.search(r'(?<![\w$])x(?![\w$])\s*[;=,)]', re.sub(r'\s[xy]="-?\d+"', '', src_text)):
        fail('identifier "x" already used in the model; choose another clock name')
    if 'M1_isCommunicating' in src_text:
        fail('model already contains M1_isCommunicating; start from the original model')

    end = src_text.find('</declaration>')
    if end < 0 or src_text.find('<template>') < end:
        fail('could not locate the global declaration')
    text = src_text[:end] + GLOBAL_ADDITION + src_text[end:]

    text, n_grant = GRANT_RE.subn(lambda m: m.group(1) + m.group(2) + ',\nx = 0,\nM1_isCommunicating = true' + m.group(3), text)
    if n_grant != 2:
        fail(f'expected 2 bus-grant edges, found {n_grant}')
    text, n_clean = CLEANUP_RE.subn(lambda m: m.group(1) + m.group(2) + ',\nM1_isCommunicating = false' + m.group(3), text)
    if n_clean != 2:
        fail(f'expected 2 transaction clean-up edges, found {n_clean}')
    return text


def build_noreset(timed_text):
    pat = re.compile(r'(current_DataLength = 0),\s*m_txn_count = 0(,\s*M1_isCommunicating = false)')
    text, n = pat.subn(r'\1\2', timed_text)
    if n != 2:
        fail(f'expected to remove 2 m_txn_count resets, removed {n}')
    return text


def main():
    with open(SRC, encoding='utf-8-sig') as f:
        src = f.read()
    timed = build_timed(src)
    noreset = build_noreset(timed)
    for path, text in ((TIMED, timed), (NORESET, noreset)):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print('wrote', os.path.relpath(path, os.path.join(HERE, '..')))


if __name__ == '__main__':
    main()
