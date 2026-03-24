from __future__ import annotations

from cspmfs.upscaling.permeability import PermeabilityInput, compute_effective_permeability


def test_permeability_lattice_value_known_case() -> None:
    inp = PermeabilityInput(
        average_velocity_lu=0.01,
        rho_in=1.01,
        rho_out=1.0,
        viscosity_lu=0.1,
        length_lu=100.0,
        dx_m=None,
    )
    out = compute_effective_permeability(inp)
    # dpdx = (0.01)/(3*100)=3.333...e-5 ; k = 0.1*0.01 / dpdx = 30
    assert abs(out.pressure_gradient_lu - (0.01 / 300.0)) < 1e-12
    assert abs(out.permeability_lu - 30.0) < 1e-10
    assert out.permeability_m2 is None


def test_permeability_physical_conversion() -> None:
    inp = PermeabilityInput(
        average_velocity_lu=0.02,
        rho_in=1.02,
        rho_out=1.0,
        viscosity_lu=0.2,
        length_lu=200.0,
        dx_m=1e-5,
    )
    out = compute_effective_permeability(inp)
    assert out.permeability_lu > 0
    assert out.permeability_m2 is not None
    assert out.permeability_m2 > 0
