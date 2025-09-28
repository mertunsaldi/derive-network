from __future__ import annotations

from derive_network import Canonicalizer


def test_canonicalization_hash_stable() -> None:
    canonicalizer = Canonicalizer()
    result = canonicalizer.canonicalize(latex=r"K = \frac{1}{2} m v^2", sympy_str=None)
    assert result.statement.sympy_srepr.startswith("Add") or result.statement.sympy_srepr.endswith("0")
    repeat = canonicalizer.canonicalize(sympy_str="K - 1/2*m*v**2", latex=None)
    assert result.statement.id == repeat.statement.id


def test_equivalence_numeric_probe() -> None:
    canonicalizer = Canonicalizer()
    lhs = canonicalizer.canonicalize(sympy_str="sin(x) - x", latex=None).statement
    rhs = canonicalizer.canonicalize(sympy_str="x - x", latex=None).statement
    assert not canonicalizer.statements_equivalent(lhs, rhs)

    lhs = canonicalizer.canonicalize(sympy_str="x**2 + 2*x + 1", latex=None).statement
    rhs = canonicalizer.canonicalize(sympy_str="(x+1)**2", latex=None).statement
    assert canonicalizer.statements_equivalent(lhs, rhs)
