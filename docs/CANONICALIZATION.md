# Canonicalization Pipeline

The canonicalization service converts LaTeX or SymPy strings into a stable
symbolic representation that can be hashed, compared and reused across the
Derive Network platform. The pipeline is deterministic and consists of the
following stages:

1. **Parsing** – input strings are parsed either with SymPy's LaTeX parser or
   the standard SymPy expression parser (with implicit multiplication and
   function application enabled). Parsing errors are raised as ``ValueError``.
2. **Normalization** – equations are rewritten onto the left-hand side and the
   algebra is canonicalised through ``expand → together → factor_terms →
   simplify``. This guarantees commutative ordering and factors global numeric
   constants.
3. **Operator Normalization** – occurrences of ``div``, ``grad`` and ``curl``
   are promoted to explicit ``Div()``, ``Grad()`` and ``Curl()`` SymPy
   ``Function`` symbols. This keeps vector calculus operators consistent across
   different authoring styles.
4. **Units Inference** – a lightweight dimensional analysis pass tracks base SI
   exponents (``M, L, T, I, Θ, N, J``). Known physical constants (``ε₀, μ₀, c, g``)
   are recognised via a registry; addition checks require matching dimensions
   and derivatives adjust units by subtracting the dimensions of the variables.
5. **Alpha Renaming** – free symbols are partitioned into independent variables
   (arguments of functions, derivative variables and limit variables), generic
   parameters, and recognised constants. They are deterministically renamed to
   ``xₙ``, ``pₙ`` and ``cₙ`` respectively, and a mapping is recorded for traceability.
6. **Assumptions Extraction** – contextual phrases found in accompanying prose
   (e.g. "for small θ", "in vacuum", "steady-state") are mapped to normalized
   assumption tags.
7. **Hashing** – the SymPy ``srepr`` of the renamed expression, the ordered list
   of assumptions and the inferred units vector are concatenated and hashed with
   SHA-256 to produce a stable content identifier.

## Equivalence Checking

For comparison tasks the module provides ``assess_equivalence`` which first
performs symbolic cancellation. If exact equivalence fails, it evaluates the
expressions on domain-aware sample points (respecting assumptions such as the
small-angle regime) and reports the maximum absolute deviation. Results are
classified as ``EXACT`` when ``simplify(A - B)`` is zero, ``APPROX_OF`` when
all samples fall within the tolerance, or ``NONE`` otherwise.

## Units Transform Placeholder

A placeholder ``units_transform`` function is included for future Gaussian ↔ SI
conversion logic. It currently returns ``None`` for unsupported conversions and
passes through expressions when the source and target systems match.
