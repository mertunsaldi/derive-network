from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import sympy as sp

from derive_network import Canonicalizer, ConfidenceLevel, Derivation, GraphEdgeType, GraphStore


def _comma_separated(value: str) -> list[str]:
    if not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class PlaygroundApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Derivation Network Playground")
        self.geometry("1100x780")
        self.minsize(960, 640)

        self.canonicalizer = Canonicalizer()
        self.store = GraphStore()

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self._build_canonicalizer_tab(notebook)
        self._build_equivalence_tab(notebook)
        self._build_graph_tab(notebook)

    # ------------------------------------------------------------------
    # Canonicalizer tab
    # ------------------------------------------------------------------
    def _build_canonicalizer_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="Canonicalizer")

        input_frame = ttk.LabelFrame(frame, text="Input expression", padding=12)
        input_frame.pack(fill=tk.BOTH, expand=False, side=tk.TOP)

        ttk.Label(input_frame, text="LaTeX or SymPy expression:").grid(row=0, column=0, sticky=tk.W)
        self.canon_expr = ScrolledText(input_frame, height=4, width=60, wrap=tk.WORD)
        self.canon_expr.grid(row=1, column=0, columnspan=4, sticky=tk.EW, pady=(4, 8))
        input_frame.columnconfigure(0, weight=1)

        self.expr_format = tk.StringVar(value="latex")
        ttk.Radiobutton(input_frame, text="LaTeX", variable=self.expr_format, value="latex").grid(
            row=2, column=0, sticky=tk.W
        )
        ttk.Radiobutton(input_frame, text="SymPy", variable=self.expr_format, value="sympy").grid(
            row=2, column=1, sticky=tk.W
        )

        ttk.Label(input_frame, text="Assumptions / context (comma separated):").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(8, 0)
        )
        self.canon_meta = ttk.Entry(input_frame)
        self.canon_meta.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))

        ttk.Label(input_frame, text="Field tags (comma separated):").grid(
            row=5, column=0, sticky=tk.W
        )
        self.canon_fields = ttk.Entry(input_frame)
        self.canon_fields.grid(row=6, column=0, sticky=tk.EW, pady=(0, 8))

        ttk.Label(input_frame, text="Sources (comma separated):").grid(row=5, column=1, sticky=tk.W)
        self.canon_sources = ttk.Entry(input_frame)
        self.canon_sources.grid(row=6, column=1, sticky=tk.EW, pady=(0, 8))

        ttk.Button(input_frame, text="Canonicalize", command=self._canonicalize_expr).grid(
            row=7, column=0, sticky=tk.W
        )

        output_frame = ttk.LabelFrame(frame, text="Canonical form", padding=12)
        output_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP, pady=(12, 0))

        self.canon_output = ScrolledText(output_frame, wrap=tk.WORD)
        self.canon_output.pack(fill=tk.BOTH, expand=True)

    def _canonicalize_expr(self) -> None:
        expr = self.canon_expr.get("1.0", tk.END).strip()
        if not expr:
            messagebox.showinfo("Canonicalizer", "Please provide an expression to canonicalize.")
            return

        assumptions = _comma_separated(self.canon_meta.get())
        field_tags = _comma_separated(self.canon_fields.get())
        sources = _comma_separated(self.canon_sources.get())

        try:
            result = self.canonicalizer.canonicalize(
                latex=expr if self.expr_format.get() == "latex" else None,
                sympy_str=expr if self.expr_format.get() == "sympy" else None,
                assumptions=assumptions,
                field_tags=field_tags,
                sources=sources,
                confidence=ConfidenceLevel.CAS,
            )
        except Exception as exc:  # pragma: no cover - interactive guard
            messagebox.showerror("Canonicalizer", f"Failed to canonicalize expression:\n{exc}")
            return

        statement = result.statement
        output_lines = [
            "Canonical Statement",
            "-------------------",
            f"SymPy form: {sp.sstr(result.expression)}",
            f"SymPy srepr: {result.sympy_srepr}",
            f"Statement id (content hash): {statement.id}",
            f"Latex variants: {', '.join(statement.latex_variants) or '—'}",
            f"Assumptions: {', '.join(statement.assumptions) or '—'}",
            "Units:",
        ]
        if statement.units:
            for unit, power in statement.units.items():
                output_lines.append(f"  {unit}: {power}")
        else:
            output_lines.append("  dimensionless")
        output_lines.extend(
            [
                f"Field tags: {', '.join(statement.field_tags) or '—'}",
                f"Sources: {', '.join(statement.sources) or '—'}",
                "",
                "Tip: you can now add this statement to the graph tab by copying the id.",
            ]
        )
        self.canon_output.delete("1.0", tk.END)
        self.canon_output.insert(tk.END, "\n".join(output_lines))

    # ------------------------------------------------------------------
    # Equivalence tab
    # ------------------------------------------------------------------
    def _build_equivalence_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="Equivalence")

        upper = ttk.Frame(frame)
        upper.pack(fill=tk.BOTH, expand=False)

        left_frame = ttk.LabelFrame(upper, text="Left expression (SymPy)", padding=8)
        left_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 8))
        self.equiv_left = ScrolledText(left_frame, height=6, wrap=tk.WORD)
        self.equiv_left.pack(fill=tk.BOTH, expand=True)

        right_frame = ttk.LabelFrame(upper, text="Right expression (SymPy)", padding=8)
        right_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.equiv_right = ScrolledText(right_frame, height=6, wrap=tk.WORD)
        self.equiv_right.pack(fill=tk.BOTH, expand=True)

        options = ttk.Frame(frame)
        options.pack(fill=tk.X, pady=8)

        ttk.Label(options, text="Tolerance (for approximate match):").pack(side=tk.LEFT)
        self.equiv_tolerance = ttk.Entry(options, width=10)
        self.equiv_tolerance.insert(0, "1e-6")
        self.equiv_tolerance.pack(side=tk.LEFT, padx=4)

        ttk.Label(options, text="Additional assumptions (comma separated):").pack(side=tk.LEFT)
        self.equiv_assumptions = ttk.Entry(options, width=40)
        self.equiv_assumptions.pack(side=tk.LEFT, padx=4)

        ttk.Button(options, text="Assess equivalence", command=self._assess_equivalence).pack(
            side=tk.LEFT, padx=8
        )

        result_frame = ttk.LabelFrame(frame, text="Result", padding=8)
        result_frame.pack(fill=tk.BOTH, expand=True)
        self.equiv_output = ScrolledText(result_frame, wrap=tk.WORD)
        self.equiv_output.pack(fill=tk.BOTH, expand=True)

    def _assess_equivalence(self) -> None:
        left_text = self.equiv_left.get("1.0", tk.END).strip()
        right_text = self.equiv_right.get("1.0", tk.END).strip()
        if not left_text or not right_text:
            messagebox.showinfo("Equivalence", "Please provide expressions on both sides.")
            return

        try:
            left_expr = sp.sympify(left_text)
            right_expr = sp.sympify(right_text)
        except Exception as exc:  # pragma: no cover - interactive guard
            messagebox.showerror("Equivalence", f"Failed to parse expressions:\n{exc}")
            return

        assumptions = _comma_separated(self.equiv_assumptions.get())
        try:
            tolerance = float(self.equiv_tolerance.get())
        except ValueError:
            tolerance = 1e-6

        from derive_network.services.canonicalizer.canon import assess_equivalence

        report = assess_equivalence(left_expr, right_expr, assumptions=assumptions, tolerance=tolerance)
        lines = [
            f"Relation: {report.relation}",
            f"Max delta: {report.max_delta if report.max_delta is not None else '—'}",
            "Samples:",
        ]
        if report.samples:
            for sample, delta in report.samples:
                parts = ", ".join(f"{symbol}={value}" for symbol, value in sample.items())
                lines.append(f"  {parts} -> |Δ| = {delta}")
        else:
            lines.append("  Expressions are exactly equivalent")
        self.equiv_output.delete("1.0", tk.END)
        self.equiv_output.insert(tk.END, "\n".join(lines))

    # ------------------------------------------------------------------
    # Graph playground tab
    # ------------------------------------------------------------------
    def _build_graph_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="Graph Playground")

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, expand=False)

        ttk.Button(controls, text="Load mechanics demo", command=self._load_demo_graph).pack(
            side=tk.LEFT
        )
        ttk.Button(controls, text="Clear graph", command=self._clear_graph).pack(side=tk.LEFT, padx=8)

        column_container = ttk.Frame(frame)
        column_container.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        self._build_statement_column(column_container)
        self._build_derivation_column(column_container)
        self._build_relations_column(column_container)

    def _build_statement_column(self, parent: ttk.Frame) -> None:
        column = ttk.Frame(parent)
        column.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 8))

        add_box = ttk.LabelFrame(column, text="Add statement", padding=8)
        add_box.pack(fill=tk.X, expand=False)

        ttk.Label(add_box, text="LaTeX expression:").grid(row=0, column=0, sticky=tk.W)
        self.graph_statement_expr = ttk.Entry(add_box)
        self.graph_statement_expr.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Assumptions (comma separated):").grid(row=2, column=0, sticky=tk.W)
        self.graph_statement_assumptions = ttk.Entry(add_box)
        self.graph_statement_assumptions.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Field tags:").grid(row=4, column=0, sticky=tk.W)
        self.graph_statement_fields = ttk.Entry(add_box)
        self.graph_statement_fields.grid(row=5, column=0, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Sources:").grid(row=4, column=1, sticky=tk.W)
        self.graph_statement_sources = ttk.Entry(add_box)
        self.graph_statement_sources.grid(row=5, column=1, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Statement id (optional):").grid(row=6, column=0, sticky=tk.W)
        self.graph_statement_id = ttk.Entry(add_box)
        self.graph_statement_id.grid(row=7, column=0, sticky=tk.EW, pady=2)

        ttk.Button(add_box, text="Add to graph", command=self._add_statement).grid(
            row=8, column=0, sticky=tk.W, pady=(6, 0)
        )

        add_box.columnconfigure(0, weight=1)
        add_box.columnconfigure(1, weight=1)

        list_box = ttk.LabelFrame(column, text="Statements", padding=8)
        list_box.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.statement_list = tk.Listbox(list_box, exportselection=False)
        self.statement_list.pack(fill=tk.BOTH, expand=True)

    def _build_derivation_column(self, parent: ttk.Frame) -> None:
        column = ttk.Frame(parent)
        column.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 8))

        add_box = ttk.LabelFrame(column, text="Add derivation", padding=8)
        add_box.pack(fill=tk.X, expand=False)

        ttk.Label(add_box, text="Derivation id:").grid(row=0, column=0, sticky=tk.W)
        self.graph_derivation_id = ttk.Entry(add_box)
        self.graph_derivation_id.grid(row=1, column=0, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Input statement ids:").grid(row=2, column=0, sticky=tk.W)
        self.graph_derivation_inputs = ttk.Entry(add_box)
        self.graph_derivation_inputs.grid(row=3, column=0, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Output statement ids:").grid(row=4, column=0, sticky=tk.W)
        self.graph_derivation_outputs = ttk.Entry(add_box)
        self.graph_derivation_outputs.grid(row=5, column=0, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Rule tags:").grid(row=6, column=0, sticky=tk.W)
        self.graph_derivation_rules = ttk.Entry(add_box)
        self.graph_derivation_rules.grid(row=7, column=0, sticky=tk.EW, pady=2)

        ttk.Label(add_box, text="Assumptions:").grid(row=8, column=0, sticky=tk.W)
        self.graph_derivation_assumptions = ttk.Entry(add_box)
        self.graph_derivation_assumptions.grid(row=9, column=0, sticky=tk.EW, pady=2)

        self.graph_derivation_exact = tk.BooleanVar(value=True)
        ttk.Checkbutton(add_box, text="Exact derivation", variable=self.graph_derivation_exact).grid(
            row=10, column=0, sticky=tk.W
        )

        ttk.Button(add_box, text="Add derivation", command=self._add_derivation).grid(
            row=11, column=0, sticky=tk.W, pady=(6, 0)
        )

        add_box.columnconfigure(0, weight=1)

        list_box = ttk.LabelFrame(column, text="Derivations", padding=8)
        list_box.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.derivation_list = tk.Listbox(list_box, exportselection=False)
        self.derivation_list.pack(fill=tk.BOTH, expand=True)

    def _build_relations_column(self, parent: ttk.Frame) -> None:
        column = ttk.Frame(parent)
        column.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        relation_box = ttk.LabelFrame(column, text="Relations", padding=8)
        relation_box.pack(fill=tk.X, expand=False)

        ttk.Label(relation_box, text="Source node id:").grid(row=0, column=0, sticky=tk.W)
        self.graph_relation_source = ttk.Entry(relation_box)
        self.graph_relation_source.grid(row=1, column=0, sticky=tk.EW, pady=2)

        ttk.Label(relation_box, text="Target node id:").grid(row=0, column=1, sticky=tk.W)
        self.graph_relation_target = ttk.Entry(relation_box)
        self.graph_relation_target.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(relation_box, text="Relation type:").grid(row=2, column=0, sticky=tk.W)
        self.graph_relation_type = ttk.Combobox(
            relation_box,
            values=[
                GraphEdgeType.INPUT_OF,
                GraphEdgeType.OUTPUT_OF,
                GraphEdgeType.EQUIVALENT_TO,
                GraphEdgeType.SPECIAL_CASE_OF,
                GraphEdgeType.LIMIT_OF,
                GraphEdgeType.APPROX_OF,
                GraphEdgeType.REFORMULATION_OF,
                GraphEdgeType.UNITS_TRANSFORM,
                GraphEdgeType.ASSUMES,
            ],
        )
        self.graph_relation_type.grid(row=3, column=0, sticky=tk.EW, pady=2)

        ttk.Label(relation_box, text="Attributes (key=value pairs, comma separated):").grid(
            row=4, column=0, columnspan=2, sticky=tk.W
        )
        self.graph_relation_attrs = ttk.Entry(relation_box)
        self.graph_relation_attrs.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=2)

        ttk.Button(relation_box, text="Add relation", command=self._add_relation).grid(
            row=6, column=0, sticky=tk.W, pady=(6, 0)
        )

        relation_box.columnconfigure(0, weight=1)
        relation_box.columnconfigure(1, weight=1)

        path_box = ttk.LabelFrame(column, text="Shortest path", padding=8)
        path_box.pack(fill=tk.X, expand=False, pady=(12, 0))

        ttk.Label(path_box, text="Source id:").grid(row=0, column=0, sticky=tk.W)
        self.path_source = ttk.Entry(path_box)
        self.path_source.grid(row=1, column=0, sticky=tk.EW)

        ttk.Label(path_box, text="Target id:").grid(row=0, column=1, sticky=tk.W)
        self.path_target = ttk.Entry(path_box)
        self.path_target.grid(row=1, column=1, sticky=tk.EW)

        ttk.Label(path_box, text="Preferred rule tags (comma separated):").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(8, 0)
        )
        self.path_preferences = ttk.Entry(path_box)
        self.path_preferences.grid(row=3, column=0, columnspan=2, sticky=tk.EW)

        ttk.Button(path_box, text="Compute path", command=self._compute_path).grid(
            row=4, column=0, sticky=tk.W, pady=(6, 0)
        )

        path_box.columnconfigure(0, weight=1)
        path_box.columnconfigure(1, weight=1)

        list_box = ttk.LabelFrame(column, text="Graph summary", padding=8)
        list_box.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.graph_summary = ScrolledText(list_box, wrap=tk.WORD)
        self.graph_summary.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Graph interactions
    # ------------------------------------------------------------------
    def _add_statement(self) -> None:
        latex = self.graph_statement_expr.get().strip()
        if not latex:
            messagebox.showinfo("Graph", "Please provide a LaTeX expression for the statement.")
            return

        assumptions = _comma_separated(self.graph_statement_assumptions.get())
        field_tags = _comma_separated(self.graph_statement_fields.get())
        sources = _comma_separated(self.graph_statement_sources.get())

        try:
            result = self.canonicalizer.canonicalize(
                latex=latex,
                sympy_str=None,
                assumptions=assumptions,
                field_tags=field_tags,
                sources=sources,
            )
        except Exception as exc:  # pragma: no cover - interactive guard
            messagebox.showerror("Graph", f"Failed to canonicalize statement:\n{exc}")
            return

        statement = result.statement
        override_id = self.graph_statement_id.get().strip()
        if override_id:
            statement = statement.model_copy(update={"id": override_id})

        self.store.add_statement(statement)
        self._refresh_graph_state()
        self.graph_summary.insert(tk.END, f"Added statement {statement.id}\n")

    def _add_derivation(self) -> None:
        derivation_id = self.graph_derivation_id.get().strip()
        if not derivation_id:
            messagebox.showinfo("Graph", "Please provide an id for the derivation.")
            return

        inputs = _comma_separated(self.graph_derivation_inputs.get())
        outputs = _comma_separated(self.graph_derivation_outputs.get())
        if not inputs or not outputs:
            messagebox.showinfo("Graph", "Derivations require at least one input and output id.")
            return

        rule_tags = _comma_separated(self.graph_derivation_rules.get())
        assumptions = _comma_separated(self.graph_derivation_assumptions.get())

        derivation = Derivation(
            id=derivation_id,
            rule_tags=rule_tags,
            exact=self.graph_derivation_exact.get(),
            assumptions=assumptions,
        )

        try:
            self.store.add_derivation(derivation, inputs=inputs, outputs=outputs)
        except KeyError as exc:  # pragma: no cover - interactive guard
            messagebox.showerror("Graph", str(exc))
            return

        self._refresh_graph_state()
        self.graph_summary.insert(tk.END, f"Added derivation {derivation.id}\n")

    def _add_relation(self) -> None:
        source = self.graph_relation_source.get().strip()
        target = self.graph_relation_target.get().strip()
        relation_type = self.graph_relation_type.get().strip()
        if not source or not target or not relation_type:
            messagebox.showinfo(
                "Graph", "Please provide source id, target id and relation type for the edge."
            )
            return

        attributes_text = self.graph_relation_attrs.get().strip()
        attributes: dict[str, object] = {}
        if attributes_text:
            for pair in attributes_text.split(","):
                if "=" not in pair:
                    continue
                key, value = pair.split("=", 1)
                attributes[key.strip()] = value.strip()

        try:
            self.store.add_relation(relation_type, source, target, attributes=attributes)
        except KeyError as exc:  # pragma: no cover - interactive guard
            messagebox.showerror("Graph", str(exc))
            return

        self._refresh_graph_state()
        self.graph_summary.insert(tk.END, f"Added relation {relation_type}: {source} -> {target}\n")

    def _compute_path(self) -> None:
        source = self.path_source.get().strip()
        target = self.path_target.get().strip()
        if not source or not target:
            messagebox.showinfo("Graph", "Please fill in both source and target ids.")
            return

        preferences = _comma_separated(self.path_preferences.get())
        try:
            path, node_data = self.store.shortest_path(source, target, preferences=preferences)
        except Exception as exc:  # pragma: no cover - interactive guard
            messagebox.showerror("Graph", f"Unable to find path:\n{exc}")
            return

        lines = ["Shortest path:", " -> ".join(path), "", "Nodes:"]
        for node in path:
            data = node_data.get(node, {})
            lines.append(f"- {node}: {data.get('type', 'unknown')}")
        self.graph_summary.insert(tk.END, "\n".join(lines) + "\n")
        self.graph_summary.see(tk.END)

    def _refresh_graph_state(self) -> None:
        self.statement_list.delete(0, tk.END)
        for statement in self.store.list_statements():
            label = f"{statement.id} :: {statement.latex_variants[0] if statement.latex_variants else statement.sympy_srepr}"
            self.statement_list.insert(tk.END, label)

        self.derivation_list.delete(0, tk.END)
        for derivation in self.store.list_derivations():
            tag_preview = ", ".join(derivation.rule_tags) or "<no tags>"
            self.derivation_list.insert(tk.END, f"{derivation.id} :: {tag_preview}")

        summary_lines = [
            f"Statements: {len(self.store.list_statements())}",
            f"Derivations: {len(self.store.list_derivations())}",
            f"Relations: {len(self.store.list_relations())}",
            "",
        ]
        for relation in self.store.list_relations():
            attr_display = (
                ", ".join(f"{key}={value}" for key, value in relation.attributes.items())
                or "—"
            )
            summary_lines.append(
                f"{relation.type}: {relation.source} -> {relation.target} ({attr_display})"
            )
        self.graph_summary.delete("1.0", tk.END)
        self.graph_summary.insert(tk.END, "\n".join(summary_lines))

    def _load_demo_graph(self) -> None:
        from examples.seed_data import load_seed_graph

        self.store = load_seed_graph()
        self._refresh_graph_state()
        self.graph_summary.insert(tk.END, "Loaded mechanics/electromagnetism demo graph.\n")

    def _clear_graph(self) -> None:
        self.store = GraphStore()
        self._refresh_graph_state()
        self.graph_summary.delete("1.0", tk.END)
        self.graph_summary.insert(tk.END, "Graph cleared. Add new statements and derivations to begin.\n")


def main() -> None:
    app = PlaygroundApp()
    app.mainloop()


if __name__ == "__main__":
    main()
