#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string>

struct SimConfig {
    double gm{3.986004418e14};
    double dt{1.0};
    int nsteps{10000};
};

struct OrbitalState {
    double x{6.778137e6}, y{0.0}, vx{0.0}, vy{7.6686e3};

    static std::array<double, 2> accel(double px, double py, double gm) {
        const double r2 = px * px + py * py;
        const double r3 = r2 * std::sqrt(r2);
        if (!std::isfinite(r3) || r3 <= 0.0) {
            throw std::runtime_error("singular or unrepresentable radius");
        }
        return {-gm * px / r3, -gm * py / r3};
    }

    void rk4_step(const SimConfig& cfg) {
        const double dt = cfg.dt;
        const auto [k1vx, k1vy] = accel(x, y, cfg.gm);
        const double k1x = vx, k1y = vy;
        const auto [k2vx, k2vy] = accel(x + 0.5 * dt * k1x, y + 0.5 * dt * k1y, cfg.gm);
        const double k2x = vx + 0.5 * dt * k1vx, k2y = vy + 0.5 * dt * k1vy;
        const auto [k3vx, k3vy] = accel(x + 0.5 * dt * k2x, y + 0.5 * dt * k2y, cfg.gm);
        const double k3x = vx + 0.5 * dt * k2vx, k3y = vy + 0.5 * dt * k2vy;
        const auto [k4vx, k4vy] = accel(x + dt * k3x, y + dt * k3y, cfg.gm);
        const double k4x = vx + dt * k3vx, k4y = vy + dt * k3vy;
        const double scale = dt / 6.0;
        x += scale * (k1x + 2.0 * k2x + 2.0 * k3x + k4x);
        y += scale * (k1y + 2.0 * k2y + 2.0 * k3y + k4y);
        vx += scale * (k1vx + 2.0 * k2vx + 2.0 * k3vx + k4vx);
        vy += scale * (k1vy + 2.0 * k2vy + 2.0 * k3vy + k4vy);
    }
};

int main() {
    try {
        constexpr SimConfig defaults{};
        SimConfig cfg = defaults;
        OrbitalState state{};
        std::string input{std::istreambuf_iterator<char>{std::cin}, {}};
        const auto newline = input.find('\n');
        if (newline != std::string::npos && input.find_first_not_of(" \t\r\n", newline) != std::string::npos) {
            throw std::runtime_error("expected one input line");
        }
        if (input.find_first_not_of(" \t\r\n") != std::string::npos) {
            std::replace(input.begin(), input.end(), 'D', 'E');
            std::replace(input.begin(), input.end(), 'd', 'e');
            std::istringstream fields{input};
            std::string extra;
            if (!(fields >> cfg.nsteps >> cfg.dt >> cfg.gm >> state.x >> state.y >> state.vx >> state.vy)
                || (fields >> extra)) { throw std::runtime_error("expected: steps dt gm x y vx vy"); }
        }
        const std::array values{cfg.dt, cfg.gm, state.x, state.y, state.vx, state.vy};
        if (!std::all_of(values.begin(), values.end(), [](double v) { return std::isfinite(v); })
            || cfg.gm < 0.0 || cfg.gm > 1e20 || cfg.dt <= 0.0 || cfg.dt > 60.0
            || cfg.nsteps < 0 || cfg.nsteps > 1000000 || state.x * state.x + state.y * state.y <= 0.0) {
            throw std::runtime_error("invalid simulation parameters");
        }
        for (int i = 0; i < cfg.nsteps; ++i) { state.rk4_step(cfg); }
        const std::array result{state.x, state.y, state.vx, state.vy};
        if (!std::all_of(result.begin(), result.end(), [](double v) { return std::isfinite(v); })) {
            throw std::runtime_error("non-finite result");
        }
        std::cout << std::scientific << std::uppercase << std::setprecision(17)
                  << state.x << ' ' << state.y << ' ' << state.vx << ' ' << state.vy << '\n';
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 2;
    }
}
