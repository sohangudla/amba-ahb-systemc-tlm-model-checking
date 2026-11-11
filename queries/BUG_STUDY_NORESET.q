// Queries for model/amba_AHB_1M1S_timed_noreset.uppaal.xml
// Same as the timed model, but the two "m_txn_count = 0" resets
// (tlm2_master_to_ahb.cpp lines 120 and 154 of the STATE-2.1 amba_AHB example) are removed.
// This recreates the bug described in Section VI-B of the paper.

/*
Deadlock freedom without the reset. A stuck transfer does not have to be a UPPAAL
deadlock, because the clock and scheduler keep running.
*/
A[] not deadlock

/*
Every started transfer completes. This is the property that should expose the missing reset.
*/
M1_isCommunicating --> !M1_isCommunicating
