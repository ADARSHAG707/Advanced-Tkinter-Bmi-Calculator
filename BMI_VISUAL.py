import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass, asdict
from math import isnan
import math
import json
import csv
import os
from pathlib import Path
from datetime import datetime

APP_NAME = "Tk BMI Pro"
APP_ID = "tk_bmi_pro"
DATA_DIR = Path.home() / ".bmi_tool"
HISTORY_FILE = DATA_DIR / "history.json"

@dataclass
class Person:
    sex: str
    age: float
    height_cm: float
    weight_kg: float
    waist_cm: float

@dataclass
class Result:
    bmi: float
    category: str
    risk: str
    whtr: float
    body_fat: float
    bmr_msj: float
    bmr_hb: float
    tdee: float
    ideal_weights: dict

class UnitSystem:
    METRIC = "Metric"
    IMPERIAL = "Imperial"

class ActivityLevel:
    LEVELS = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9,
    }

class UndoRedo:
    def __init__(self):
        self.stack = []
        self.redo_stack = []
    def push(self, state):
        self.stack.append(state)
        self.redo_stack.clear()
    def undo(self, current_state):
        if not self.stack:
            return current_state
        self.redo_stack.append(current_state)
        return self.stack.pop()
    def redo(self, current_state):
        if not self.redo_stack:
            return current_state
        self.stack.append(current_state)
        return self.redo_stack.pop()

class HistoryStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write([])
    def _read(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    def _write(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    def add_entry(self, payload: dict):
        data = self._read()
        data.append(payload)
        self._write(data)
    def all(self):
        return self._read()
    def clear(self):
        self._write([])

class Calculator:
    @staticmethod
    def clamp(x, a, b):
        return max(a, min(b, x))
    @staticmethod
    def to_float(x):
        try:
            if x is None or x == "":
                return float("nan")
            return float(x)
        except Exception:
            return float("nan")
    @staticmethod
    def cm_to_m(cm):
        return cm / 100.0
    @staticmethod
    def inches_to_cm(inches):
        return inches * 2.54
    @staticmethod
    def pounds_to_kg(lb):
        return lb * 0.45359237
    @staticmethod
    def feet_inches_to_cm(ft, inch):
        return Calculator.inches_to_cm(ft * 12 + inch)
    @staticmethod
    def kg_to_pounds(kg):
        return kg / 0.45359237
    @staticmethod
    def cm_to_inches(cm):
        return cm / 2.54
    @staticmethod
    def bmi(weight_kg, height_cm):
        h_m = Calculator.cm_to_m(height_cm)
        if h_m <= 0:
            return float("nan")
        return weight_kg / (h_m * h_m)
    @staticmethod
    def bmi_category(bmi):
        if math.isnan(bmi):
            return "Invalid"
        if bmi < 16:
            return "Severe Underweight"
        if bmi < 17:
            return "Moderate Underweight"
        if bmi < 18.5:
            return "Mild Underweight"
        if bmi < 25:
            return "Normal"
        if bmi < 30:
            return "Overweight"
        if bmi < 35:
            return "Obesity I"
        if bmi < 40:
            return "Obesity II"
        return "Obesity III"
    @staticmethod
    def whtr(waist_cm, height_cm):
        if height_cm <= 0:
            return float("nan")
        return waist_cm / height_cm
    @staticmethod
    def whtr_risk(whtr, sex, age):
        if math.isnan(whtr):
            return "Invalid"
        if age < 40:
            if whtr < 0.35:
                return "Underweight"
            if whtr < 0.5:
                return "Healthy"
            if whtr < 0.6:
                return "Overweight"
            return "Obese"
        if age <= 50:
            if whtr < 0.35:
                return "Underweight"
            if whtr < 0.5:
                return "Healthy"
            if whtr < 0.6:
                return "Overweight"
            return "Obese"
        if whtr < 0.35:
            return "Underweight"
        if whtr < 0.5:
            return "Healthy"
        if whtr < 0.6:
            return "Overweight"
        return "Obese"
    @staticmethod
    def body_fat_bmi(bmi, age, sex):
        s = 1 if sex == "Male" else 0
        v = 1.20 * bmi + 0.23 * age - 10.8 * s - 5.4
        return max(0.0, v)
    @staticmethod
    def bmr_mifflin_st_jeor(sex, weight_kg, height_cm, age):
        s = 5 if sex == "Male" else -161
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + s
    @staticmethod
    def bmr_harris_benedict(sex, weight_kg, height_cm, age):
        if sex == "Male":
            return 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age
        return 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age
    @staticmethod
    def tdee(bmr, activity_factor):
        return bmr * activity_factor
    @staticmethod
    def ideal_weight_ranges(height_cm, sex):
        h_in = Calculator.cm_to_inches(height_cm)
        base_in = 60
        over = max(0.0, h_in - base_in)
        if sex == "Male":
            devine = 50 + 2.3 * over
            robinson = 52 + 1.9 * over
            miller = 56.2 + 1.41 * over
            hamwi = 48 + 2.7 * over
        else:
            devine = 45.5 + 2.3 * over
            robinson = 49 + 1.7 * over
            miller = 53.1 + 1.36 * over
            hamwi = 45.5 + 2.2 * over
        return {
            "Devine": devine,
            "Robinson": robinson,
            "Miller": miller,
            "Hamwi": hamwi,
        }
    @staticmethod
    def recomposition_targets(person: Person, bmi_target: float):
        h_m = Calculator.cm_to_m(person.height_cm)
        if h_m <= 0:
            return None
        target_weight = bmi_target * h_m * h_m
        delta = target_weight - person.weight_kg
        pace = 0.5
        weeks = abs(delta) / pace if pace > 0 else float("nan")
        return {
            "target_weight": target_weight,
            "delta": delta,
            "estimated_weeks": weeks,
        }

class Gauge(ttk.Frame):
    def __init__(self, master, width=520, height=60):
        super().__init__(master)
        self.width = width
        self.height = height
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.value = float("nan")
        self.bind("<Configure>", lambda e: self.redraw())
    def set(self, value):
        self.value = value
        self.redraw()
    def redraw(self):
        w = self.winfo_width() or self.width
        h = self.winfo_height() or self.height
        c = self.canvas
        c.delete("all")
        segments = [
            (0, 16, "#7fb3ff"),
            (16, 18.5, "#a0d8ff"),
            (18.5, 25, "#95e1a0"),
            (25, 30, "#ffd480"),
            (30, 35, "#ffab66"),
            (35, 40, "#ff7f7f"),
            (40, 50, "#ff4c4c"),
        ]
        min_b, max_b = 0, 50
        for lo, hi, color in segments:
            x0 = (lo - min_b) / (max_b - min_b) * w
            x1 = (hi - min_b) / (max_b - min_b) * w
            c.create_rectangle(x0, 0, x1, h, fill=color, width=0)
        for v in [16, 18.5, 25, 30, 35, 40]:
            x = (v - min_b) / (max_b - min_b) * w
            c.create_line(x, 0, x, h, fill="#222", width=1)
            c.create_text(x, h - 12, text=str(v), anchor="n", font=("Segoe UI", 8))
        if not math.isnan(self.value):
            x = Calculator.clamp((self.value - min_b) / (max_b - min_b) * w, 0, w)
            c.create_polygon(x, 0, x - 8, -10, x + 8, -10, fill="#121212", outline="#121212")
            c.create_oval(x - 6, h - 18, x + 6, h - 6, fill="#111", outline="#eee", width=2)
            c.create_text(x, 8, text=f"BMI: {self.value:.1f}", font=("Segoe UI Semibold", 10))

class BMICalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("980x700")
        self.minsize(920, 660)
        self.style = ttk.Style()
        self._apply_theme(dark=True)
        self.history = HistoryStore(HISTORY_FILE)
        self.undo_redo = UndoRedo()
        self.unit_var = tk.StringVar(value=UnitSystem.METRIC)
        self.sex_var = tk.StringVar(value="Male")
        self.activity_var = tk.StringVar(value="Sedentary")
        self.age_var = tk.StringVar()
        self.height_cm_var = tk.StringVar()
        self.weight_kg_var = tk.StringVar()
        self.waist_cm_var = tk.StringVar()
        self.ft_var = tk.StringVar()
        self.in_var = tk.StringVar()
        self.lb_var = tk.StringVar()
        self._build_ui()
        self._bind_shortcuts()
    def _apply_theme(self, dark=True):
        base = "clam"
        self.style.theme_use(base)
        bg = "#0f172a" if dark else "#f8fafc"
        fg = "#e2e8f0" if dark else "#0f172a"
        acc = "#38bdf8"
        self.configure(bg=bg)
        for cls in ["TFrame", "TLabel", "TNotebook", "TNotebook.Tab", "TLabelframe", "TLabelframe.Label", "TButton", "TCombobox", "TEntry"]:
            self.style.configure(cls, background=bg, foreground=fg, fieldbackground="#111827", bordercolor="#334155")
        self.style.map("TButton", background=[("active", "#0ea5e9")])
        self.style.configure("Accent.TButton", background=acc, foreground="#00111a")
    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=14)
        self.page_calc = ttk.Frame(self.notebook)
        self.page_history = ttk.Frame(self.notebook)
        self.page_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.page_calc, text="Calculator")
        self.notebook.add(self.page_history, text="History")
        self.notebook.add(self.page_settings, text="Settings")
        self._build_calc_page()
        self._build_history_page()
        self._build_settings_page()
    def _labeled(self, parent, text, widget):
        frm = ttk.Frame(parent)
        ttk.Label(frm, text=text).pack(side="left", padx=(0, 8))
        widget.pack(side="left", fill="x", expand=True)
        return frm
    def _build_calc_page(self):
        top = ttk.Frame(self.page_calc)
        top.pack(fill="x", pady=(12, 8))
        ttk.Label(top, text="Unit System:").pack(side="left")
        ttk.Radiobutton(top, text=UnitSystem.METRIC, value=UnitSystem.METRIC, variable=self.unit_var, command=self._on_unit_change).pack(side="left", padx=8)
        ttk.Radiobutton(top, text=UnitSystem.IMPERIAL, value=UnitSystem.IMPERIAL, variable=self.unit_var, command=self._on_unit_change).pack(side="left", padx=8)
        ttk.Label(top, text="Sex:").pack(side="left", padx=(20, 6))
        ttk.Combobox(top, textvariable=self.sex_var, values=["Male", "Female"], width=10, state="readonly").pack(side="left")
        ttk.Label(top, text="Activity:").pack(side="left", padx=(20, 6))
        ttk.Combobox(top, textvariable=self.activity_var, values=list(ActivityLevel.LEVELS.keys()), width=18, state="readonly").pack(side="left")
        middle = ttk.Frame(self.page_calc)
        middle.pack(fill="x", pady=8)
        left = ttk.Labelframe(middle, text="Inputs")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = ttk.Labelframe(middle, text="Outputs")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        grid = ttk.Frame(left)
        grid.pack(fill="x", padx=12, pady=12)
        ttk.Label(grid, text="Age (years)").grid(row=0, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.age_var).grid(row=0, column=1, sticky="ew")
        ttk.Label(grid, text="Height").grid(row=1, column=0, sticky="w")
        self.ent_height = ttk.Entry(grid, textvariable=self.height_cm_var)
        self.ent_height.grid(row=1, column=1, sticky="ew")
        ttk.Label(grid, text="cm").grid(row=1, column=2, sticky="w")
        ttk.Label(grid, text="Weight").grid(row=2, column=0, sticky="w")
        self.ent_weight = ttk.Entry(grid, textvariable=self.weight_kg_var)
        self.ent_weight.grid(row=2, column=1, sticky="ew")
        ttk.Label(grid, text="kg").grid(row=2, column=2, sticky="w")
        ttk.Label(grid, text="Waist").grid(row=3, column=0, sticky="w")
        self.ent_waist = ttk.Entry(grid, textvariable=self.waist_cm_var)
        self.ent_waist.grid(row=3, column=1, sticky="ew")
        ttk.Label(grid, text="cm").grid(row=3, column=2, sticky="w")
        ttk.Separator(grid, orient="horizontal").grid(row=4, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Label(grid, text="Feet").grid(row=5, column=0, sticky="w")
        self.ent_ft = ttk.Entry(grid, textvariable=self.ft_var)
        self.ent_ft.grid(row=5, column=1, sticky="ew")
        ttk.Label(grid, text="inches").grid(row=5, column=2, sticky="w")
        ttk.Label(grid, text="Inches").grid(row=6, column=0, sticky="w")
        self.ent_in = ttk.Entry(grid, textvariable=self.in_var)
        self.ent_in.grid(row=6, column=1, sticky="ew")
        ttk.Label(grid, text="lbs").grid(row=6, column=2, sticky="w")
        ttk.Label(grid, text="Pounds").grid(row=7, column=0, sticky="w")
        self.ent_lb = ttk.Entry(grid, textvariable=self.lb_var)
        self.ent_lb.grid(row=7, column=1, sticky="ew")
        grid.columnconfigure(1, weight=1)
        btns = ttk.Frame(left)
        btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Calculate", style="Accent.TButton", command=self._calculate).pack(side="left")
        ttk.Button(btns, text="Save to History", command=self._save_history).pack(side="left", padx=8)
        ttk.Button(btns, text="Export CSV", command=self._export_csv).pack(side="left", padx=8)
        ttk.Button(btns, text="Undo", command=self._undo).pack(side="left", padx=8)
        ttk.Button(btns, text="Redo", command=self._redo).pack(side="left", padx=8)
        ttk.Button(btns, text="Reset", command=self._reset).pack(side="right")
        out = ttk.Frame(right)
        out.pack(fill="both", expand=True, padx=12, pady=12)
        self.lbl_bmi = ttk.Label(out, text="BMI: -", font=("Segoe UI", 14, "bold"))
        self.lbl_bmi.pack(anchor="w")
        self.lbl_cat = ttk.Label(out, text="Category: -")
        self.lbl_cat.pack(anchor="w", pady=(4, 0))
        self.lbl_whtr = ttk.Label(out, text="Waist/Height: -")
        self.lbl_whtr.pack(anchor="w")
        self.lbl_risk = ttk.Label(out, text="Central Adiposity Risk: -")
        self.lbl_risk.pack(anchor="w")
        self.lbl_bodyfat = ttk.Label(out, text="Body Fat %: -")
        self.lbl_bodyfat.pack(anchor="w")
        self.lbl_bmr1 = ttk.Label(out, text="BMR (Mifflin-St Jeor): -")
        self.lbl_bmr1.pack(anchor="w")
        self.lbl_bmr2 = ttk.Label(out, text="BMR (Harris-Benedict): -")
        self.lbl_bmr2.pack(anchor="w")
        self.lbl_tdee = ttk.Label(out, text="TDEE: -")
        self.lbl_tdee.pack(anchor="w")
        self.lbl_ideal = ttk.Label(out, text="Ideal Weights: -")
        self.lbl_ideal.pack(anchor="w", pady=(4, 0))
        self.lbl_target = ttk.Label(out, text="Target @ BMI 22.5: -")
        self.lbl_target.pack(anchor="w")
        self.gauge = Gauge(self.page_calc)
        self.gauge.pack(fill="x", padx=12, pady=10)
        self._on_unit_change()
    def _build_history_page(self):
        top = ttk.Frame(self.page_history)
        top.pack(fill="x", padx=12, pady=12)
        ttk.Button(top, text="Refresh", command=self._refresh_history).pack(side="left")
        ttk.Button(top, text="Clear All", command=self._clear_history).pack(side="left", padx=8)
        ttk.Button(top, text="Export CSV", command=self._export_history_csv).pack(side="left", padx=8)
        self.tree = ttk.Treeview(self.page_history, columns=("time","sex","age","height","weight","waist","bmi","cat","bf","tdee"), show="headings")
        for k, w in zip(["time","sex","age","height","weight","waist","bmi","cat","bf","tdee"],[160,60,60,80,80,80,80,120,80,100]):
            self.tree.heading(k, text=k.upper())
            self.tree.column(k, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self._refresh_history()
    def _build_settings_page(self):
        frm = ttk.Labelframe(self.page_settings, text="Appearance")
        frm.pack(fill="x", padx=12, pady=12)
        ttk.Button(frm, text="Dark", command=lambda: self._apply_theme(True)).pack(side="left")
        ttk.Button(frm, text="Light", command=lambda: self._apply_theme(False)).pack(side="left", padx=8)
        frm2 = ttk.Labelframe(self.page_settings, text="Data")
        frm2.pack(fill="x", padx=12, pady=12)
        ttk.Label(frm2, text=f"Data Directory: {DATA_DIR}").pack(anchor="w")
        ttk.Button(frm2, text="Open Folder", command=self._open_data_dir).pack(anchor="w", pady=6)
    def _open_data_dir(self):
        path = DATA_DIR
        path.mkdir(exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(path))
            elif os.name == "posix":
                os.system(f"xdg-open '{path}' >/dev/null 2>&1 &")
        except Exception:
            pass
    def _bind_shortcuts(self):
        self.bind("<Control-Return>", lambda e: self._calculate())
        self.bind("<Control-s>", lambda e: self._save_history())
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        self.bind("<Escape>", lambda e: self._reset())
    def _snapshot(self):
        return {
            "unit": self.unit_var.get(),
            "sex": self.sex_var.get(),
            "activity": self.activity_var.get(),
            "age": self.age_var.get(),
            "height_cm": self.height_cm_var.get(),
            "weight_kg": self.weight_kg_var.get(),
            "waist_cm": self.waist_cm_var.get(),
            "ft": self.ft_var.get(),
            "inch": self.in_var.get(),
            "lb": self.lb_var.get(),
        }
    def _restore(self, s):
        self.unit_var.set(s.get("unit","Metric"))
        self.sex_var.set(s.get("sex","Male"))
        self.activity_var.set(s.get("activity","Sedentary"))
        self.age_var.set(s.get("age",""))
        self.height_cm_var.set(s.get("height_cm",""))
        self.weight_kg_var.set(s.get("weight_kg",""))
        self.waist_cm_var.set(s.get("waist_cm",""))
        self.ft_var.set(s.get("ft",""))
        self.in_var.set(s.get("inch",""))
        self.lb_var.set(s.get("lb",""))
        self._on_unit_change()
    def _on_unit_change(self):
        metric = self.unit_var.get() == UnitSystem.METRIC
        for w in [self.ent_height, self.ent_weight, self.ent_waist]:
            w.configure(state="normal" if metric else "disabled")
        for w in [self.ent_ft, self.ent_in, self.ent_lb]:
            w.configure(state="disabled" if metric else "normal")
    def _get_person(self):
        age = Calculator.to_float(self.age_var.get())
        if self.unit_var.get() == UnitSystem.METRIC:
            height_cm = Calculator.to_float(self.height_cm_var.get())
            weight_kg = Calculator.to_float(self.weight_kg_var.get())
            waist_cm = Calculator.to_float(self.waist_cm_var.get())
        else:
            ft = Calculator.to_float(self.ft_var.get())
            inch = Calculator.to_float(self.in_var.get())
            lb = Calculator.to_float(self.lb_var.get())
            height_cm = Calculator.feet_inches_to_cm(ft, inch)
            weight_kg = Calculator.pounds_to_kg(lb)
            waist_cm = Calculator.inches_to_cm(Calculator.to_float(self.waist_cm_var.get())) if self.waist_cm_var.get() else float("nan")
        return Person(self.sex_var.get(), age, height_cm, weight_kg, waist_cm)
    def _validate_person(self, p: Person):
        errs = []
        if math.isnan(p.age) or p.age <= 0 or p.age > 120:
            errs.append("Age must be 1-120")
        if math.isnan(p.height_cm) or p.height_cm <= 0 or p.height_cm > 300:
            errs.append("Height must be valid")
        if math.isnan(p.weight_kg) or p.weight_kg <= 0 or p.weight_kg > 500:
            errs.append("Weight must be valid")
        if math.isnan(p.waist_cm) or p.waist_cm <= 0 or p.waist_cm > 300:
            errs.append("Waist must be valid")
        return errs
    def _compute(self, p: Person):
        bmi = Calculator.bmi(p.weight_kg, p.height_cm)
        cat = Calculator.bmi_category(bmi)
        whtr = Calculator.whtr(p.waist_cm, p.height_cm)
        risk = Calculator.whtr_risk(whtr, p.sex, p.age)
        bf = Calculator.body_fat_bmi(bmi, p.age, p.sex)
        bmr1 = Calculator.bmr_mifflin_st_jeor(p.sex, p.weight_kg, p.height_cm, p.age)
        bmr2 = Calculator.bmr_harris_benedict(p.sex, p.weight_kg, p.height_cm, p.age)
        factor = ActivityLevel.LEVELS.get(self.activity_var.get(), 1.2)
        tdee = Calculator.tdee(bmr1, factor)
        ideals = Calculator.ideal_weight_ranges(p.height_cm, p.sex)
        target = Calculator.recomposition_targets(p, 22.5)
        return Result(bmi, cat, risk, whtr, bf, bmr1, bmr2, tdee, ideals), target
    def _calculate(self):
        s = self._snapshot()
        self.undo_redo.push(s)
        p = self._get_person()
        errs = self._validate_person(p)
        if errs:
            messagebox.showerror(APP_NAME, "\n".join(errs))
            return
        res, tgt = self._compute(p)
        self._render_results(res, tgt)
        self.gauge.set(res.bmi)
    def _render_results(self, r: Result, tgt):
        self.lbl_bmi.configure(text=f"BMI: {r.bmi:.2f}")
        self.lbl_cat.configure(text=f"Category: {r.category}")
        self.lbl_whtr.configure(text=f"Waist/Height: {r.whtr:.3f}")
        self.lbl_risk.configure(text=f"Central Adiposity Risk: {r.risk}")
        self.lbl_bodyfat.configure(text=f"Body Fat %: {r.body_fat:.1f}")
        self.lbl_bmr1.configure(text=f"BMR (Mifflin-St Jeor): {r.bmr_msj:.0f} kcal")
        self.lbl_bmr2.configure(text=f"BMR (Harris-Benedict): {r.bmr_hb:.0f} kcal")
        self.lbl_tdee.configure(text=f"TDEE ({self.activity_var.get()}): {r.tdee:.0f} kcal")
        ideals = ", ".join([f"{k}: {v:.1f} kg" for k, v in r.ideal_weights.items()])
        self.lbl_ideal.configure(text=f"Ideal Weights: {ideals}")
        if tgt:
            sign = "+" if tgt["delta"]>0 else ""
            self.lbl_target.configure(text=f"Target @ BMI 22.5: {tgt['target_weight']:.1f} kg ({sign}{tgt['delta']:.1f} kg) ~ {tgt['estimated_weeks']:.0f} weeks @0.5kg/wk")
    def _save_history(self):
        p = self._get_person()
        errs = self._validate_person(p)
        if errs:
            messagebox.showerror(APP_NAME, "\n".join(errs))
            return
        res, tgt = self._compute(p)
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "person": asdict(p),
            "result": asdict(res),
            "activity": self.activity_var.get(),
            "target": tgt,
        }
        self.history.add_entry(payload)
        self._refresh_history()
        messagebox.showinfo(APP_NAME, "Saved.")
    def _refresh_history(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.history.all():
            t = row.get("timestamp","-")
            sex = row.get("person",{}).get("sex","-")
            age = row.get("person",{}).get("age","-")
            h = row.get("person",{}).get("height_cm","-")
            w = row.get("person",{}).get("weight_kg","-")
            waist = row.get("person",{}).get("waist_cm","-")
            bmi = row.get("result",{}).get("bmi","-")
            cat = row.get("result",{}).get("category","-")
            bf = row.get("result",{}).get("body_fat","-")
            tdee = row.get("result",{}).get("tdee","-")
            self.tree.insert("", "end", values=(t,sex,f"{age}",f"{h:.1f}",f"{w:.1f}",f"{waist:.1f}",f"{bmi:.1f}",cat,f"{bf:.1f}",f"{tdee:.0f}"))
    def _clear_history(self):
        if messagebox.askyesno(APP_NAME, "Clear all history?"):
            self.history.clear()
            self._refresh_history()
    def _export_csv(self):
        p = self._get_person()
        errs = self._validate_person(p)
        if errs:
            messagebox.showerror(APP_NAME, "\n".join(errs))
            return
        res, tgt = self._compute(p)
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], initialfile="bmi_result.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Field","Value"])
            w.writerow(["Sex", p.sex])
            w.writerow(["Age", p.age])
            w.writerow(["Height_cm", p.height_cm])
            w.writerow(["Weight_kg", p.weight_kg])
            w.writerow(["Waist_cm", p.waist_cm])
            w.writerow(["BMI", res.bmi])
            w.writerow(["Category", res.category])
            w.writerow(["WHtR", res.whtr])
            w.writerow(["Risk", res.risk])
            w.writerow(["BodyFat%", res.body_fat])
            w.writerow(["BMR_MSJ", res.bmr_msj])
            w.writerow(["BMR_HB", res.bmr_hb])
            w.writerow(["TDEE", res.tdee])
            for k,v in res.ideal_weights.items():
                w.writerow([f"Ideal_{k}", v])
            if tgt:
                w.writerow(["TargetWeight", tgt["target_weight"]])
                w.writerow(["Delta", tgt["delta"]])
                w.writerow(["Weeks@0.5kg/wk", tgt["estimated_weeks"]])
        messagebox.showinfo(APP_NAME, "Exported CSV.")
    def _export_history_csv(self):
        data = self.history.all()
        if not data:
            messagebox.showinfo(APP_NAME, "No history to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], initialfile="bmi_history.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            head = ["timestamp","sex","age","height_cm","weight_kg","waist_cm","bmi","category","whtr","risk","body_fat","bmr_msj","bmr_hb","tdee","ideal_devine","ideal_robinson","ideal_miller","ideal_hamwi","activity","target_weight","delta","weeks"]
            w.writerow(head)
            for row in data:
                p = row.get("person",{})
                r = row.get("result",{})
                ideals = r.get("ideal_weights",{})
                tgt = row.get("target",{}) or {}
                w.writerow([
                    row.get("timestamp",""),
                    p.get("sex",""),
                    p.get("age",""),
                    p.get("height_cm",""),
                    p.get("weight_kg",""),
                    p.get("waist_cm",""),
                    r.get("bmi",""),
                    r.get("category",""),
                    r.get("whtr",""),
                    r.get("risk",""),
                    r.get("body_fat",""),
                    r.get("bmr_msj",""),
                    r.get("bmr_hb",""),
                    r.get("tdee",""),
                    ideals.get("Devine",""),
                    ideals.get("Robinson",""),
                    ideals.get("Miller",""),
                    ideals.get("Hamwi",""),
                    row.get("activity",""),
                    tgt.get("target_weight",""),
                    tgt.get("delta",""),
                    tgt.get("estimated_weeks",""),
                ])
        messagebox.showinfo(APP_NAME, "History exported.")
    def _undo(self):
        s = self._snapshot()
        prev = self.undo_redo.undo(s)
        self._restore(prev)
    def _redo(self):
        s = self._snapshot()
        nxt = self.undo_redo.redo(s)
        self._restore(nxt)
    def _reset(self):
        self.age_var.set("")
        self.height_cm_var.set("")
        self.weight_kg_var.set("")
        self.waist_cm_var.set("")
        self.ft_var.set("")
        self.in_var.set("")
        self.lb_var.set("")
        self.gauge.set(float("nan"))
        for lbl in [self.lbl_bmi,self.lbl_cat,self.lbl_whtr,self.lbl_risk,self.lbl_bodyfat,self.lbl_bmr1,self.lbl_bmr2,self.lbl_tdee,self.lbl_ideal,self.lbl_target]:
            lbl.configure(text=lbl.cget("text").split(":")[0] + ": -")

if __name__ == "__main__":
    app = BMICalculatorApp()
    app.mainloop()
