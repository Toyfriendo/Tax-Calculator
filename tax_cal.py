"""
Simple Tax Calculator App (Tkinter)
===================================
Features
--------
* Flat **or** progressive tax calculation
* Editable progressive brackets (add/remove rows)
* Save/Load profiles to JSON (in the project dir)
* Shows taxable income, total tax, net income, effective and marginal rates

Notes
-----
* This is an educational tool, **not** tax or legal advice.
* Default sample profiles are illustrative; edit to match your jurisdiction.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

PROFILE_FILE = "tax_profiles.json"


# ---------------------------------------------------------------------------
#  Data models
# ---------------------------------------------------------------------------
@dataclass
class Bracket:
    up_to: Optional[float]  # None means infinity
    rate: float             # percent


@dataclass
class TaxProfile:
    name: str
    mode: str  # "flat" or "progressive"
    flat_rate: float = 10.0
    brackets: List[Bracket] = None

    # ---------------- JSON helpers ----------------
    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mode": self.mode,
            "flat_rate": self.flat_rate,
            "brackets": [asdict(b) for b in (self.brackets or [])],
        }

    @staticmethod
    def from_json(d: Dict[str, Any]) -> "TaxProfile":
        return TaxProfile(
            name=d.get("name", "Unnamed"),
            mode=d.get("mode", "flat"),
            flat_rate=float(d.get("flat_rate", 10.0)),
            brackets=[Bracket(b.get("up_to"), float(b.get("rate", 0))) for b in d.get("brackets", [])],
        )


# ---------------------------------------------------------------------------
#  Persisting profiles
# ---------------------------------------------------------------------------

def load_profiles() -> Dict[str, TaxProfile]:
    """Load existing profiles or seed a default set on first run."""
    if not os.path.exists(PROFILE_FILE):
        # Seed with a couple of illustrative profiles
        default = {
            "Flat 10%": TaxProfile(name="Flat 10%", mode="flat", flat_rate=10.0, brackets=[]).to_json(),
            "Sample Progressive": TaxProfile(
                name="Sample Progressive",
                mode="progressive",
                brackets=[
                    Bracket(10_000, 5.0),   # 0–10 k → 5 %
                    Bracket(30_000, 10.0),  # 10 k–30 k → 10 %
                    Bracket(80_000, 20.0),  # 30 k–80 k → 20 %
                    Bracket(None, 30.0),    # 80 k+ → 30 %
                ],
            ).to_json(),
        }
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return {k: TaxProfile.from_json(v) for k, v in default.items()}

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    profiles = {name: TaxProfile.from_json(p) for name, p in raw.items()}

    # Keep keys consistent with profile.name to avoid duplicates
    return {v.name: v for v in profiles.values()}


def save_profiles(profiles: Dict[str, TaxProfile]):
    serial = {name: p.to_json() for name, p in profiles.items()}
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(serial, f, indent=2)


# ---------------------------------------------------------------------------
#  Utility helpers
# ---------------------------------------------------------------------------

def format_money(amount: float, symbol: str = "$") -> str:
    return f"{symbol}{amount:,.2f}"


def compute_tax_flat(taxable: float, rate: float) -> tuple[float, float]:
    tax = max(0.0, taxable) * (rate / 100.0)
    return tax, rate


def compute_tax_progressive(taxable: float, brackets: List[Bracket]) -> tuple[float, float]:
    """Return (total_tax, marginal_rate)."""
    # Ensure brackets are sorted (None last)
    cleaned: List[Bracket] = sorted(
        [Bracket(float("inf") if b.up_to is None else float(b.up_to), float(b.rate)) for b in brackets],
        key=lambda b: b.up_to,
    )

    # Guarantee an infinite bracket exists so we don't special‑case tail calculation
    if cleaned[-1].up_to != float("inf"):
        cleaned.append(Bracket(float("inf"), cleaned[-1].rate))

    remaining = max(0.0, taxable)
    lower_bound = 0.0
    total_tax = 0.0
    marginal_rate = 0.0

    for b in cleaned:
        upper_bound = b.up_to
        span = max(0.0, min(remaining, upper_bound - lower_bound))
        if span > 0:
            total_tax += span * (b.rate / 100.0)
            remaining -= span
            marginal_rate = b.rate
        lower_bound = upper_bound
        if remaining <= 0:
            break

    return total_tax, marginal_rate


# ---------------------------------------------------------------------------
#  Tkinter GUI
# ---------------------------------------------------------------------------

class TaxApp(tk.Tk):
    """Main application window."""

    # ---------------- Construction ----------------
    def __init__(self):
        super().__init__()
        self.title("Tax Calculator")
        self.geometry("780x600")
        self.minsize(720, 560)

        # Load profiles before building the UI so the combobox has values
        self.profiles = load_profiles()

        # State variables
        self.var_income = tk.StringVar(value="60000")
        self.var_deductions = tk.StringVar(value="0")
        self.var_currency = tk.StringVar(value="$")
        self.var_mode = tk.StringVar(value="flat")
        self.var_flat_rate = tk.StringVar(value="10.0")
        self.var_profile = tk.StringVar(value="Flat 10%")

        self.bracket_rows: List[Dict[str, Any]] = []  # [{frame, up_to_var, rate_var}]

        self._build_ui()
        self._load_profile_by_name(self.var_profile.get())

    # ---------------- Widget helpers ----------------
    def _set_state_recursive(self, widget: tk.Widget, state: str):
        """Recursively set the ttk state of a widget *and* all its descendants."""
        try:
            widget.configure(state=state)
        except tk.TclError:
            # Frame‑like widgets have no state – ignore
            pass
        for child in widget.winfo_children():
            self._set_state_recursive(child, state)

    # ---------------- UI build ----------------
    def _build_ui(self):
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # ── Profile select / save ────────────────────────────────────────────
        prof_frame = ttk.LabelFrame(outer, text="Profile")
        prof_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(prof_frame, text="Select:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.cbo_profile = ttk.Combobox(
            prof_frame,
            textvariable=self.var_profile,
            values=list(self.profiles.keys()),
            state="readonly",
            width=28,
        )
        self.cbo_profile.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Button(prof_frame, text="Load", command=self.on_load_profile).grid(row=0, column=2, padx=6, pady=6)
        ttk.Button(prof_frame, text="Save As…", command=self.on_save_profile).grid(row=0, column=3, padx=6, pady=6)

        # ── Income / deduction inputs ────────────────────────────────────────
        inputs = ttk.LabelFrame(outer, text="Inputs")
        inputs.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(inputs, text="Gross Income").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(inputs, textvariable=self.var_income, width=18).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(inputs, text="Deductions").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        ttk.Entry(inputs, textvariable=self.var_deductions, width=18).grid(row=0, column=3, padx=6, pady=6, sticky="w")
        ttk.Label(inputs, text="Currency Symbol").grid(row=0, column=4, padx=6, pady=6, sticky="e")
        ttk.Entry(inputs, textvariable=self.var_currency, width=8).grid(row=0, column=5, padx=6, pady=6, sticky="w")

        # ── Mode select ──────────────────────────────────────────────────────
        mode_frame = ttk.LabelFrame(outer, text="Mode")
        mode_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Radiobutton(mode_frame, text="Flat", variable=self.var_mode, value="flat", command=self._on_mode_change).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Radiobutton(mode_frame, text="Progressive", variable=self.var_mode, value="progressive", command=self._on_mode_change).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        # Flat‑rate controls
        self.flat_container = ttk.Frame(mode_frame)
        self.flat_container.grid(row=1, column=0, columnspan=2, sticky="w", padx=6, pady=2)
        ttk.Label(self.flat_container, text="Flat Rate (%):").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(self.flat_container, textvariable=self.var_flat_rate, width=10).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        # Progressive controls
        self.prog_container = ttk.Frame(mode_frame)
        self.prog_container.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=6, pady=2)

        hdr = ttk.Frame(self.prog_container)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="#", width=3).grid(row=0, column=0, padx=4)
        ttk.Label(hdr, text="Up To (inclusive)", width=22).grid(row=0, column=1, padx=4)
        ttk.Label(hdr, text="Rate %", width=10).grid(row=0, column=2, padx=4)
        ttk.Label(hdr, text="Actions", width=10).grid(row=0, column=3, padx=4)

        self.rows_frame = ttk.Frame(self.prog_container)
        self.rows_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self.prog_container, text="Add Bracket", command=self.add_bracket_row).pack(anchor="w", padx=4, pady=6)

        # ── Action buttons ───────────────────────────────────────────────────
        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(actions, text="Calculate", command=self.on_calculate).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Reset", command=self.on_reset).pack(side=tk.LEFT, padx=4)

        # ── Results ──────────────────────────────────────────────────────────
        result = ttk.LabelFrame(outer, text="Results")
        result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.lbl_taxable = ttk.Label(result, text="Taxable: -")
        self.lbl_taxable.pack(anchor="w", padx=8, pady=4)
        self.lbl_tax = ttk.Label(result, text="Tax: -")
        self.lbl_tax.pack(anchor="w", padx=8, pady=4)
        self.lbl_net = ttk.Label(result, text="Net Income: -")
        self.lbl_net.pack(anchor="w", padx=8, pady=4)
        self.lbl_effective = ttk.Label(result, text="Effective Rate: -")
        self.lbl_effective.pack(anchor="w", padx=8, pady=4)
        self.lbl_marginal = ttk.Label(result, text="Marginal Rate: -")
        self.lbl_marginal.pack(anchor="w", padx=8, pady=4)

        # Initialise widget states
        self._on_mode_change()

    # ---------------- Bracket row helpers ----------------
    def add_bracket_row(self, up_to: Optional[float] = None, rate: float = 0.0):
        idx = len(self.bracket_rows) + 1
        row_frame = ttk.Frame(self.rows_frame)
        row_frame.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(row_frame, text=str(idx), width=3).grid(row=0, column=0)
        up_var = tk.StringVar(value="" if up_to is None or up_to == float("inf") else str(up_to))
        rate_var = tk.StringVar(value=str(rate))
        ttk.Entry(row_frame, textvariable=up_var, width=22).grid(row=0, column=1, padx=4)
        ttk.Entry(row_frame, textvariable=rate_var, width=10).grid(row=0, column=2, padx=4)

        def remove_row():
            row_frame.destroy()
            self.bracket_rows.remove(entry)
            self._renumber_rows()

        ttk.Button(row_frame, text="Remove", command=remove_row).grid(row=0, column=3, padx=4)
        entry = {"frame": row_frame, "up_to_var": up_var, "rate_var": rate_var}
        self.bracket_rows.append(entry)

    def _renumber_rows(self):
        for i, entry in enumerate(self.bracket_rows, start=1):
            for child in entry["frame"].winfo_children():
                if child.grid_info().get("column") == 0:
                    child.configure(text=str(i))

    def clear_bracket_rows(self):
        for entry in list(self.bracket_rows):
            entry["frame"].destroy()
        self.bracket_rows.clear()

    # ---------------- Profile handling ----------------
    def _load_profile_by_name(self, name: str):
        prof = self.profiles.get(name)
        if not prof:
            return
        self.var_mode.set(prof.mode)
        self.var_flat_rate.set(str(prof.flat_rate))
        self.clear_bracket_rows()
        for b in prof.brackets or []:
            self.add_bracket_row(None if b.up_to == float("inf") else b.up_to, b.rate)
        self._on_mode_change()

    def on_load_profile(self):
        self._load_profile_by_name(self.var_profile.get())

    def on_save_profile(self):
        name = simpledialog.askstring("Save Profile", "Profile name:", parent=self)
        if not name:
            return
        try:
            prof = self._collect_profile(name)
        except ValueError as e:
            messagebox.showerror("Invalid Profile", str(e))
            return
        self.profiles[name] = prof
        save_profiles(self.profiles)
        self.cbo_profile.configure(values=list(self.profiles.keys()))
        self.var_profile.set(name)
        messagebox.showinfo("Saved", f"Profile '{name}' saved to {PROFILE_FILE}")

    def _collect_profile(self, name: str) -> TaxProfile:
        mode = self.var_mode.get()
        if mode == "flat":
            try:
                rate = float(self.var_flat_rate.get())
            except ValueError:
                raise ValueError("Flat rate must be a number.")
            return TaxProfile(name=name, mode=mode, flat_rate=rate, brackets=[])
        else:
            brackets = self._collect_brackets()
            return TaxProfile(name=name, mode=mode, brackets=brackets)

    # ---------------- Mode toggle handling ----------------
    def _on_mode_change(self):
        mode = self.var_mode.get()
        if mode == "flat":
            self._set_state_recursive(self.flat_container, "normal")
            self._set_state_recursive(self.prog_container, "disabled")
        else:
            self._set_state_recursive(self.flat_container, "disabled")
            self._set_state_recursive(self.prog_container, "normal")

    # ---------------- Input collection ----------------
    def _collect_numbers(self) -> tuple[float, float]:
        try:
            income = float(self.var_income.get())
            deductions = float(self.var_deductions.get())
            if income < 0 or deductions < 0:
                raise ValueError
        except ValueError:
            raise ValueError("Income and deductions must be non‑negative numbers.")
        return income, deductions

    def _collect_brackets(self) -> List[Bracket]:
        rows: List[Bracket] = []
        for r in self.bracket_rows:
            up_s = r["up_to_var"].get().strip()
            rate_s = r["rate_var"].get().strip()
            if rate_s == "":
                raise ValueError("Each bracket must have a rate.")
            try:
                rate = float(rate_s)
            except ValueError:
                raise ValueError("Rates must be numbers.")

            # Empty "up_to" means infinity
            up_val: Optional[float]
            if up_s == "":
                up_val = None
            else:
                try:
                    up_val = float(up_s)
                except ValueError:
                    raise ValueError("'Up To' values must be numbers or left blank for infinity.")
            rows.append(Bracket(up_val, rate))

        # Validate duplicate finite bounds
        finite_bounds = [b.up_to for b in rows if b.up_to is not None]
        if len(set(finite_bounds)) != len(finite_bounds):
            raise ValueError("Duplicate 'Up To' values found.")

        # Sort ascending (None → inf at end)
        rows.sort(key=lambda b: float("inf") if b.up_to is None else b.up_to)
        return rows

    # ---------------- Actions ----------------
    def on_calculate(self):
        try:
            income, deductions = self._collect_numbers()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        taxable = max(0.0, income - deductions)
        mode = self.var_mode.get()

        if mode == "flat":
            try:
                rate = float(self.var_flat_rate.get())
            except ValueError:
                messagebox.showerror("Invalid Rate", "Flat rate must be a number.")
                return
            tax, marginal = compute_tax_flat(taxable, rate)
        else:
            try:
                brackets = self._collect_brackets()
            except ValueError as e:
                messagebox.showerror("Invalid Brackets", str(e))
                return
            tax, marginal = compute_tax_progressive(taxable, brackets)

        net = income - tax
        eff_rate = (tax / income * 100.0) if income > 0 else 0.0
        sym = (self.var_currency.get() or "$").strip()

        self.lbl_taxable.configure(text=f"Taxable: {format_money(taxable, sym)}")
        self.lbl_tax.configure(text=f"Tax: {format_money(tax, sym)}")
        self.lbl_net.configure(text=f"Net Income: {format_money(net, sym)}")
        self.lbl_effective.configure(text=f"Effective Rate: {eff_rate:.2f}%")
        self.lbl_marginal.configure(text=f"Marginal Rate: {marginal:.2f}%")

    def on_reset(self):
        self.var_income.set("60000")
        self.var_deductions.set("0")
        self.var_currency.set("$")
        self.var_mode.set("flat")
        self.var_flat_rate.set("10.0")
        self.clear_bracket_rows()
        self._on_mode_change()


# ---------------------------------------------------------------------------
#  Main entry‑point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = TaxApp()
    app.mainloop()
