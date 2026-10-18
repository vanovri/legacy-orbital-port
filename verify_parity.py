"""Compile real solvers and check differential, analytic, and rejection gates.

Python 3.10+, standard library only. No network access or mocked executables.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TOLERANCE = 1e-12
GM = 3.986004418e14
RADIUS = 6.778137e6
LANGUAGES = ("fortran", "rust", "cpp")


@dataclass(frozen=True)
class Scenario:
    name: str
    steps: int = 10000
    dt: float = 1.0
    gm: float = GM
    state: tuple[float, float, float, float] = (RADIUS, 0.0, 0.0, 7668.6)

    def stdin(self) -> str:
        return f"{self.steps} " + " ".join(f"{v:.17e}" for v in (self.dt, self.gm, *self.state)) + "\n"


def run(command: list[str], *, stdin: str = "", timeout: int = 60) -> subprocess.CompletedProcess:
    result = subprocess.run(command, input=stdin, text=True, capture_output=True,
                            cwd=ROOT, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr}\n{result.stdout}")
    return result


def parse_vec(output: str) -> tuple[float, ...]:
    tokens = output.split()
    if len(tokens) != 4:
        raise ValueError(f"Expected exactly 4 result fields, received {len(tokens)}")
    values = tuple(float(token.replace("D", "E").replace("d", "e")) for token in tokens)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Non-finite solver output")
    return values


def compare(reference: tuple[float, ...], candidate: tuple[float, ...]) -> float:
    if len(reference) != 4 or len(candidate) != 4:
        raise ValueError("Both states must contain exactly 4 components")
    if not all(math.isfinite(v) for v in (*reference, *candidate)):
        raise ValueError("Cannot compare non-finite states")
    error = max(abs(a - b) / max(1.0, abs(a)) for a, b in zip(reference, candidate))
    if error >= TOLERANCE:
        raise AssertionError(f"Scaled component error {error:.6e} >= {TOLERANCE:.1e}")
    return error


def compile_solvers(build_dir: Path, profile: str) -> tuple[dict[str, Path], dict]:
    settings = {
        "fortran": ("FC", "gfortran", "legacy_orbital.f"),
        "rust": ("RUSTC", "rustc", "orbital_solver.rs"),
        "cpp": ("CXX", "g++", "orbital_solver.cpp"),
    }
    build_dir.mkdir(parents=True, exist_ok=True)
    binaries, metadata = {}, {}
    for language, (variable, default, source) in settings.items():
        compiler = shutil.which(os.environ.get(variable, default))
        if compiler is None:
            raise RuntimeError(f"Missing {default}. Install it or set {variable} to its executable path.")
        binary = (build_dir / f"orbital_{language}{'.exe' if os.name == 'nt' else ''}").resolve()
        optimized = profile == "optimized"
        if language == "fortran":
            flags = ["-std=legacy", "-ffp-contract=off", "-fno-fast-math", "-fno-align-commons",
                     "-Wall", "-Wextra", "-Werror=conversion", "-Werror=line-truncation"]
            flags += ["-O2"] if optimized else ["-O0", "-g", "-fcheck=all", "-ffpe-trap=invalid,zero,overflow"]
        elif language == "cpp":
            flags = ["-std=c++20", "-ffp-contract=off", "-fno-fast-math", "-Wall", "-Wextra", "-Werror"]
            flags += ["-O2"] if optimized else ["-O0", "-g", "-fsanitize=undefined,bounds", "-fno-sanitize-recover=all"]
        else:
            flags = ["--edition=2021", "-D", "warnings", "-C", f"opt-level={2 if optimized else 0}"]
            if not optimized:
                flags += ["-C", "debug-assertions=yes", "-C", "overflow-checks=yes"]
        command = [compiler, *flags, str(ROOT / source), "-o", str(binary)]
        result = run(command)
        binaries[language] = binary
        metadata[language] = {
            "version": run([compiler, "--version"]).stdout.splitlines()[0],
            "flags": flags,
            "source_sha256": hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
            "diagnostics": result.stderr.strip().replace(str(ROOT) + os.sep, ""),
        }
    return binaries, metadata


def execute(binary: Path, scenario: Scenario) -> tuple[float, ...]:
    return parse_vec(run([str(binary)], stdin=scenario.stdin(), timeout=15).stdout)


def scenarios() -> list[Scenario]:
    cases = [Scenario(f"checkpoint_{n}", steps=n) for n in (0, 1, 10, 100, 1000, 10000)]
    speed = math.sqrt(GM / RADIUS)
    cases += [Scenario("circular", state=(RADIUS, 0.0, 0.0, speed)),
              Scenario("retrograde", state=(RADIUS, 0.0, 0.0, -speed)),
              Scenario("eccentric", state=(RADIUS, 0.0, 0.0, 0.85 * speed)),
              Scenario("free_drift", steps=500, gm=0.0, state=(RADIUS, 1000.0, 50.0, -20.0)),
              Scenario("dimensionless", gm=1.0, dt=0.001, state=(1.0, 0.0, 0.0, 1.0))]
    generator = random.Random(20261019)
    for index in range(16):
        radius = generator.uniform(6.8e6, 4.2e7)
        angle = generator.uniform(-math.pi, math.pi)
        speed = math.sqrt(GM / radius) * generator.uniform(0.85, 1.1)
        cases.append(Scenario(f"seeded_{index:02}", steps=generator.choice((100, 1000, 10000)),
                              dt=generator.choice((0.25, 0.5, 1.0, 2.0)),
                              state=(radius * math.cos(angle), radius * math.sin(angle),
                                     -speed * math.sin(angle), speed * math.cos(angle))))
    return cases


def invariants(state: tuple[float, ...], gm: float) -> tuple[float, float]:
    x, y, vx, vy = state
    return ((vx * vx + vy * vy) / 2.0 - gm / math.hypot(x, y), x * vy - y * vx)


def circular_error(state: tuple[float, ...], scenario: Scenario) -> float:
    radius = scenario.state[0]
    speed = math.sqrt(scenario.gm / radius)
    theta = speed / radius * scenario.steps * scenario.dt
    exact = (radius * math.cos(theta), radius * math.sin(theta),
             -speed * math.sin(theta), speed * math.cos(theta))
    return max(abs(a - b) / scale for a, b, scale in zip(state, exact, (radius, radius, speed, speed)))


def verify(binaries: dict[str, Path], metadata: dict, profile: str) -> dict:
    rows = []
    for scenario in scenarios():
        states = {lang: execute(binary, scenario) for lang, binary in binaries.items()}
        errors = {lang: compare(states["fortran"], states[lang]) for lang in ("rust", "cpp")}
        rows.append({"scenario": asdict(scenario), "states": states, "scaled_error": errors})
    baseline = rows[5]["states"]
    for lang, binary in binaries.items():
        compare(baseline[lang], parse_vec(run([str(binary)]).stdout))
        if execute(binary, Scenario("repeat")) != baseline[lang]:
            raise AssertionError(f"Non-deterministic baseline: {lang}")

    physical = {}
    for lang, binary in binaries.items():
        energy0, momentum0 = invariants(Scenario("baseline").state, GM)
        energy1, momentum1 = invariants(baseline[lang], GM)
        drifts = {"energy_relative_drift": abs((energy1 - energy0) / energy0),
                  "angular_momentum_relative_drift": abs((momentum1 - momentum0) / momentum0)}
        if max(drifts.values()) >= 1e-8:
            raise AssertionError(f"Invariant drift: {lang}: {drifts}")
        circular = scenarios()[6]
        exact_error = circular_error(execute(binary, circular), circular)
        if exact_error >= 1e-8:
            raise AssertionError(f"Circular analytic oracle failed: {lang}: {exact_error}")
        errors = []
        for dt in (40.0, 20.0, 10.0):
            case = replace(circular, steps=int(4000 / dt), dt=dt)
            errors.append(circular_error(execute(binary, case), case))
        ratios = [errors[0] / errors[1], errors[1] / errors[2]]
        if not all(8 < ratio < 32 for ratio in ratios):
            raise AssertionError(f"RK4 convergence failed: {lang}: {ratios}")
        free = scenarios()[9]
        expected = (free.state[0] + free.steps * free.dt * free.state[2],
                    free.state[1] + free.steps * free.dt * free.state[3], *free.state[2:])
        compare(expected, execute(binary, free))
        physical[lang] = {**drifts, "circular_scaled_error": exact_error,
                          "convergence_errors_dt_40_20_10": errors, "convergence_ratios": ratios,
                          "analytic_free_drift": "pass"}

    # Deliberately malformed inputs must never emit an accepted state.
    rejected = []
    invalid = ["-1 1 1 1 0 0 1", "1000001 1 1 1 0 0 1", "1 0 1 1 0 0 1",
               "1 61 1 1 0 0 1", "1 1 -1 1 0 0 1", "1 1 1 0 0 0 1",
               "1 1 NaN 1 0 0 1", "1 1 1 Infinity 0 0 1", "1 1 1", "garbage",
               "1 1 1 1 0 0 1 extra", "1 1 1 1e300 1e300 0 0",
               "1 1 1 1 0 0 1\n1 1 1 1 0 0 1", "1 1 0 0.5 0 -1 0"]
    for lang, binary in binaries.items():
        for payload in invalid:
            result = subprocess.run([str(binary)], input=payload + "\n", text=True,
                                    capture_output=True, timeout=15)
            if result.returncode == 0:
                raise AssertionError(f"Accepted invalid input: {lang}: {payload}")
        rejected.append({"language": lang, "rejected_cases": len(invalid)})

    # Preserve the supplied bug as an executable regression, not a hidden correction.
    source = ROOT / "tests" / "fixtures" / "supplied_implicit_integer.f"
    binary = next(iter(binaries.values())).parent / f"supplied_bug{'.exe' if os.name == 'nt' else ''}"
    compiler = shutil.which(os.environ.get("FC", "gfortran"))
    result = run([compiler, "-std=legacy", "-O2", "-fno-align-commons", "-Wconversion", str(source), "-o", str(binary)])
    buggy = parse_vec(run([str(binary)]).stdout)
    corrected = execute(binaries["fortran"], Scenario("bug_reproduction", steps=1000))
    try:
        compare(corrected, buggy)
    except AssertionError:
        bug_rejected = True
    else:
        raise AssertionError("Supplied integer-stage defect escaped the parity gate")

    # Samples are independently re-run to produce a real, portable plot dataset.
    trajectory = []
    for step in range(0, 10001, 100):
        case = Scenario("trajectory", steps=step)
        states = {lang: execute(binary, case) for lang, binary in binaries.items()}
        for lang in ("rust", "cpp"):
            compare(states["fortran"], states[lang])
        trajectory.append({"step": step, "time_s": step * case.dt, "states": states})
    return {"schema_version": 1, "status": "pass", "profile": profile,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(), "python": platform.python_version(),
            "referee_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "fixture_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "tolerance": {"threshold": TOLERANCE, "comparison": "strictly less than",
                          "metric": "max_i(abs(reference_i-candidate_i)/max(1,abs(reference_i)))"},
            "compilers": metadata, "scenario_count": len(rows), "scenarios": rows,
            "physics": physical, "invalid_inputs": rejected,
            "supplied_bug": {"rejected": bug_rejected, "buggy_1000_steps": buggy,
                             "corrected_1000_steps": corrected,
                             "diagnostics": result.stderr.strip().replace(str(ROOT) + os.sep, "")},
            "trajectory": trajectory}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("optimized", "checked"), default="optimized")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "local-verification.json")
    args = parser.parse_args()
    # Replace previous success before starting, so a failed run cannot leave a stale PASS.
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"status": "running", "profile": args.profile}) + "\n", encoding="utf-8")
    try:
        binaries, metadata = compile_solvers(ROOT / "build" / args.profile, args.profile)
        report = verify(binaries, metadata, args.profile)
    except (AssertionError, ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        args.report.write_text(json.dumps({"status": "failed", "error": str(error)}, indent=2) + "\n", encoding="utf-8")
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    maximum = max(max(row["scaled_error"].values()) for row in report["scenarios"])
    print(f"PASS [{args.profile}]: {report['scenario_count']} scenarios + 101 trajectory checkpoints; max error {maximum:.3e} < {TOLERANCE:.1e}")
    print("Analytic circular/free-drift oracles, RK4 convergence, invariants, invalid-input and supplied-bug gates passed.")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
