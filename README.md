# SEIVE: Parametric Surface Visualizer

Interactive 3D surface explorer built with Dash and Plotly.

## Modes

**Ellipsoid**: parametric ellipsoid scaled by axes a, b, c.

**Spherical Harmonics**: sphere of radius r₀ deformed by a weighted sum of real spherical harmonics: `r(θ,φ) = r₀ + Σ aₗₘ Yₗᵐ(θ,φ)`. Coefficients aₗₘ are set per (l,m) pair up to L_max.

**Orbital**: polar plot of `r(θ,φ) = r₀ + Σ |Yₗᵐ|·Yₗᵐ`, showing the pure angular structure of the harmonics as lobes (analogous to atomic orbitals). An optional semi-transparent SH overlay can be toggled to compare the two representations.

θ and φ domain limits are shared across all modes.

## Run

```bash
pip install dash plotly numpy scipy beartype
python app.py
```

Then open `http://127.0.0.1:8050`.

## Files

| File                          | Purpose                       |
| ----------------------------- | ----------------------------- |
| `app.py`                      | Dash app, layout, callbacks   |
| `ellipticalSurface.py`        | Ellipsoid surface computation |
| `sphericalHarmonicSurface.py` | SH-deformed sphere            |
| `orbitalSurface.py`           | Orbital polar plot            |
| `sphericalHarmonic.py`        | Real spherical harmonic Yₗᵐ   |
| `mesh.py`                     | θ/φ meshgrid utility          |
