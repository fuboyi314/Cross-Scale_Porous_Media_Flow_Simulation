from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PermeabilityInput:
    """Inputs for effective permeability estimation.

    Parameters
    ----------
    average_velocity_lu:
        Domain-averaged pore velocity in lattice units [lu/ts].
    rho_in:
        Inlet density in lattice units.
    rho_out:
        Outlet density in lattice units.
    viscosity_lu:
        Kinematic viscosity in lattice units [lu^2/ts]. For BGK D2Q9: nu=(tau-0.5)/3.
    length_lu:
        Sample length along pressure-gradient direction in lattice units [lu].
    dx_m:
        Optional physical size of one lattice cell [m/lu].

    Notes
    -----
    Lattice pressure for D2Q9 is p = c_s^2 * rho, where c_s^2 = 1/3.
    Therefore dp/dx (lattice units) = (rho_in-rho_out)/(3*length_lu).

    Effective permeability in lattice units from Darcy law is:
        k_lu = nu_lu * u_avg_lu / (dpdx_lu)

    If `dx_m` is provided, physical permeability is mapped as:
        k_m2 = k_lu * dx_m^2
    which assumes similarity between lattice and physical Darcy forms.
    """

    average_velocity_lu: float
    rho_in: float
    rho_out: float
    viscosity_lu: float
    length_lu: float
    dx_m: float | None = None


@dataclass(slots=True)
class PermeabilityResult:
    """Computed permeability outputs."""

    pressure_gradient_lu: float
    permeability_lu: float
    permeability_m2: float | None


def compute_effective_permeability(inp: PermeabilityInput) -> PermeabilityResult:
    """Compute effective permeability from Darcy relation.

    Returns lattice permeability always, and physical m^2 if `dx_m` is provided.
    """

    if inp.length_lu <= 0:
        raise ValueError("length_lu must be > 0")
    if inp.viscosity_lu <= 0:
        raise ValueError("viscosity_lu must be > 0")
    if inp.rho_in <= inp.rho_out:
        raise ValueError("rho_in must be greater than rho_out for positive driving gradient")

    dpdx_lu = (inp.rho_in - inp.rho_out) / (3.0 * inp.length_lu)
    if dpdx_lu <= 0:
        raise ValueError("computed pressure gradient must be > 0")

    k_lu = inp.viscosity_lu * inp.average_velocity_lu / dpdx_lu
    k_m2 = k_lu * (inp.dx_m**2) if inp.dx_m is not None else None

    return PermeabilityResult(
        pressure_gradient_lu=dpdx_lu,
        permeability_lu=k_lu,
        permeability_m2=k_m2,
    )
