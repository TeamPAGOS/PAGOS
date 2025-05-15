"""
Built-in gas exchange models for PAGOS.
"""
from pint import Quantity
from collections.abc import Iterable
from pagos.gas import abn, ice, calc_Ceq, calc_dCeq_dT, calc_Sc
from pagos.water import calc_dens, calc_kinvisc, calc_vappres
import numpy as np

def ua(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, A:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Unfractionated excess air (UA) model, typically for groundwater studies.
    * C = Cₑ(T, S, p) + Aχ
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    :param gas: Gas(es) whose concentration should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature of the water
    :type T: float | Quantity
    :param S: Salinity of the water
    :type S: float | Quantity
    :param p: Pressure over the water
    :type p: float | Quantity
    :param A: Excess air
    :type A: float | Quantity
    :return: Concentration of gas(es) calculated with the model
    :rtype: Quantity | Iterable[Quantity]
    """
    return calc_Ceq(gas, T, S, p) + A * abn(gas)


def pr(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, A:float|Quantity, FPR:float|Quantity, beta:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Partial re-equilibration (PR) model, typically for groundwater studies.
    * C = Cₑ(T, S, p) + Aχ·exp(−Fᴾᴿ·(D/Dᶰᵉ)ᵝ)
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
        * Fᴾᴿ = dimensionless excess air loss parameter
        * D = diffusion coefficient of gas
        * Dᶰᵉ = diffusion coefficient of neon
        * β = exponent in relationship of gas transfer velocity to diffusivity in water
    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    :param gas: Gas(es) whose concentration should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature of the water
    :type T: float | Quantity
    :param S: Salinity of the water
    :type S: float | Quantity
    :param p: Pressure over the water
    :type p: float | Quantity
    :param A: Excess air
    :type A: float | Quantity
    :param FPR: Dimensionless excess air loss parameter
    :type FPR: float | Quantity
    :param beta: Dimenionless exponent in PR model
    :type beta: float | Quantity
    :return: Concentration of gas(es) calculated with the model
    :rtype: Quantity | Iterable[Quantity]
    """
    kinvisc = calc_kinvisc(T, S, magnitude=True)
    schmidt = calc_Sc(gas, T, S, magnitude=True)
    diff = kinvisc/schmidt
    diffNe = kinvisc/calc_Sc('Ne', T, S, magnitude=True)
    return calc_Ceq(gas, T, S, p) + A * abn(gas)  * np.exp(-FPR * (diff/diffNe)**beta)


def pd(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, A:float|Quantity, FPD:float|Quantity, beta:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Partial degassing (PD) model, typically for groundwater studies.
    * C = [Cₑ(T, S, p) + Aχ]·exp(−Fᴾᴰ·(D/Dᶰᵉ)ᵝ)
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
        * Fᴾᴰ = dimensionless diffusive gas loss parameter
        * D = diffusion coefficient of gas
        * Dᶰᵉ = diffusion coefficient of neon
        * β = exponent in relationship of gas transfer velocity to diffusivity in water
    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    :param gas: Gas(es) whose concentration should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature of the water
    :type T: float | Quantity
    :param S: Salinity of the water
    :type S: float | Quantity
    :param p: Pressure over the water
    :type p: float | Quantity
    :param A: Excess air
    :type A: float | Quantity
    :param FPD: Dimensionless diffusive gas loss parameter
    :type FPD: float | Quantity
    :param beta: Dimenionless exponent in PD model
    :type beta: float | Quantity
    :return: Concentration of gas(es) calculated with the model
    :rtype: Quantity | Iterable[Quantity]
    """
    kinvisc = calc_kinvisc(T, S, magnitude=True)
    schmidt = calc_Sc(gas, T, S, magnitude=True)
    diff = kinvisc/schmidt
    diffNe = kinvisc/calc_Sc('Ne', T, S, magnitude=True)
    return (calc_Ceq(gas, T, S, p) + A * abn(gas))  * np.exp(-FPD * (diff/diffNe)**beta)


def od(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, A:float|Quantity, POD:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Oxygen depletion (OD) model, typically for groundwater studies.
    * C = Cₑ(T, S, p)·Pᴼᴰ + Aχ
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * Pᴼᴰ = dimensionless pressure increase factor
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.
    
    :param gas: Gas(es) whose concentration should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature of the water
    :type T: float | Quantity
    :param S: Salinity of the water
    :type S: float | Quantity
    :param p: Pressure over the water
    :type p: float | Quantity
    :param A: Excess air
    :type A: float | Quantity
    :param POD: Pressure increase factor
    :type POD: float | Quantity
    :return: Concentration of gas(es) calculated with the model
    :rtype: Quantity | Iterable[Quantity]
    """
    return calc_Ceq(gas, T, S, p) * POD + A * abn(gas)


def ce(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, A:float|Quantity, F:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Closed-system equilibration (CE) model, typically for groundwater studies.
    * C = Cₑ(T, S, p) + (1 − F)·Aχ / (1 + FAχ / Cₑ(T, S, p))
        * Cₑ(T, S, p) = equilibrium concentration at water recharge temperature T, salinity S and air pressure p
        * F = dimensionless fractionation factor by whichthe size of the gas phase has changed during re-equilibration
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
    See Jung and Aeschbach 2018 (https://doi.org/10.1016/j.envsoft.2018.02.004) for more details.

    :param gas: Gas(es) whose concentration should be calculated
    :type gas: str | Iterable[str]
    :param T: Temperature of the water
    :type T: float | Quantity
    :param S: Salinity of the water
    :type S: float | Quantity
    :param p: Pressure over the water
    :type p: float | Quantity
    :param A: Excess air
    :type A: float | Quantity
    :param F: Dimensionless fractionation factor
    :type F: float | Quantity
    :return: Concentration of gas(es) calculated with the model
    :rtype: Quantity | Iterable[Quantity]
    """
    ceq = calc_Ceq(gas, T, S, p)
    z = abn(gas)
    return ceq + (1 - F) * A * z / (1 + F * A * z / ceq)


def taylor_swif(gas:str|Iterable[str], T_r:float|Quantity, S:float|Quantity, p:float|Quantity, R:float|Quantity, A:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Unfractionated excess air injection before freezing, then fractionation of gases upon freezing. Taylor
    expansion of concentration equation with fractionation during freezing yields:
    * C = [1 - R·(κ-1)] · [Cₑ(T_r, S, p) + Aχ].
        * R = small remaining ice fraction after melting
        * κ = ice fractionation coefficient of the given gas
        * Cₑ(T_r, S, p) = equilibrium concentration at water recharge temperature T_r, salinity S and air pressure p
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
    See Chiara Hubner's Master Thesis (2024) for more info.

    :param gas: Gas(es) whose concentration should be calculated
    :type gas: str | Iterable[str]
    :param T_r: Recharge temperature of the water
    :type T_r: float | Quantity
    :param S: In-situ salinity of the water
    :type S: float | Quantity
    :param p: Air pressure over the water during recharge
    :type p: float | Quantity
    :param R: Remaining ice fraction after melting
    :type R: float | Quantity
    :param A: Excess air
    :type A: float | Quantity
    :return: Concentration of gas(es) calculated with the model
    :rtype: Quantity | Iterable[Quantity]
    """
    chi = abn(gas)
    kappa = ice(gas)
    Ceq = calc_Ceq(gas, T_r, S, p, 'cc/g')
    # C calculations
    C = (1 - R * (kappa - 1)) * (Ceq + A*chi)
    return C


def taylor_swift(gas:str|Iterable[str], T_r:float|Quantity, S:float|Quantity, p:float|Quantity, R:float|Quantity, A:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Unfractionated excess air injection before freezing, then fractionation of gases upon freezing. Taylor
    expansion of concentration equation with fractionation during freezing AND melting yields:
    * C = [1 - R·(κ²-1)] · [Cₑ(T_r, S, p) + Aχ].
        * R = small remaining ice fraction after melting
        * κ = ice fractionation coefficient of the given gas
        * Cₑ(T_r, S, p) = equilibrium concentration at water recharge temperature T_r, salinity S and air pressure p.
        * A = excess air in same units as Cₑ
        * χ = atmospheric abundance of given gas
    See Chiara Hubner's Master Thesis (2024) for more info.

    :param gas: Gas(es) whose concentration should be calculated.
    :type gas: str | Iterable[str]
    :param T_r: Recharge temperature of the water.
    :type T_r: float | Quantity
    :param S: In-situ salinity of the water.
    :type S: float | Quantity
    :param p: Air pressure over the water during recharge.
    :type p: float | Quantity
    :param R: Remaining ice fraction after melting.
    :type R: float | Quantity
    :param A: Excess air.
    :type A: float | Quantity
    :return: Concentration of gas(es) calculated with the model.
    :rtype: Quantity | Iterable[Quantity]
    """
    chi = abn(gas)
    kappa = ice(gas)
    Ceq = calc_Ceq(gas, T_r, S, p, 'cc/g')
    # C calculations
    C = (1 - R * (kappa**2 - 1)) * (Ceq + A*chi)
    return C


def dwarf(gas:str|Iterable[str], T_r:float|Quantity, S:float|Quantity, p:float|Quantity, omega:float|Quantity, zeta:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Steady-state mixed reactor including a full mass balance and no diffusion. Equation reads:
    * C = 1/[1 + ω·(κ-1)] · [Cₑ(T_r, S, p) + ζχ]
        * ω = net freeze-to-flush rates ratio
        * κ = ice fractionation coefficient of the given gas
        * Cₑ(T_r, S, p) = equilibrium concentration at water recharge temperature T_r, salinity S and air pressure p.
        * ζ = net diffusion + excess air parameter
        * χ = atmospheric abundance of given gas
    See Chiara Hubner's Master Thesis (2024) for more info

    :param gas: Gas(es) whose concentration should be calculated.
    :type gas: str | Iterable[str]
    :param T_r: Recharge temperature of the water.
    :type T_r: float | Quantity
    :param S: In-situ salinity of the water.
    :type S: float | Quantity
    :param p: Air pressure over the water during recharge.
    :type p: float | Quantity
    :param omega: Net freeze-to-flush rates ratio.
    :type omega: float | Quantity
    :param zeta: Net diffusion + excess air parameter.
    :type zeta: float | Quantity
    :return: Concentration of gas(es) calculated with the model.
    :rtype: Quantity | Iterable[Quantity]
    """
    chi = abn(gas)
    kappa = ice(gas)
    Ceq = calc_Ceq(gas, T_r, S, p, 'cc/g')
    # C calculation
    C = 1 / (1 + omega*(kappa - 1)) * (Ceq + zeta * chi)
    return C


def qs_dwarf(gas:str|Iterable[str], T:float|Quantity, S:float|Quantity, p:float|Quantity, omega:float|Quantity, zeta:float|Quantity, T_r:float|Quantity) -> Quantity|Iterable[Quantity]:
    """Quasi-steady-state mixed reactor including a full mass balance and no diffusion, and a temperature
    differential simplification. Equation reads:
    * C = 1/[1 + ω·(κ-1) + q·Cₑ'(T, S, p)/Cₑ(T, S, p)] · [Cₑ(T_r, S, p) + ζχ]
        * ω = net freeze-to-flush rates ratio
        * κ = ice fractionation coefficient of the given gas
        * Cₑ(T, S, p) = equilibrium concentration at in-situ temperature T, salinity S and air pressure p
        * Cₑ' = dCₑ/dT
        * Cₑ(T_r, S, p) = equilibrium concentration at water recharge temperature T_r, salinity S and air pressure p
        * q = T - T_r
        * ζ = net diffusion + excess air parameter
        * χ = atmospheric abundance of given gas
    See Chiara Hubner's Master Thesis (2024) for more info

    :param gas: Gas(es) whose concentration should be calculated.
    :type gas: str | Iterable[str]
    :param T: In-situ temperature of the water.
    :type T: float | Quantity
    :param S: In-situ salinity of the water.
    :type S: float | Quantity
    :param p: Air pressure over the water during recharge.
    :type p: float | Quantity
    :param omega: Net freeze-to-flush rates ratio.
    :type omega: float | Quantity
    :param zeta: Net diffusion + excess air parameter.
    :type zeta: float | Quantity
    :param T_r: Recharge temperature of the water.
    :type T_r: float | Quantity
    :return: Concentration of gas(es) calculated with the model.
    :rtype: Quantity | Iterable[Quantity]
    """
    chi = abn(gas)
    kappa = ice(gas)
    q = T-T_r
    Ceq_T = calc_Ceq(gas, T, S, p, 'cc/g')
    dCeq_T_dT = calc_dCeq_dT(gas, T, S, p, 'cc/g/K')
    invpref = 1 + (kappa-1)*omega + q*dCeq_T_dT/Ceq_T
    Ceq_T_r = calc_Ceq(gas, T_r, S, p, 'cc/g')
    # C calculation
    C = 1/invpref * (Ceq_T_r + zeta*chi)
    return C