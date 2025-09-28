from __future__ import annotations

import pytest
import sympy as sp

from services.canonicalizer.canon import (
    assess_equivalence,
    canonicalize,
    units_transform,
)


def test_vector_operator_normalization() -> None:
    stmt = canonicalize("div(E)", fmt="sympy")
    assert "Function('Div')" in stmt.sympy_srepr


def test_derivative_alpha_renaming() -> None:
    stmt = canonicalize("Eq(Derivative(f(x), x), k)", fmt="sympy")
    assert stmt.roles.independent == ("x1",)
    assert stmt.roles.parameters == ("p1",)
    assert "Derivative" in stmt.sympy_srepr
    assert "p1" in stmt.sympy_srepr


def test_limit_normalization() -> None:
    stmt = canonicalize("Limit((1 + 1/n)**n, n, oo)", fmt="sympy")
    assert stmt.expression == sp.E
    assert stmt.sympy_srepr == sp.srepr(sp.E)


def test_small_angle_assumptions_and_approximation() -> None:
    lhs = canonicalize("sin(theta)", fmt="sympy", meta_text="for small θ in vacuum")
    rhs = canonicalize("theta", fmt="sympy")
    assert lhs.assumptions == ("small-angle", "vacuum")
    assert lhs.roles.independent == ("x1",)
    assert rhs.roles.independent == ("x1",)
    report = assess_equivalence(
        lhs.expression,
        rhs.expression,
        assumptions=lhs.assumptions,
        tolerance=1e-6,
    )
    assert report.relation == "APPROX_OF"
    assert report.max_delta is not None
    assert report.max_delta < 1e-6


def test_units_and_gaussian_placeholder() -> None:
    stmt = canonicalize("epsilon_0 * E", fmt="sympy")
    units = dict(stmt.units)
    assert pytest.approx(-1.0) == units["M"]
    assert pytest.approx(-3.0) == units["L"]
    assert pytest.approx(4.0) == units["T"]
    assert pytest.approx(2.0) == units["I"]
    assert stmt.roles.constants == ("c1",)
    assert ("epsilon_0", "c1") in stmt.roles.mapping
    assert units_transform(stmt.expression, source="gaussian", target="si") is None
    assert units_transform(stmt.expression, source="si", target="si") == stmt.expression
