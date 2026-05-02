# 🕷️ Spider-Arm Assistant v2.5

> **Control your Windows PC from your phone using voice-friendly natural language — powered by a local AI model, no cloud inference fees.**

Spider-Arm is a personal AI assistant that runs a fine-tuned **Qwen2.5-1.5B** model locally on your GPU. You send it a plain-English command (e.g. *"take a screenshot"*, *"play the next song"*, *"check my CPU temp"*) from a mobile web dashboard, and it figures out which tool to execute on your PC.

---

## ✨ What It Can Do

| Category | Capabilities |
|---|---|
| 🖥️ App Control | Launch any app, close processes by name |
| 📸 Screen | Take and save screenshots |
| 🎵 Media | Play/Pause, Next/Prev track, Volume up/down — works with Spotify, YouTube, etc. |
| 📊 System Stats | CPU, RAM, Disk usage + GPU & CPU temperatures (NVIDIA) |
| ⌨️ Input | Type text into any window, press individual keys |
| 📁 File System | Create files/folders on Desktop, delete files *(requires your approval)* |
| 🔒 Safety | Sensitive actions (delete, create) require a one-tap approval on your phone |

---

## 🏗️ How It Works

```
Your Phone (Dashboard)
        │
        │  writes command to cloud
        ▼
  Firebase Firestore  ◄──────────────────────────────┐
        │                                             │
        │  triggers snapshot listener                 │  updates result
        ▼                                             │
  Local Python Bridge (firebase_bridge.py)            │
        │                                             │
        │  runs local inference                       │
        ▼                                             │
  Qwen 1.5B LoRA Model  ──► controller/tools.py ──► Windows PC
```

1. You type a command on your phone.
2. It's written to Firebase Firestore (cloud database).
3. The bridge script running on your PC picks it up instantly.
4. The local AI model decides which tool to run.
5. The tool executes on your PC and the result is sent back to your phone.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI Model | Qwen2.5-1.5B-Instruct (4-bit LoRA via Unsloth) |
| Fine-Tuning | TRL + HuggingFace Transformers |
| Backend | Python 3.12 |
| Cloud Sync | Google Firebase Firestore |
| Mobile UI | Vanilla HTML/JS (Glassmorphism theme) |
| Hosting | Firebase Hosting |

---

## ⚙️ Prerequisites

Before cloning, install these on your PC:

| Tool | Why You Need It | Install Command |
|---|---|---|
| **Python 3.12** | Runs all scripts | `winget install -e --id Python.Python.3.12 --version 3.12.10` |
| **Node.js + npm** | Required by Firebase CLI | [nodejs.org/en/download](https://nodejs.org/en/download) |
| **Firebase CLI** | Manages cloud setup | `npm install -g firebase-tools` |
| **NVIDIA GPU** | Runs the AI model locally (4GB+ VRAM) | — |

> ⚠️ During Python install: check **"Add Python to PATH"** or commands won't work.

---

## 🚀 Installation (One-Time Setup)

### Step 1 — Clone the repo

```powershell
git clone https://github.com/Mayan-kr/Spider-Arm-Assistant.git
cd Spider-Arm-Assistant
```

### Step 2 — Create a virtual environment & install packages

```powershell
python -m venv venv_312
.\venv_312\Scripts\activate
pip install -r requirements.txt
```

> 📦 This installs PyTorch, Unsloth, Firebase Admin, and all other dependencies.

### Step 3 — Run the Setup Wizard

```powershell
python setup_wizard.py
```

The wizard will automatically:
- ✅ Check that Firebase CLI is installed
- ✅ Log you in to Firebase
- ✅ Create a Firebase project in the cloud
- ✅ Register the mobile dashboard web app
- ✅ Walk you through enabling Google Sign-In (3 browser clicks)
- ✅ Save your credentials to `credentials.json`
- ✅ Deploy the mobile dashboard
- ✅ Fine-tune the AI model on your GPU

**During the wizard, your browser will open 3 times:**

| When | What to do |
|---|---|
| **Firebase Login** | Sign in with your Google account |
| **Auth Providers page** | Click **"Get Started"** → **"Google"** → Enable → **Save** |
| **Service Accounts page** | Click **"Generate New Private Key"** → open the downloaded `.json` → paste its full contents into the terminal |

### Step 4 — Start the Bridge

```powershell
python -m backend.firebase_bridge
```

Keep this running. It listens for commands from your phone in real time.

### Step 5 — Open the Dashboard on Your Phone

The wizard printed a URL at the end that looks like:
```
https://spider-arm-XXXX.web.app
```
Open that on your phone, sign in with the same Google account, and start giving commands.

---

## 🎮 Daily Usage

### Local Mode (terminal only, no phone needed)
```powershell
.\venv_312\Scripts\activate
python inference.py
```

### Remote Mode (phone → PC)
```powershell
.\venv_312\Scripts\activate
python -m backend.firebase_bridge
```

---

## 🔒 Security & Privacy

- **Local AI** — your model runs 100% on your own GPU. No text or screenshots are sent to any external AI API.
- **Google Auth** — the mobile dashboard requires sign-in. Only your Google account can send commands.
- **Firestore Rules** — the database is locked to your verified email. No one else can write to it.
- **Approval Flow** — destructive actions (file delete, file create) show an approval card on your phone before executing.

---

## 🔧 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `firebase: command not found` | Firebase CLI not installed | `npm install -g firebase-tools` |
| `ModuleNotFoundError` | Packages not installed in venv | Activate venv, then `pip install -r requirements.txt` |
| `credentials.json not found` | Setup wizard not completed | Re-run `python setup_wizard.py` |
| `CUDA out of memory` | GPU is busy | Close games or other GPU-heavy apps, then restart |
| Temperature shows `---` | Missing WMI/GPUtil permissions | Relaunch terminal as **Administrator** |
| Commands not received on PC | Bridge not running | Make sure `firebase_bridge.py` is running |
| Model generates wrong tool | Training data issue | Add better examples to `data/pc_control_dataset.jsonl` and re-run `python train.py` |

---

## 📜 License

MIT — free to use, modify, and share.
