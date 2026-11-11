# Model Checking a SystemC/TLM AMBA AHB Design with UPPAAL (23ECE337 SoC)

C. Deepthi Sree (BL.EN.U4ECE23107), G. Sohan (BL.EN.U4ECE23117), K. Lochana Reddy (BL.EN.U4ECE23127)

This folder repeats the 1M1S part of Pockrandt, Herber and Glesner, "Model Checking a
SystemC/TLM Design of the AMBA AHB Protocol" (ESTIMedia 2011), Table II, with UPPAAL.
See `PROJECT_SUMMARY.md` for the results and `DEMO_GUIDE.txt` for the demo.

## Status

All checks have been run with UPPAAL 5.0.0 (results in `results/results.md`, raw verifyta
output in `results/raw/`). The three applicable paper properties hold: deadlock freedom
(1,241,387 states explored), bus grant to M1 (leads-to), and communication in time with
N = 40 time units (N = 39 fails). A teammate reproduced N = 40, N = 39 and the bug-study result
on another PC.

## Folder layout

| Path | What it is |
|---|---|
| `report/23ECE337_1M1S_Report.docx` / `.pdf` | Report in the college format |
| `report/1M1S_Report.pdf` | Same work as an IEEE-style paper |
| `UPPAAL_Screenshots.pdf` | 16 captioned UPPAAL GUI screenshots |
| `model/amba_AHB_1M1S.uppaal.xml` | The 1M1S UPPAAL model (unchanged) |
| `model/amba_AHB_1M1S_timed.uppaal.xml` | Same model + clock `x` and flag `M1_isCommunicating` (generated) |
| `model/amba_AHB_1M1S_timed_noreset.uppaal.xml` | Timed model without the `m_txn_count` resets (bug study, generated) |
| `model/test_fifo.uppaal.xml` | Small FIFO example (toolchain check) |
| `model/demo_view/` | GUI copies: comment boxes removed, `$` written `__` (UPPAAL 5 GUI cannot handle `$`) |
| `queries/`, `queries/demo_view/` | Query files for the models and for the GUI copies |
| `tools/` | Scripts: `make_models.py`, `run_all.py`, `make_figures.py`, `make_clean_view.py`, `make_docx_report.py` |
| `results/` | `results.json`, `results.md`, `raw/` (the `raw/` files record the paths of the PC they ran on) |
| `screenshots/`, `figures/` | Images used in the reports |
| `systemc_source/` | SystemC sources of the design: bus, memory slave, master adapter, traffic generator and `defines.h` (STATE-2.1 `examples/amba_AHB`) |
| `2M2S_evaluation/` | The authors' 2M2S model, grant/FIFO query files and verifyta log |
| `TOOLCHAIN_EVALUATION_REPORT.md` | STATE 2.1 SystemC-to-UPPAAL toolchain evaluation |

The base paper is not included (IEEE copyright): Pockrandt, Herber, Glesner, ESTIMedia 2011.

## Running it on any PC

1. Install UPPAAL 5.0 and activate your own academic licence (in its `bin` folder):
   `powershell -ExecutionPolicy Bypass -File .\lease-update.ps1 YOUR_KEY 168`.
   The lease lasts 7 days, so renew it the day before a demo.
2. Tell the project where UPPAAL is, in either way:
   - create `uppaal_path.txt` containing the UPPAAL folder (the one with `uppaal.jar`)
     (absolute, or relative to this folder), or
   - unzip UPPAAL into a folder named `uppaal` inside this folder.
3. Re-run everything (Python 3, several minutes): `python tools/run_all.py`
4. Rebuild the reports after editing text: `python tools/run_all.py --render-only` and
   `python tools/make_docx_report.py`
5. GUI demo (needs Java 21, e.g. Eclipse Temurin 21): double-click `LAUNCH_UPPAAL.bat`
   and follow `DEMO_GUIDE.txt`. Tested on K. Lochana Reddy's PC on 10 Nov 2026; test it on
   the demo PC beforehand.

## Notes on the model

- The 1M1S model was reduced by hand from the 2M2S model (not regenerated with STATE). The bus
  templates still loop over two masters and two slaves; the master-2 and slave-2 ports are
  left unconnected. `number_of_slaves` is 1 and the initial `readyprocs` is 2.
  `systemc_source/defines.h` still shows the original 2M2S values (`MASTER_N 2`, `SLAVE_N` = 2),
  which is why the bus keeps two master slots.
- The `m_txn_count = 0` resets are at lines 120 and 154 of `systemc_source/tlm2_master_to_ahb.cpp`
  (STATE-2.1 `examples/amba_AHB`). The UPPAAL model merges each clean-up block into one update
  and annotates it with lines 116 and 150. The bus-grant edges are lines 36-37 and 277-278.
- The model has no AMBA SPLIT response. The paper's "split" means a transaction split into
  several transfers.
- Communication in time: clock `x` is reset at every bus grant, as in the paper, so N = 40 is
  the time from the latest grant to the end of the transaction. Measuring from another point
  (for example the start of `b_transport`) gives a different bound; the team uses N = 40.
