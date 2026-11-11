// Queries for model/amba_AHB_1M1S_timed.uppaal.xml
// (the 1M1S model plus clock x and flag M1_isCommunicating; see tools/make_models.py)

/*
Paper property 4: as soon as the master is granted the bus, communication never takes
more than N time units (paper 1M1S: 0:17). tools/run_all.py finds the smallest N that
holds and writes it into this file. One bus clock period is 20 time units.
*/
A[] M1_isCommunicating imply x <= 40

/*
Sanity checks: the added clock does not introduce a deadlock, and communication does start.
*/
A[] not deadlock

E<> M1_isCommunicating

/*
Bug study, part 1: with the m_txn_count reset in place, every started transfer completes.
*/
M1_isCommunicating --> !M1_isCommunicating
