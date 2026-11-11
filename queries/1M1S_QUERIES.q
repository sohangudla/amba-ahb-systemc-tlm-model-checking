// Queries for model/amba_AHB_1M1S.uppaal.xml (the original 1M1S model, unchanged)
// Paper: Pockrandt, Herber, Glesner, ESTIMedia 2011, Section VI-B and Table II (1M1S column).
// Results for each query are recorded by tools/run_all.py in results/results.md.

/*
Paper property 1: deadlock freedom (paper 1M1S: 0:07, 74,345 states)
*/
A[] not deadlock

/*
Paper property 3 for M1: a bus request is always eventually answered with a bus grant
(paper 1M1S: 0:05). Leads-to: whenever M1 has a pending bus request, it is eventually granted.
*/
AHB_M1$m_bus_req_pending --> AHB_M1$m_bus_granted

/*
Reachability only: there is at least one run in which M1 is granted the bus.
This does NOT show that M1 is always granted; the leads-to query above does that.
*/
E<> AHB_M1$m_bus_granted

/*
Extra: the arbiter never uses the master-2 grant value (bit 1), and the grant
register only ever holds 0 (idle) or 1 (M1). Paper properties 2 and the M2 half of 3
need a second master and do not apply to 1M1S.
*/
A[] AHB_Bus$m_InService_Register != 2

A[] AHB_Bus$m_InService_Register <= 1

/*
Extra: memory safety of the generated model.
*/
A[] not MEM_ERR_ACCESS_FAIL

A[] not MEM_ERR_DOUBLE_FREE

A[] not MEM_ERR_NOT_ENOUGH_MEM
