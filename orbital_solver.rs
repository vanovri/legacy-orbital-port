#![forbid(unsafe_code)]

use std::io::{self, Read};

#[derive(Clone, Copy, Debug)]
pub struct SimConfig {
    pub gm: f64,
    pub dt: f64,
    pub nsteps: usize,
}

#[derive(Clone, Copy, Debug)]
pub struct OrbitalState {
    pub x: f64,
    pub y: f64,
    pub vx: f64,
    pub vy: f64,
}

impl OrbitalState {
    fn accel(px: f64, py: f64, gm: f64) -> Result<(f64, f64), &'static str> {
        let r2 = px * px + py * py;
        let r3 = r2 * r2.sqrt();
        if !r3.is_finite() || r3 <= 0.0 {
            return Err("singular or unrepresentable radius");
        }
        Ok((-gm * px / r3, -gm * py / r3))
    }

    pub fn rk4_step(&mut self, cfg: &SimConfig) -> Result<(), &'static str> {
        let dt = cfg.dt;
        let (k1vx, k1vy) = Self::accel(self.x, self.y, cfg.gm)?;
        let (k1x, k1y) = (self.vx, self.vy);
        let (k2vx, k2vy) = Self::accel(
            self.x + 0.5 * dt * k1x, self.y + 0.5 * dt * k1y, cfg.gm,
        )?;
        let (k2x, k2y) = (self.vx + 0.5 * dt * k1vx, self.vy + 0.5 * dt * k1vy);
        let (k3vx, k3vy) = Self::accel(
            self.x + 0.5 * dt * k2x, self.y + 0.5 * dt * k2y, cfg.gm,
        )?;
        let (k3x, k3y) = (self.vx + 0.5 * dt * k2vx, self.vy + 0.5 * dt * k2vy);
        let (k4vx, k4vy) = Self::accel(self.x + dt * k3x, self.y + dt * k3y, cfg.gm)?;
        let (k4x, k4y) = (self.vx + dt * k3vx, self.vy + dt * k3vy);
        let scale = dt / 6.0;
        self.x += scale * (k1x + 2.0 * k2x + 2.0 * k3x + k4x);
        self.y += scale * (k1y + 2.0 * k2y + 2.0 * k3y + k4y);
        self.vx += scale * (k1vx + 2.0 * k2vx + 2.0 * k3vx + k4vx);
        self.vy += scale * (k1vy + 2.0 * k2vy + 2.0 * k3vy + k4vy);
        Ok(())
    }
}

fn run() -> Result<(), String> {
    let mut cfg = SimConfig { gm: 3.986004418e14, dt: 1.0, nsteps: 10000 };
    let mut state = OrbitalState { x: 6.778137e6, y: 0.0, vx: 0.0, vy: 7.6686e3 };
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).map_err(|e| e.to_string())?;
    if input.lines().skip(1).any(|line| !line.trim().is_empty()) {
        return Err("expected one input line".into());
    }
    if !input.trim().is_empty() {
        let fields: Vec<&str> = input.split_whitespace().collect();
        if fields.len() != 7 { return Err("expected: steps dt gm x y vx vy".into()); }
        cfg.nsteps = fields[0].parse().map_err(|_| "invalid steps")?;
        let values: Vec<f64> = fields[1..].iter()
            .map(|s| s.replace(['D', 'd'], "E").parse::<f64>().map_err(|_| "invalid number"))
            .collect::<Result<_, _>>()?;
        cfg.dt = values[0]; cfg.gm = values[1];
        state = OrbitalState { x: values[2], y: values[3], vx: values[4], vy: values[5] };
    }
    if ![cfg.dt, cfg.gm, state.x, state.y, state.vx, state.vy].iter().all(|v| v.is_finite())
        || cfg.gm < 0.0 || cfg.gm > 1e20 || cfg.dt <= 0.0 || cfg.dt > 60.0
        || cfg.nsteps > 1_000_000 || state.x * state.x + state.y * state.y <= 0.0 {
        return Err("invalid simulation parameters".into());
    }
    for _ in 0..cfg.nsteps { state.rk4_step(&cfg)?; }
    if ![state.x, state.y, state.vx, state.vy].iter().all(|v| v.is_finite()) {
        return Err("non-finite result".into());
    }
    println!("{:.17E} {:.17E} {:.17E} {:.17E}", state.x, state.y, state.vx, state.vy);
    Ok(())
}

fn main() {
    if let Err(error) = run() { eprintln!("{error}"); std::process::exit(2); }
}
