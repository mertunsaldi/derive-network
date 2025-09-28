from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from itertools import product
from typing import Iterable, List, Optional, Sequence, Tuple

import sympy as sp
from sympy import Eq
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_application,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from .models import ConfidenceLevel, Statement

SI_BASE_UNITS = ("m", "kg", "s", "A", "K", "mol", "cd")


@dataclass(frozen=True)
class CanonicalizationResult:
    expression: sp.Expr
    sympy_srepr: str
    assumptions: Tuple[str, ...]
    units: Tuple[Tuple[str, float], ...]
    statement: Statement


class Canonicalizer:
    def __init__(self) -> None:
        self._transformations = standard_transformations + (
            convert_xor,
            implicit_application,
            implicit_multiplication_application,
        )

    def _parse(self, *, latex: Optional[str], sympy_str: Optional[str]) -> sp.Expr:
        if latex:
            try:
                return parse_latex(latex)
            except Exception as exc:  # pragma: no cover - protective guard
                raise ValueError(f"Failed to parse LaTeX: {exc}") from exc
        if sympy_str:
            return parse_expr(sympy_str, transformations=self._transformations)
        raise ValueError("Either latex or sympy string must be provided")

    def _move_all_to_lhs(self, expr: sp.Expr) -> sp.Expr:
        if isinstance(expr, Eq):
            return sp.simplify(expr.lhs - expr.rhs)
        if expr.has(Eq):
            # Flatten nested equations by subtracting
            return sp.simplify(sp.Add.fromiter([term.lhs - term.rhs for term in expr.atoms(Eq)]))
        return expr

    def _alpha_rename(self, expr: sp.Expr) -> Tuple[sp.Expr, List[sp.Symbol]]:
        symbols = sorted(expr.free_symbols, key=lambda s: s.name)
        replacements = {
            sym: sp.Symbol(f"x_{index + 1}")
            for index, sym in enumerate(symbols)
        }
        if not replacements:
            return expr, []
        renamed = expr.xreplace(replacements)
        return renamed, list(replacements.values())

    def _normalize_commutative(self, expr: sp.Expr) -> sp.Expr:
        expanded = sp.expand(expr, power_exp=True)
        simplified = sp.simplify(expanded)
        return sp.factor(simplified)

    def _standardize_gradient(self, expr: sp.Expr) -> sp.Expr:
        # SymPy already uses Derivative objects for gradients. We normalise
        # symbolic nabla characters (\nabla) to Derivative when possible by
        # replacing them with the gradient operator acting on scalars.
        nabla = sp.Symbol("∇")
        if nabla in expr.free_symbols:
            expr = expr.subs(nabla, sp.Function("grad"))
        return expr

    def _units_vector(self, expr: sp.Expr) -> Tuple[Tuple[str, float], ...]:
        # A lightweight dimensional analysis stub: we look for SymPy physics
        # units and aggregate the powers. When none are present we return zeros.
        powers = {unit: 0.0 for unit in SI_BASE_UNITS}
        try:
            from sympy.physics import units as u
        except Exception:  # pragma: no cover - optional dependency
            return tuple(sorted(powers.items()))

        def accumulate(subexpr: sp.Expr) -> None:
            if subexpr.has(*u.__dict__.values()):
                for unit_name in SI_BASE_UNITS:
                    unit_obj = getattr(u, unit_name, None)
                    if unit_obj is None:
                        continue
                    if subexpr.has(unit_obj):
                        exp = sp.expand_logarithmic(sp.log(subexpr / unit_obj))
                        if exp.is_Number:
                            powers[unit_name] += float(exp)

        for arg in sp.preorder_traversal(expr):
            accumulate(arg)
        return tuple(sorted(powers.items()))

    def _content_hash(self, expr: sp.Expr, assumptions: Sequence[str]) -> str:
        normalized = sp.srepr(expr)
        hash_input = normalized + "|" + "|".join(sorted(assumptions))
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    def canonicalize(
        self,
        *,
        latex: Optional[str],
        sympy_str: Optional[str],
        assumptions: Sequence[str] | None = None,
        regime: Sequence[str] | None = None,
        field_tags: Sequence[str] | None = None,
        sources: Sequence[str] | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.UNCHECKED,
    ) -> CanonicalizationResult:
        expr = self._parse(latex=latex, sympy_str=sympy_str)
        expr = self._move_all_to_lhs(expr)
        expr = self._normalize_commutative(expr)
        expr = self._standardize_gradient(expr)
        expr, _ = self._alpha_rename(expr)
        expr = sp.simplify(expr)
        assumptions_seq = tuple(assumptions or ())
        units = self._units_vector(expr)
        statement_id = self._content_hash(expr, assumptions_seq)
        latex_variants: List[str] = []
        if latex:
            latex_variants.append(latex)
        sympy_srepr = sp.srepr(expr)
        statement = Statement(
            id=statement_id,
            latex_variants=latex_variants,
            sympy_srepr=sympy_srepr,
            assumptions=list(assumptions_seq),
            units=dict(units),
            regime=list(regime or ()),
            field_tags=list(field_tags or ()),
            sources=list(sources or ()),
            confidence=confidence,
        )
        return CanonicalizationResult(
            expression=expr,
            sympy_srepr=sympy_srepr,
            assumptions=assumptions_seq,
            units=units,
            statement=statement,
        )

    def statements_equivalent(
        self,
        left: Statement,
        right: Statement,
        *,
        assumptions: Optional[Sequence[str]] = None,
    ) -> bool:
        left_expr = sp.sympify(left.sympy_srepr)
        right_expr = sp.sympify(right.sympy_srepr)
        difference = sp.simplify(left_expr - right_expr)
        if difference == 0:
            return True
        symbols = sorted(difference.free_symbols, key=lambda sym: sym.name)
        for sample in self._generate_numeric_samples(len(symbols)):
            subs = {symbol: value for symbol, value in zip(symbols, sample)}
            try:
                left_val = complex(left_expr.evalf(subs=subs))
                right_val = complex(right_expr.evalf(subs=subs))
            except TypeError:
                continue
            if not math.isclose(float(left_val.real), float(right_val.real), rel_tol=1e-9):
                return False
        return True

    def _generate_numeric_samples(self, count: int) -> Iterable[Tuple[float, ...]]:
        if count == 0:
            yield ()
            return
        samples = [-2.0, -1.0, 0.5, 1.0, 2.0]
        max_samples = 10
        for idx, combo in enumerate(product(samples, repeat=count)):
            if idx >= max_samples:
                break
            yield combo


__all__ = ["Canonicalizer", "CanonicalizationResult"]
