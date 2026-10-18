"""Optional publication figure. Requires Matplotlib; never invents measurements."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.ticker import NullFormatter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/verification.png"))
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("status") != "pass":
        raise ValueError("A successful measured verification report is required")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none"})
    fig = plt.figure(figsize=(13.5, 7), facecolor="#f5f5f2", layout="constrained")
    grid = fig.add_gridspec(2, 2, width_ratios=(1.15, 1))
    orbit = fig.add_subplot(grid[:, 0], facecolor="#f5f5f2")
    for language, color, style in (("fortran", "#253d58", "-"), ("rust", "#ca713b", "--"),
                                    ("cpp", "#287d67", ":")):
        xy = [row["states"][language][:2] for row in report["trajectory"]]
        orbit.plot([p[0] / 1e6 for p in xy], [p[1] / 1e6 for p in xy], style,
                   color=color, linewidth=2, label=language.title() if language != "cpp" else "C++20")
    orbit.add_patch(Circle((0, 0), 6.371, facecolor="#dde5e9", edgecolor="#b0bfc7"))
    orbit.text(0, 0, "Earth radius\nfor scale only", ha="center", va="center", color="#516171")
    orbit.scatter([6.778137], [0], s=25, color="#1d2228", zorder=5)
    orbit.set(aspect="equal", xlabel="x (1,000 km)", ylabel="y (1,000 km)",
              title="10,000 steps, three measured trajectories")
    orbit.legend(loc="lower left", frameon=False)
    orbit.grid(alpha=0.12)

    convergence = fig.add_subplot(grid[0, 1], facecolor="#f5f5f2")
    physical = report["physics"]["fortran"]
    convergence.loglog([40, 20, 10], physical["convergence_errors_dt_40_20_10"],
                      "o-", color="#253d58", linewidth=2)
    convergence.set(xlabel="Timestep (seconds)", ylabel="Scaled error vs analytic orbit",
                    title="Independent circular-orbit check")
    convergence.set_xticks([10, 20, 40], labels=["10", "20", "40"])
    convergence.xaxis.set_minor_formatter(NullFormatter())
    convergence.grid(alpha=0.15)

    notes = fig.add_subplot(grid[1, 1], facecolor="#f5f5f2")
    notes.axis("off")
    max_error = max(max(row["scaled_error"].values()) for row in report["scenarios"])
    bug = report["supplied_bug"]
    position_error = sum((a - b) ** 2 for a, b in zip(bug["buggy_1000_steps"][:2],
                                                      bug["corrected_1000_steps"][:2])) ** 0.5 / 1000
    lines = [f"{report['scenario_count']} scenarios + {len(report['trajectory'])} trajectory checkpoints",
             f"Measured port discrepancy: {max_error:.2e} (gate: < 1e-12)",
             "Threshold uses max(1, abs(reference)) scaling.",
             f"Circular-orbit error at dt=1 s: {physical['circular_scaled_error']:.2e}",
             f"Convergence ratios: {physical['convergence_ratios'][0]:.2f}, {physical['convergence_ratios'][1]:.2f}",
             f"Supplied integer-stage bug: {position_error:.1f} km discrepancy at 1,000 s",
             "Original faulty result rejected by the referee.",
             "Synthetic educational model. No flight validation."]
    notes.text(0.0, 0.98, "\n\n".join(lines), va="top", fontsize=10, color="#25313e")
    fig.suptitle("LEGACY ORBITAL PORT  /  FORTRAN · RUST · C++20", fontsize=18,
                 fontweight="bold", color="#25313e")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=160, facecolor=fig.get_facecolor())
    svg = args.output.with_suffix(".svg")
    fig.savefig(svg, facecolor=fig.get_facecolor(), metadata={"Date": None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
