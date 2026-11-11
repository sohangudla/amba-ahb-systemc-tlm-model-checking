# 1M1S verification results

- UPPAAL: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023
- Run: 2026-11-10 14:53 on Windows 11, Intel64 Family 6 Model 154 Stepping 3, GenuineIntel

| Check | Model | Query | Result | Explored | Stored | CPU | Raw output |
|---|---|---|---|---|---|---|---|
| Deadlock freedom | amba_AHB_1M1S.uppaal.xml | `A[] not deadlock` | satisfied | 1,241,387 | 1,119,525 | 16.38 s | results/raw/deadlock.txt |
| Bus granted to M1 (leads-to) | amba_AHB_1M1S.uppaal.xml | `AHB_M1$m_bus_req_pending --> AHB_M1$m_bus_granted` | satisfied | 1,259,923 | 1,119,525 | 11.83 s | results/raw/grant_m1.txt |
| M1 can be granted the bus (reachability only) | amba_AHB_1M1S.uppaal.xml | `E<> AHB_M1$m_bus_granted` | satisfied | 501 | 464 | 0.01 s | results/raw/grant_m1_reach.txt |
| Arbiter never grants the unused master-2 slot | amba_AHB_1M1S.uppaal.xml | `A[] AHB_Bus$m_InService_Register != 2` | satisfied | 1,241,387 | 1,119,525 | 12.78 s | results/raw/m2_never.txt |
| Arbiter grant register only 0 or 1 | amba_AHB_1M1S.uppaal.xml | `A[] AHB_Bus$m_InService_Register <= 1` | satisfied | 1,241,387 | 1,119,525 | 17.16 s | results/raw/reg_range.txt |
| No invalid memory access | amba_AHB_1M1S.uppaal.xml | `A[] not MEM_ERR_ACCESS_FAIL` | satisfied | 1,241,387 | 1,119,525 | 16.55 s | results/raw/mem_access.txt |
| No double free | amba_AHB_1M1S.uppaal.xml | `A[] not MEM_ERR_DOUBLE_FREE` | satisfied | 1,241,387 | 1,119,525 | 36.83 s | results/raw/mem_double_free.txt |
| No out-of-memory | amba_AHB_1M1S.uppaal.xml | `A[] not MEM_ERR_NOT_ENOUGH_MEM` | satisfied | 1,241,387 | 1,119,525 | 42.38 s | results/raw/mem_out.txt |
| Timed model: deadlock freedom (instrumentation sanity check) | amba_AHB_1M1S_timed.uppaal.xml | `A[] not deadlock` | satisfied | 1,241,387 | 1,119,525 | 1:04.6 | results/raw/timed_deadlock.txt |
| Timed model: communication starts | amba_AHB_1M1S_timed.uppaal.xml | `E<> M1_isCommunicating` | satisfied | 501 | 464 | 0.02 s | results/raw/timed_grant_reach.txt |
| With reset: every started transfer completes | amba_AHB_1M1S_timed.uppaal.xml | `M1_isCommunicating --> !M1_isCommunicating` | satisfied | 1,799,151 | 1,119,525 | 1:13.4 | results/raw/txn_completes.txt |
| Without reset: deadlock freedom | amba_AHB_1M1S_timed_noreset.uppaal.xml | `A[] not deadlock` | satisfied | 57,806 | 52,628 | 0.69 s | results/raw/noreset_deadlock.txt |
| Without reset: every started transfer completes | amba_AHB_1M1S_timed_noreset.uppaal.xml | `M1_isCommunicating --> !M1_isCommunicating` | NOT satisfied | 41,403 | 17,687 | 0.42 s | results/raw/noreset_completes.txt |
| FIFO: deadlock freedom | test_fifo.uppaal.xml | `A[] not deadlock` | satisfied | 11,163 | 10,359 | 0.05 s | results/raw/fifo_deadlock.txt |
| FIFO: no invalid memory access | test_fifo.uppaal.xml | `A[] not MEM_ERR_ACCESS_FAIL` | satisfied | 11,163 | 10,359 | 0.02 s | results/raw/fifo_mem_access.txt |
| FIFO: no memory corruption | test_fifo.uppaal.xml | `A[] not MEM_ERR_CORRUPTED_MEM` | satisfied | 11,163 | 10,359 | 0.02 s | results/raw/fifo_mem_corrupt.txt |

## Communication in time (timed model)

Smallest N: **40** time units (2 clock periods). Explored 1,241,387, stored 1,119,525, CPU 13.02 s.

| N | Result | Raw output |
|---|---|---|
| 20 | NOT satisfied | results/raw/comm_N20.txt |
| 40 | satisfied | results/raw/comm_N40.txt |
| 30 | NOT satisfied | results/raw/comm_N30.txt |
| 35 | NOT satisfied | results/raw/comm_N35.txt |
| 37 | NOT satisfied | results/raw/comm_N37.txt |
| 38 | NOT satisfied | results/raw/comm_N38.txt |
| 39 | NOT satisfied | results/raw/comm_N39.txt |
