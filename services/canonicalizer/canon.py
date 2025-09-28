from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from itertools import product
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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
from sympy.matrices.matrices import MatrixBase

__all__ = [
    "CanonicalStatement",
    "SymbolRoles",
    "EquivalenceReport",
    "canonicalize",
    "assess_equivalence",
    "units_transform",
]

_SI_BASES: Tuple[str, ...] = ("M", "L", "T", "I", "Θ", "N", "J")
_ZERO_VECTOR: Tuple[float, ...] = (0.0,) * len(_SI_BASES)

_OPERATOR_NORMALIZATION: Mapping[str, str] = {
    "div": "Div",
    "Div": "Div",
    "grad": "Grad",
    "Grad": "Grad",
    "curl": "Curl",
    "Curl": "Curl",
}

_CONSTANT_UNITS: Mapping[str, Tuple[float, ...]] = {
    "epsilon_0": (-1.0, -3.0, 4.0, 2.0, 0.0, 0.0, 0.0),
    "mu_0": (1.0, 1.0, -2.0, -2.0, 0.0, 0.0, 0.0),
    "c": (0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0),
    "g": (0.0, 1.0, -2.0, 0.0, 0.0, 0.0, 0.0),
}

_ASSUMPTION_PATTERNS: Mapping[re.Pattern[str], str] = {
    re.compile(r"\bfor\s+small\s+(?:theta|θ)\b", re.IGNORECASE): "small-angle",
    re.compile(r"\bin\s+vacuum\b", re.IGNORECASE): "vacuum",
    re.compile(r"\bsteady[-\s]?state\b", re.IGNORECASE): "steady-state",
}

_transformations = standard_transformations + (
    convert_xor,
    implicit_application,
    implicit_multiplication_application,
)
_PARSER_LOCALS = {name: sp.Function(name) for name in _OPERATOR_NORMALIZATION}


@dataclass(frozen=True)
class SymbolRoles:
    independent: Tuple[str, ...]
    parameters: Tuple[str, ...]
    constants: Tuple[str, ...]
    mapping: Tuple[Tuple[str, str], ...]


@dataclass(frozen=True)
class EquivalenceReport:
    relation: str
    max_delta: Optional[float]
    samples: Tuple[Tuple[Dict[str, float], float], ...]


@dataclass(frozen=True)
class CanonicalStatement:
    expression: sp.Expr
    sympy_srepr: str
    assumptions: Tuple[str, ...]
    units: Tuple[Tuple[str, float], ...]
    content_hash: str
    roles: SymbolRoles
    equivalence: Optional[EquivalenceReport] = None
    units_transform: Optional[str] = None


def canonicalize(
    expr_str: str,
    *,
    fmt: str = "latex",
    meta_text: Optional[str] = None,
) -> CanonicalStatement:
    """Canonicalize an expression into a symbolic normal form.

    Parameters
    ----------
    expr_str:
        Source expression represented either as LaTeX or a SymPy string.
    fmt:
        Either ``"latex"`` or ``"sympy"``.
    meta_text:
        Optional free-form text describing contextual assumptions. Phrases such
        as "for small θ" or "in vacuum" are converted into normalized tags.
    """

    raw_expr = _parse(expr_str, fmt)
    normalized = _normalize_expression(raw_expr)
    normalized = _normalize_operators(normalized)
    assumptions = _extract_assumptions(meta_text)
    units = _units_vector(normalized)
    renamed_expr, roles = _alpha_rename(normalized)
    simplified = sp.simplify(renamed_expr)
    sympy_srepr = sp.srepr(simplified)
    content_hash = _content_hash(sympy_srepr, assumptions, units)
    return CanonicalStatement(
        expression=simplified,
        sympy_srepr=sympy_srepr,
        assumptions=assumptions,
        units=units,
        content_hash=content_hash,
        roles=roles,
        units_transform=None,
    )


