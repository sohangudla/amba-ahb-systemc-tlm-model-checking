// Queries for model/test_fifo.uppaal.xml (toolchain check on a small SystemC FIFO example)

/*
Deadlock freedom
*/
A[] not deadlock

/*
No invalid memory access
*/
A[] not MEM_ERR_ACCESS_FAIL

/*
No memory corruption
*/
A[] not MEM_ERR_CORRUPTED_MEM
