"""Example script demonstrating kinetic energy derivation."""

from __future__ import annotations

from sympy import Function, Symbol, diff


def compute_work_energy() -> object:
    t = Symbol("t")
    m = Symbol("m", positive=True)
    v = Function("v")(t)
    F = Symbol("F")
    kinetic = 1 / 2 * m * v ** 2
    power = diff(kinetic, t)
    return power.subs(diff(v, t), F / m)


if __name__ == "__main__":
    print(compute_work_energy())
