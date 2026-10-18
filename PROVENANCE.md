# Provenance and reference correction

This project adapts a user-supplied educational Fortran/Rust/C++ RK4 example.
Development and verification used Codex assistance. No Gemini model invocation or
Google demo reproduction was performed. The inspiration is a legacy-code migration
exercise. The source has no authenticated historical provenance and is not described
as actual 1960s flight software.

The original Fortran program is preserved in
`tests/fixtures/supplied_implicit_integer.f`. Its original comments are retained as
part of the regression fixture, not adopted as provenance claims. It uses a labelled
conditional/unconditional GOTO loop, not the three-way arithmetic IF or computed GOTO.

## Changes made before establishing the migration reference

1. Explicitly declare all sixteen RK4 `K` stage variables as double precision.
   `IMPLICIT DOUBLE PRECISION (A-H,O-Z)` leaves names starting with I through N as
   integers. The supplied code therefore truncated velocities and accelerations.
   The referee compiles that exact fixture, records conversion warnings and its
   result, then requires the faulty result to fail comparison with the corrected
   reference at the fixture's original 1,000 steps.
2. Set the default step count to 10,000, matching the requested verification target.
   All three supplied programs originally used 1,000.
3. Add optional one-line simulation input, input bounds, finite-result checks, and
   singular-radius rejection. The fixed-form COMMON/GOTO numerical core remains.
   `IEEE_ARITHMETIC`, I/O status handling, and the output edit descriptor require a
   modern compiler. This is not a claim of strict FORTRAN 66 or FORTRAN 77 compliance.
4. Print seventeen digits after the decimal in scientific notation. Compare a
   four-component finite state under a strict, documented threshold. Do not accept
   empty output, truncated vectors, NaN, Infinity, or extra log tokens as a pass.
5. Keep the RK4 stage order and force law in all ports. Use `std::array<double, 2>`
   for C++ acceleration and a constexpr default configuration. Do not label
   `std::sqrt` a portable C++20 constexpr calculation.

## Ownership boundary

The examples and test states are synthetic. No shared thesis firmware, measurements,
private company source, account data, photographs, or institutional files are used.
The MIT license covers this repository's educational implementation and supplied
example adaptation. Runtime/compiler licenses remain their own.

## References

- GNU Fortran compiler flags and fixed-form source rules:
  https://gcc.gnu.org/onlinedocs/gfortran/Fortran-Dialect-Options.html
- Safe/unsafe Rust boundary and `forbid(unsafe_code)`:
  https://doc.rust-lang.org/stable/nomicon/safe-unsafe-meaning.html
- Independent circular-orbit solution: insert
  `x = r*cos(omega*t), y = r*sin(omega*t), omega = sqrt(gm/r^3)` into
  `d2(position)/dt2 = -gm*position/r^3`. The referee uses this closed form rather
  than a fourth copy of the RK4 implementation.
