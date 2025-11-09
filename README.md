🧮 Advanced Tkinter BMI Calculator

A professional-grade, visually advanced BMI Calculator GUI application built using Python (Tkinter).
This project goes beyond basic BMI and includes body fat, BMR, TDEE, ideal weight formulas, history tracking, export options, and a gauge-style BMI meter.

🚀 Features

✅ Modern Tkinter UI (Dark/Light themes)
✅ BMI calculation with WHO category bands
✅ Waist-to-Height Ratio (WHtR) & Risk assessment
✅ Body Fat % estimation (Deurenberg formula)
✅ BMR formulas (Mifflin–St Jeor & Harris-Benedict)
✅ TDEE based on activity level
✅ Ideal weight by Devine, Robinson, Miller & Hamwi formulas
✅ Recomposition goal suggestion (target BMI = 22.5)
✅ Undo / Redo input states
✅ Save history to local JSON
✅ Export results & history to CSV
✅ Keyboard shortcuts
✅ Beautiful BMI gauge indicator
✅ Dual Unit Support (Metric & Imperial)

🖥️ GUI Preview

💡 Include screenshots or GIFs here later like:

/screenshots/home.png  
/screenshots/history.png

🛠️ Tech Stack
Component	Tech
Language	Python 3.x
GUI Framework	Tkinter (no external libs)
Data Storage	JSON
Charts / Visuals	Custom Tk Canvas
Export	CSV writer

📦 Installation

Clone Repo
git clone https://github.com/ADARSHAG707/Advanced-Tkinter-Bmi-Calculator.git
cd Advanced-Tkinter-Bmi-Calculator

Run the App
python bmi_tk_app.py


If using Linux/Mac:

python3 bmi_tk_app.py

🎮 Keyboard Shortcuts
Action	Shortcut
Calculate	Ctrl + Enter
Save to History	Ctrl + S
Undo	Ctrl + Z
Redo	Ctrl + Y
Reset Inputs	Esc
📁 Data Storage
Type	Location
History	~/.bmi_tool/history.json
Output CSV	User-selected folder
🧠 Calculations Included

BMI = kg/m²

WHtR = waist / height

Deurenberg Body Fat %

BMR (MSJ & Harris-Benedict)

TDEE based on activity multiplier

Ideal weights (4 formulas)

Fat-loss timeline projection

🧑‍💻 Developer Notes

No third-party libraries — uses pure Tkinter

Code structured with classes & dataclasses

Undo/Redo stack implemented manually

Persistent history + export tools

📜 License

MIT License – free to use, modify, and distribute.

👨‍💻 Author

Adarsh AG
Cybersecurity & Python Enthusiast
