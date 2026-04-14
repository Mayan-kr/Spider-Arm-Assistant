# 🕸️ Spider-Arm v2.0 Quick Start Guide

Welcome to **Spider-Arm v2.0**. This guide will help you manage your local agent and remote dashboard.

## 🧭 Navigation
- **`inference.py`**: Local terminal control.
- **`backend/firebase_bridge.py`**: Remote web control (Android).
- **`controller/tools.py`**: The "hands" of the assistant.
- **`train.py`**: Fine-tuning your assistant.

```powershell
.\venv_312\Scripts\activate
```

---

## 2. Training & Brain Updates
Run these commands if you add new training examples to `data/pc_control_dataset.jsonl`.

### Fine-Tuning (3-5 minutes)
This teaches the model your specific PC control patterns.
```powershell
python train.py
```

---

## 3. Running the Assistant
Use this to connect your PC to the Firebase cloud and start listening for mobile commands.

### Start the Firebase Bridge
```powershell
python -m backend.firebase_bridge
```

---

## 4. Maintenance Commands
Useful for troubleshooting and installing new features.

### Install Hardware Libraries (Temperatures)
```powershell
pip install GPUtil wmi
```

### Check Installed Packages
```powershell
pip list
```

---

## 5. UI Dashboard
- To open the mobile controller on your phone (or PC browser), simply open the local file:
  `d:\Projects\LLM\Qwen 3.5 0.8B\mobile\index.html`

---

## 🔧 Troubleshooting
- **Permission Errors**: If the PC temperature doesn't show up, try closing the terminal and opening it as **Run as Administrator**.
- **Venv Issues**: If `pip` gives a "Fatal error," ensure your project folder name is exactly **`Qwen 3.5 0.8B`**.
- **Model Loading**: Ensure your RTX 3050 is not being heavily used by other games/apps while starting the bridge to avoid Out-Of-Memory (OOM) errors.

Happy Automating! 🕸️🤖
