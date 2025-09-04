# 💰 Simple Tax Calculator (Tkinter) 🧮

A lightweight, educational **desktop app** for calculating taxes with either a **flat** or **progressive** system. Ideal for quick experimentation, classroom demos, or personal finance tinkering—***not*** a substitute for professional advice.

---

## ✨ Features

|                           | Description                                                                       |
| ------------------------- | --------------------------------------------------------------------------------- |
| ⚡ **Two Modes**           | Toggle between *Flat‑Rate* and *Progressive* calculations.                        |
| 📝 **Editable Brackets**  | Add / remove brackets on‑the‑fly for progressive regimes.                         |
| 💾 **Profile Management** | Save and load tax profiles as readable JSON—great for sharing.                    |
| 📊 **Instant Metrics**    | Displays taxable income, total tax, net income, effective **and** marginal rates. |
| 🌐 **Currency‑Agnostic**  | Pick any currency symbol (€, ₹, ¥, etc.).                                         |

> **Note** This tool is for illustration only—always consult a certified professional for real tax matters.

---

## 🚀 Quick Start

### 1. Clone & install

```bash
# Clone
git clone https://github.com/<your‑handle>/tax‑calculator.git
cd tax‑calculator

# (Optional) create a venv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install runtime deps (Tkinter is included with most Python installers)
pip install -r requirements.txt  # Currently empty, kept for future
```

### 2. Run the app

```bash
python tax_calculator_fixed.py
```

> **Heads‑up** The first launch seeds `tax_profiles.json` with two example profiles—feel free to tweak or replace them.

---

## 🖥️ Usage at a Glance

1. **Enter Gross Income** and optional **Deductions**.
2. **Choose Mode**:

   * *Flat* → set a single percentage.
   * *Progressive* → define brackets with an *upper bound* and *rate* (leave the last bound blank → ∞).
3. Hit **Calculate** to see **Taxable**, **Tax**, **Net**, **Effective Rate**, and **Marginal Rate**.
4. Click **Save As…** to store the current configuration for later.

![screenshot placeholder](docs/screenshot.png)

---

## 📂 Project Layout

```text
├── tax_calculator_fixed.py   # Main application
├── tax_profiles.json         # Auto‑generated profile store
├── README.md                 # You are here
└── docs/
    └── screenshot.png        # (Optional) add screenshots / diagrams
```

---

## 🤝 Contributing

1. Fork the repo and create your branch: `git checkout -b feature/awesome`.
2. Commit your changes with clear messages.
3. Push to the branch: `git push origin feature/awesome`.
4. Open a **Pull Request**.

All code should follow **PEP 8** and include type hints where practical. For UI tweaks, keep the minimal, clean aesthetic intact.

---

## 🙏 Acknowledgments

* Python ❤️ Tkinter for the GUI stack.
* Inspired by countless late‑night tax calculations gone wrong.

<div align="center">GLHF &nbsp;and&nbsp; ☕</div>