def assess_equivalence(
    left: sp.Expr,
    right: sp.Expr,
    *,
    assumptions: Sequence[str] | None = None,
    tolerance: float = 1e-6,
) -> EquivalenceReport:
    """Compare two SymPy expressions for exact or approximate equivalence."""

    assumptions = tuple(assumptions or ())
    difference = sp.simplify(left - right)
    if difference == 0:
        return EquivalenceReport("EXACT", 0.0, tuple())

    symbols = sorted(difference.free_symbols, key=lambda s: s.name)
    sample_values = _domain_safe_samples(difference, symbols, assumptions)
    deltas: List[Tuple[Dict[str, float], float]] = []
    max_delta: Optional[float] = None
    for values in sample_values:
        subs = {sym: val for sym, val in zip(symbols, values)}
        try:
            delta_val = difference.evalf(subs=subs)
        except Exception:
            continue
        if not delta_val.is_real:
            continue
        delta = float(abs(delta_val))
        deltas.append((subs, delta))
        max_delta = delta if max_delta is None else max(max_delta, delta)

    if max_delta is not None and max_delta <= tolerance:
        return EquivalenceReport("APPROX_OF", max_delta, tuple(deltas))

    return EquivalenceReport("NONE", max_delta, tuple(deltas))


def units_transform(expr: sp.Expr, *, source: str, target: str) -> Optional[sp.Expr]:
    """Placeholder for future Gaussian/SI conversion rules."""

    if source.lower() == target.lower():
        return expr
    return None


def _parser_locals_for(expr_str: str) -> Dict[str, object]:
    local_dict: Dict[str, object] = dict(_PARSER_LOCALS)
    for match in re.finditer(r"([A-Za-z]\w*)\s*\(", expr_str):
        name = match.group(1)
        if name in local_dict:
            continue
        if hasattr(sp, name):
            continue
        local_dict[name] = sp.Function(name)
    return local_dict


def _parse(expr_str: str, fmt: str) -> sp.Expr:
    if fmt not in {"latex", "sympy"}:
        raise ValueError("fmt must be either 'latex' or 'sympy'")
    if fmt == "latex":
        try:
            return parse_latex(expr_str)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Failed to parse LaTeX: {exc}") from exc
    return parse_expr(
        expr_str,
        transformations=_transformations,
        local_dict=_parser_locals_for(expr_str),
    )


def _normalize_expression(expr: sp.Expr) -> sp.Expr:
    expr = _move_to_lhs(expr)
    expr = sp.expand(expr, force=True)
    expr = sp.together(expr)
    expr = sp.factor_terms(expr)
    return sp.simplify(expr)


def _move_to_lhs(expr: sp.Expr) -> sp.Expr:
    if isinstance(expr, Eq):
        return sp.simplify(expr.lhs - expr.rhs)
    if expr.has(Eq):
        terms = [subexpr.lhs - subexpr.rhs for subexpr in expr.atoms(Eq)]
        return sp.simplify(sp.Add.fromiter(terms))
    return expr


def _normalize_operators(expr: sp.Expr) -> sp.Expr:
    normalized = expr
    for original, canonical in _OPERATOR_NORMALIZATION.items():
        original_function = sp.Function(original)
        canonical_function = sp.Function(canonical)
        normalized = normalized.replace(original_function, canonical_function)
        symbol = sp.Symbol(original)
        normalized = normalized.xreplace({symbol: canonical_function})
    return normalized


def _extract_assumptions(meta_text: Optional[str]) -> Tuple[str, ...]:
    if not meta_text:
        return tuple()
    normalized: List[str] = []
    for pattern, tag in _ASSUMPTION_PATTERNS.items():
        if pattern.search(meta_text):
            normalized.append(tag)
    return tuple(dict.fromkeys(normalized))


def _units_vector(expr: sp.Expr) -> Tuple[Tuple[str, float], ...]:
    units = _infer_units(expr)
    return tuple(zip(_SI_BASES, units))


def _infer_units(expr: sp.Expr) -> Tuple[float, ...]:
    if expr.is_Number:
        return _ZERO_VECTOR
    if isinstance(expr, sp.Symbol):
        return _CONSTANT_UNITS.get(expr.name, _ZERO_VECTOR)
    if isinstance(expr, sp.Function):
        # Assume dimensionless output for elementary functions.
        return _ZERO_VECTOR
    if expr.is_Add:
        term_units = {_infer_units(arg) for arg in expr.args}
        if not term_units:
            return _ZERO_VECTOR
        nonzero = {units for units in term_units if units != _ZERO_VECTOR}
        if len(nonzero) <= 1:
            return next(iter(nonzero)) if nonzero else _ZERO_VECTOR
        return _ZERO_VECTOR
    if expr.is_Mul:
        vector = list(_ZERO_VECTOR)
        for arg in expr.args:
            arg_units = _infer_units(arg)
            vector = [lhs + rhs for lhs, rhs in zip(vector, arg_units)]
        return tuple(vector)
    if expr.is_Pow:
        base_units = _infer_units(expr.base)
        if expr.exp.is_Number:
            exponent = float(expr.exp)
            return tuple(component * exponent for component in base_units)
        return _ZERO_VECTOR
    if isinstance(expr, sp.Derivative):
        func_units = _infer_units(expr.expr)
        variable_units = [_infer_units(var) for var in expr.variables]
        for v_units in variable_units:
            func_units = tuple(f - v for f, v in zip(func_units, v_units))
        return func_units
    if isinstance(expr, MatrixBase):
        element_units = {_infer_units(elem) for elem in expr}
        if not element_units:
            return _ZERO_VECTOR
        nonzero = {units for units in element_units if units != _ZERO_VECTOR}
        if len(nonzero) == 1:
            return nonzero.pop()
        if not nonzero:
            return _ZERO_VECTOR
        return _ZERO_VECTOR
    return _ZERO_VECTOR


