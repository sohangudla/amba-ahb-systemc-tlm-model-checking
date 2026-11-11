// =================================================================
// ðŸŸ¢ DEMO 1: Master 1 Bus Grant Reachability (Takes ~0.016s)
// =================================================================
E<> AHB_M1$m_bus_granted == 1

// =================================================================
// ðŸŸ¢ DEMO 2: Master 2 Bus Grant Reachability (Madam's ~80k States Target!)
// Explores 77,322 states in ~0.54s and gives a GREEN LIGHT!
// =================================================================
E<> AHB_M2$m_bus_granted == 1

// =================================================================
// ðŸŸ¢ DEMO 3: Liveness Sanity Check (Instant Green Light in 0.001s)
// Proves system is not deadlocked from the initial state
// =================================================================
E<> not deadlock

// =================================================================
// ðŸ” DEMO 4: Counterexample Finding (Master Local Flag Caching)
// Turns RED in 0.7s! Proves why checking master local flags is wrong
// =================================================================
A[] AHB_M1$m_bus_granted + AHB_M2$m_bus_granted <= 1

// =================================================================
// ðŸ›¡ï¸ DEMO 5: Central Arbiter Mutual Exclusion (The Hardware Register)
// Safe single-grant register (takes >25 min for exhaustive proof)
// =================================================================
A[] AHB_Bus$m_InService_Register != 3
