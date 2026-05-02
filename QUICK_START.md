# 🕸️ Spider-Arm v2.5 — Quick Start Guide

> **Your daily cheatsheet.** Everything you need to run, train, and maintain Spider-Arm after the one-time setup is done.

---

## 🗺️ File Map (What Does What)

| File | Role |
|---|---|
| `setup_wizard.py` | **One-time setup** — builds Firebase cloud & trains the AI brain |
| `inference.py` | **Local mode** — run the assistant directly in your terminal |
| `backend/firebase_bridge.py` | **Remote mode** — connects your PC to the mobile dashboard |
| `controller/tools.py` | The "hands" — all 11 tools the agent can execute |
| `train.py` | Re-trains the AI brain after adding new examples |
| `data/pc_control_dataset.jsonl` | Training data — add new examples here |

---

## ✅ Step 1 — Activate Your Environment

> Run this **every time** you open a new terminal before starting Spider-Arm.

```powershell
# Navigate to the project folder first
cd "d:\Projects\LLM\Qwen 3.5 0.8B"

# Activate the virtual environment
.\venv_312\Scripts\activate

# Your prompt should now show (venv_312) on the left
```

**First time only** — install dependencies after cloning:
```powershell
pip install -r requirements.txt
```

---

## 🚀 Step 2 — Choose Your Mode

### Mode A · Local Terminal (No Internet Required)
Talks to the model directly in your terminal. Great for testing.
```powershell
python inference.py
```
Type a command and press Enter. Type `exit` to quit.

---

### Mode B · Remote Mobile Dashboard (Full Experience)
Connects your PC to Firebase so your phone can send commands.
```powershell
python -m backend.firebase_bridge
```
Keep this running in the background while using the mobile dashboard.

> 📱 **Mobile Dashboard URL**: `https://<your-project-id>.web.app`
> *(The wizard printed this URL when you first ran it.)*

---

## 🧠 Step 3 — Updating the AI Brain (Optional)

Only needed if you want to teach the model new commands.

**1. Add your new examples** to `data/pc_control_dataset.jsonl` — follow the existing format:
```json
{"instruction": "Open Notepad", "thought": "Launch the text editor.", "action": "{\"tool\": \"launch_app\", \"parameters\": {\"name\": \"notepad\"}}"}
```

**2. Re-run training:**
```powershell
python train.py
```
> ⏱️ Takes ~3–5 minutes on an RTX 3050. The updated model saves to `qwen_assistant_lora/`.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `(venv_312)` not showing in prompt | Run `.\venv_312\Scripts\activate` first |
| `ModuleNotFoundError` on startup | Run `pip install -r requirements.txt` inside the venv |
| Temperature stats missing (`---`) | Reopen terminal as **Run as Administrator** |
| `CUDA out of memory` on bridge start | Close games/heavy GPU apps before launching |
| Mobile dashboard not responding | Make sure `firebase_bridge.py` is running on your PC |
| `credentials.json not found` error | Re-run `python setup_wizard.py` and complete the service account step |
| Bridge connects but commands fail | Check that `qwen_assistant_lora/` folder exists (re-run `python train.py` if missing) |

---

## 🧹 Maintenance Commands

```powershell
# Check what's installed in your venv
pip list

# Re-install everything from scratch (if packages break)
pip install -r requirements.txt --force-reinstall

# Manually install hardware monitoring libs (if temperatures show as ---)
pip install GPUtil wmi
```

---

Happy Automating! 🕸️🤖
