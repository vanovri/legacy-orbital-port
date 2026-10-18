# Bounded numerical migration prompt

This is a reusable prompt template. It is not evidence of an unattended agent run.

```text
Migrate the approved legacy numerical solver to safe Rust and C++20 while preserving
the documented physical model, numerical algorithm, units, and input/output contract.

Before editing, run:
  python -m unittest discover -s tests -v
  python verify_parity.py --report reports/baseline.json
  python verify_parity.py --profile checked --report reports/baseline-checked.json

Record source hashes, compiler versions, and the verification result. If the legacy
baseline fails an independent oracle, stop migration and document the reference defect
before proposing a separately reviewable correction. Never silently redefine parity.

Freeze verify_parity.py, tests/, tolerance, and oracle definitions for the migration
attempt. Permitted edits: orbital_solver.rs, orbital_solver.cpp, and explanatory docs.
No unsafe Rust, mutable globals in migrated implementations, raw pointer arithmetic,
fast-math, test removal, fixture replacement, or precomputed solver outputs.

After each change, run both profiles and negative controls. Accept only when every
gate passes, including exact output shape, finite values, parity strictly below
1e-12 in the documented scaled metric, analytic checks, RK4 convergence, invariants,
invalid-input rejection, and reproduction of the supplied reference defect.

Allow at most 5 edit/check attempts and 20 minutes. Preserve failing diagnostics and
stop with an incomplete result if the limit is reached. Do not install dependencies,
access network services, change credentials, publish, or alter unrelated files.

Return the reviewed diff, commands, compiler versions, source/report hashes,
measured results, and limitations. Do not claim bitwise portability, historical
source provenance, validated orbital flight software, or a particular model's
performance from these tests.
```
