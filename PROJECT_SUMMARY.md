# 23ECE337 SoC Project: 1M1S AMBA AHB verification with UPPAAL

C. Deepthi Sree (BL.EN.U4ECE23107), G. Sohan (BL.EN.U4ECE23117), K. Lochana Reddy (BL.EN.U4ECE23127)

This folder holds everything needed to submit and demonstrate the project.

## What is in this folder

| Item | Purpose |
|---|---|
| `report/23ECE337_1M1S_Report.docx` / `.pdf` | **Submit this.** Report in the college format (23ECE337 template) with the real results and screenshots |
| `report/1M1S_Report.pdf` | Same work as an IEEE-style paper |
| `UPPAAL_Screenshots.pdf` | **Submit with the report.** 16 captioned UPPAAL screenshots of every check |
| `screenshots/` | The individual screenshot images and the HTML source of the PDF |
| `report/1M1S_Report.html`, `report/report_template.html` | IEEE-style report as a web page, and its editable text |
| `model/amba_AHB_1M1S.uppaal.xml` | The 1M1S UPPAAL model (unchanged) |
| `model/amba_AHB_1M1S_timed.uppaal.xml` | Model + clock `x` for communication in time |
| `model/amba_AHB_1M1S_timed_noreset.uppaal.xml` | Model without the `m_txn_count` reset (bug study) |
| `model/test_fifo.uppaal.xml` | Small FIFO example (toolchain check) |
| `model/demo_view/`, `queries/demo_view/` | Copies for the UPPAAL 5 GUI (no comment boxes, `$` written `__`) |
| `queries/` | Query files to load in the UPPAAL Verifier tab |
| `results/results.md` | All measured numbers (use as your sheet in the demo) |
| `results/raw/` | Raw UPPAAL output for every check (proof of the numbers) |
| `figures/` | Figures used in the reports |
| `tools/` | Scripts that build the models, figures, results and reports |
| `systemc_source/` | SystemC sources of the design (bus, memory slave, master adapter, traffic generator, `defines.h`) |
| `reference_paper/` | The IEEE ESTIMedia 2011 base paper |
| `DEMO_GUIDE.txt` | Step-by-step script for the evaluation |
| `LAUNCH_UPPAAL.bat` | Opens UPPAAL on the 1M1S demo model |
| `uppaal_path.txt` | Where UPPAAL 5.0 is installed (change it on another PC; see README.md) |

## What was done

1. Reviewed the team's earlier work. Problems found there: the paper's numbers were shown as our
   results; communication in time was never checked; bus grant used `E<>` instead of leads-to; the
   bug demo did not reproduce; and some code excerpts and references could not be matched to the
   design or the paper. (A copy of UPPAAL 4.1.26 in that earlier working folder had also been
   modified; it was not used for any result here.)
2. Rebuilt the project: added the paper's clock `x` to a copy of the model, wrote correct queries,
   made a no-reset copy for the bug study, drew figures from the model, and wrote scripts that run
   every check and fill both reports from UPPAAL's output.
3. Ran everything on the official, licensed UPPAAL 5.0.0 (10 Nov 2026). A teammate re-ran
   N = 40, N = 39 and the bug-study check with UPPAAL 5.0.0 on another PC and got the same results,
   and the same 1,241,387 states for deadlock freedom.

## Results (UPPAAL 5.0.0)

| Property | Paper (1M1S) | Ours |
|---|---|---|
| Deadlock freedom | 0:07, 74,345 states | Satisfied, 16.4 s, 1,241,387 states explored |
| Bus granted to M1 (leads-to) | 0:05 | Satisfied, 11.8 s |
| Communication in time | 0:17 | Satisfied with N = 40 time units (2 clock periods); N = 39 fails |
| Only one master / bus granted to M2 | - | Not applicable (no second master) |

- Bug study: without the `m_txn_count` reset (`tlm2_master_to_ahb.cpp` lines 120 and 154),
  deadlock freedom still holds but "every started transfer completes" fails, so the bug shows up as
  a transfer that never finishes.
- Extra checks: master-2 slot never granted; no memory errors; FIFO check passes (11,163 states).
- Our state count is about 16.7 times the paper's. The report gives both and explains possible reasons.
- N = 40 is measured from the latest bus grant to the end of the transaction, as in the paper. Measuring
  from another point (for example the start of `b_transport`) gives a different bound; the team uses 40.

## What is left

1. Fill in Date of Evaluation, Batch Number and Faculty In-charge on the cover of
   `report/23ECE337_1M1S_Report.docx`, then save it again as PDF.
2. Optionally add page numbers for references [1] and [2] from IEEE Xplore.

## Before the demo

1. Install Java 21 (Temurin 21 from https://adoptium.net); the UPPAAL 5 GUI needs it.
2. Renew the UPPAAL licence a day before (the 7-day lease ends about 17 Nov 2026). In PowerShell in the
   UPPAAL `bin` folder: `powershell -ExecutionPolicy Bypass -File .\lease-update.ps1 YOUR_KEY 168`, then type Y.
3. On the demo PC, set `uppaal_path.txt` (or unzip UPPAAL into `uppaal\` inside this folder) and
   double-click `LAUNCH_UPPAAL.bat`. It was tested on K. Lochana Reddy's PC on 10 Nov 2026.
4. Read `DEMO_GUIDE.txt` and keep `results/results.md` open.

## During the demo (details in DEMO_GUIDE.txt)

1. Open `model/demo_view/amba_AHB_1M1S_clean.uppaal.xml`; show `peq_element`, `peq_fetch` and the arbiter.
2. Verifier tab: File > Import Queries > `queries/demo_view/1M1S_QUERIES.q`; check `A[] not deadlock`
   and the leads-to bus-grant query.
3. Open the timed demo model with `queries/demo_view/1M1S_TIMED_QUERIES.q`; check `x <= 40` (and `x <= 39` fails).
4. If asked: the bug study (no-reset demo model with `queries/demo_view/BUG_STUDY_NORESET.q`) and the FIFO check.
5. Points to make: our state count differs from the paper's and we report both; master-2
   properties do not apply to 1M1S; we used UPPAAL 5.0 because 4.1.26-1 failed its start-up check.
