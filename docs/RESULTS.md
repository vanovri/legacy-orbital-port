# Local verification, 19 October 2026

These are recorded results from the repository's real executables under WSL Ubuntu
26.04 x86-64. They are measurements for these compiler/flag combinations, not
promises of bitwise portability. Re-run the referee to verify another environment.

| Check | Optimized | Checked |
| --- | --- | --- |
| GNU Fortran | 15.2.0 | 15.2.0 |
| GNU C++ | 15.2.0 | 15.2.0 |
| Rust | 1.93.1 | 1.93.1 |
| Main scenarios | 27 passed | 27 passed |
| Additional trajectory samples | 101 passed | 101 passed |
| Maximum port discrepancy, scaled metric | 0.0 | 0.0 |
| Strict parity gate | < 1e-12 | < 1e-12 |
| Independent circular/free-drift oracles | passed | passed |
| RK4 convergence and invariant checks | passed | passed |
| Invalid input/singular-stage cases per language | 14 rejected | 14 rejected |
| Supplied implicit-integer regression | rejected | rejected |

Ten output-gate unit tests passed in Linux Python and Windows Python. The
machine-readable reports contain full states, measured oracle errors, convergence
ratios, flags, compiler versions, source/referee hashes, and warning diagnostics.

For the optimized run, the independent circular-orbit scaled error at a one-second
timestep was approximately `4.55e-13`. Halving 40-second and 20-second timesteps
reduced error by factors `16.98` and `16.51`, consistent with fourth-order global
convergence over the tested interval.

The supplied 1,000-step program produced position `(3196907.00000003,
6421571.49999997)` meters. The corrected double-precision reference produced
`(2883588.5477393656, 6134218.302223325)` meters. This is a deliberate negative
control. The correction is documented separately from the subsequent port parity.

See the Actions page for fresh CI status. A checked-in local report is not evidence
that an uninspected remote CI run passed.
