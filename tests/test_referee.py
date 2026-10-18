"""Negative controls for the acceptance gate, independent of solver code."""
import math
import unittest

from verify_parity import compare, parse_vec, scenarios


class OutputGateTests(unittest.TestCase):
    def test_accepts_four_finite_values_and_fortran_exponent(self):
        self.assertEqual(parse_vec("1D0 2d0 3E0 -4e0\n"), (1.0, 2.0, 3.0, -4.0))

    def test_rejects_empty_truncated_extra_and_diagnostics(self):
        for text in ("", "1 2 3", "1 2 3 4 5", "PASS 1 2 3 4", "1 2 3 nope"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_vec(text)

    def test_rejects_nan_and_infinity(self):
        for token in ("NaN", "inf", "-Infinity", "1e999"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                parse_vec(f"1 2 3 {token}")

    def test_rejects_mismatched_lengths(self):
        for values in ((), (1, 2, 3), (1, 2, 3, 4, 5)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                compare((1, 2, 3, 4), values)

    def test_rejects_nonfinite_comparisons(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                compare((1, 2, 3, 4), (1, 2, 3, value))

    def test_rejects_error_at_strict_threshold(self):
        with self.assertRaises(AssertionError):
            compare((0, 0, 0, 0), (1e-12, 0, 0, 0))

    def test_near_zero_uses_absolute_floor(self):
        self.assertEqual(compare((0, 0, 0, 0), (1e-13, 0, 0, 0)), 1e-13)

    def test_large_components_use_reference_scale(self):
        self.assertLess(compare((1e12, 0, 0, 0), (1e12 + 0.1, 0, 0, 0)), 1e-12)

    def test_detects_wrong_sign_and_wrong_units(self):
        for state in ((-1e6, 1, 1, 1), (1e3, 1, 1, 1)):
            with self.subTest(state=state), self.assertRaises(AssertionError):
                compare((1e6, 1, 1, 1), state)

    def test_scenario_seed_and_target_are_reproducible(self):
        self.assertEqual(scenarios(), scenarios())
        self.assertTrue(any(case.steps == 10000 for case in scenarios()))


if __name__ == "__main__":
    unittest.main()