def _alpha_rename(expr: sp.Expr) -> Tuple[sp.Expr, SymbolRoles]:
    ordered_symbols = list(dict.fromkeys(sorted(expr.atoms(sp.Symbol), key=lambda s: s.name)))
    constants = [sym for sym in ordered_symbols if sym.name in _CONSTANT_UNITS]
    independent_candidates = sorted(
        {sym for sym in _collect_independent_symbols(expr) if sym in ordered_symbols},
        key=lambda s: s.name,
    )
    if not independent_candidates:
        independent_candidates = [sym for sym in ordered_symbols if sym not in constants]
    parameters = [
        sym
        for sym in ordered_symbols
        if sym not in independent_candidates and sym not in constants
    ]

    mapping: Dict[sp.Symbol, sp.Symbol] = {}
    name_mapping: List[Tuple[str, str]] = []

    for index, sym in enumerate(independent_candidates, start=1):
        renamed = sp.Symbol(f"x{index}")
        mapping[sym] = renamed
        name_mapping.append((sym.name, renamed.name))
    for index, sym in enumerate(parameters, start=1):
        renamed = sp.Symbol(f"p{index}")
        mapping[sym] = renamed
        name_mapping.append((sym.name, renamed.name))
    for index, sym in enumerate(constants, start=1):
        renamed = sp.Symbol(f"c{index}")
        mapping[sym] = renamed
        name_mapping.append((sym.name, renamed.name))

    renamed_expr = expr.xreplace(mapping)
    roles = SymbolRoles(
        independent=tuple(mapping[s].name for s in independent_candidates),
        parameters=tuple(mapping[s].name for s in parameters),
        constants=tuple(mapping[s].name for s in constants),
        mapping=tuple(sorted(name_mapping, key=lambda pair: pair[1])),
    )
    return renamed_expr, roles


def _collect_independent_symbols(expr: sp.Expr) -> Iterable[sp.Symbol]:
    independent: set[sp.Symbol] = set()
    for derivative in expr.atoms(sp.Derivative):
        for variable in derivative.variables:
            if isinstance(variable, sp.Symbol):
                independent.add(variable)
    for func in expr.atoms(sp.Function):
        for argument in func.args:
            if isinstance(argument, sp.Symbol):
                independent.add(argument)
    for limit in expr.atoms(sp.Limit):
        if isinstance(limit.var, sp.Symbol):
            independent.add(limit.var)
    return independent


def _content_hash(
    sympy_srepr: str,
    assumptions: Sequence[str],
    units: Sequence[Tuple[str, float]],
) -> str:
    digest_input = "|".join([
        sympy_srepr,
        ",".join(sorted(assumptions)),
        ",".join(f"{name}:{value}" for name, value in units),
    ])
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def _domain_safe_samples(
    expr: sp.Expr,
    symbols: Sequence[sp.Symbol],
    assumptions: Sequence[str],
    *,
    max_samples: int = 12,
) -> Iterable[Tuple[float, ...]]:
    if not symbols:
        yield ()
        return

    requires_positive = expr.has(sp.log, sp.sqrt, sp.acos, sp.asin, sp.atanh)
    if "small-angle" in assumptions:
        base = [1e-3, 5e-3, 1e-2]
        if not requires_positive:
            base.append(-1e-3)
    else:
        base = [0.5, 1.0, 2.0] if requires_positive else [-2.0, -1.0, -0.5, 0.5, 1.0, 2.0]

    for index, combo in enumerate(product(base, repeat=len(symbols))):
        if index >= max_samples:
            break
        yield combo
